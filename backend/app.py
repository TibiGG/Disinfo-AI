import re
from typing import List, Dict, Optional

from chainlit import send_message, on_message, send_action, action
from dotenv import load_dotenv
from langchain import OpenAI, PromptTemplate, LLMChain
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

NUM_LINKS = 3

sites = [
    {
        "link": "https://fullfact.org/search",
        "id": "gsc-i-id1",
        "url_wrapper_class": "gsc-expansionArea",
        "toggle_class": None
    },
    {
        "link": "https://oversight.house.gov/?s=yo+mama",
        "id": "mobile-menu-search-input",
        "url_wrapper_class": "post",
        "toggle_class": "navbar-toggle"
    }
    #   {
    #       "link": "https://www.legislation.gov.uk",
    #       "id": "title",
    #       "url_wrapper_class": "results",
    #   },
    #   {
    #       "link": "https://www.ons.gov.uk/search",
    #       "id": "search-in-page",
    #       "url_wrapper_class": "flush--padding",
    #       "filter_id": "group-0"
    #   }
]

visited_references = set()


def filter_out_nones(l: list):
    return [x for x in l if x is not None]


def scrape_article_only(link: str) -> str:
    global driver

    # Load page
    driver.get(link)
    # Find <article> element
    article_elem = driver.find_element(By.CSS_SELECTOR, "article")
    # Extract text from <article> element
    article_text = article_elem.text
    return article_text


def initialise_webdriver():
    global driver
    options = Options()
    # options.add_argument('--headless')
    driver = webdriver.Firefox(options=options)
    driver.set_window_size(375, 667)  # Example dimensions for iPhone 6/7/8


def scrape_link(link: str, id: str, url_wrapper_class: str, toggle_class: Optional[str] = None,
                query: str = "immigration healthcare") -> List[Dict[str, str]]:

    # navigate to your website
    driver.get(link)

    # if there's a toggleable element for navigation, toggle it now
    if toggle_class:
        navbar_toggle = driver.find_element(By.CLASS_NAME, toggle_class)
        navbar_toggle.click()

    # wait for the search results to appear
    wait = WebDriverWait(driver, 1)

    # locate the search input field and enter your search query
    search_input = driver.find_element(by="id", value=id)
    search_input.send_keys(query)
    search_input.send_keys(Keys.RETURN)

    try:
        search_results: list = wait.until(EC.presence_of_all_elements_located((By.XPATH,
                                                                               f"//div[contains(concat(' ', normalize-space(@class), ' '), ' {url_wrapper_class} ')]//a[not(@target='_blank')]"
                                                                               f" | //ul[contains(concat(' ', normalize-space(@class), ' '), ' {url_wrapper_class} ')]//a[not(@target='_blank')]")))
    except TimeoutException:
        print("Timed out: nothing found!")
        return []

    print(search_results)
    urls = list(dict.fromkeys(filter_out_nones([result.get_attribute("href") for result in search_results])))
    print(urls)
    articles_scraped = 0
    articles = []
    for url in urls:
        if url in visited_references:
            continue
        driver.get(url)
        try:
            main_div = wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
            text = main_div.text
            articles.append({"src": url, "text": text})
            articles_scraped += 1
        # print(text)
        except TimeoutException:
            # print("NO ARTICLE IN THIS LINK")
            pass
        if articles_scraped >= NUM_LINKS:
            break

    # time.sleep(1000)
    return articles


# Press the green button in the gutter to run the script.
def summarise(text: str) -> str:
    llm = OpenAI(model_name="text-davinci-003", temperature=0.9)
    prompt = PromptTemplate(
        input_variables=["text"],
        template="Summarise this in 2 short sentences:\n{text}"
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    chain_output = chain.run(text)
    return chain_output


def main_scrape(query: str = "immigration healthcare"):
    # Load environment variables (the OpenAI env var in particular)
    articles = []
    for site in sites:
        articles.extend(scrape_link(link=site["link"], id=site["id"], url_wrapper_class=site["url_wrapper_class"],
                                    toggle_class=site["toggle_class"], query=query))
    summaries = []
    for article in articles:
        summaries.append({"src": article["src"], "text": summarise(article["text"])})

    return summaries


# See PyCharm help at https://www.jetbrains.com/help/pycharm/


def main_claims(text: str) -> str:
    llm = OpenAI(model_name="text-davinci-003", temperature=0.9)
    prompt = PromptTemplate(
        input_variables=["text"],
        template="You are factGPT. Read the following article/text and assess the claims it makes which are most likely"
                 " to be false. Provide these claims as a list in plain english, separated by new lines. You should"
                 " not exceed more than the"
                 " three most controversial claims which you have found. You should provide any context given in the"
                 " text that is necessary for evaluating the claim. Provide each claim as a short sentence"
                 " that does not exceed 15 words.\nArticle:\n{text}"
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    chain_output = chain.run(text)
    return chain_output


def remove_punctuation(text):
    # Define the pattern to match non-alphanumeric characters or spaces
    pattern = r"[^a-zA-Z0-9\s]"

    # Remove punctuation using regex
    cleaned_text = re.sub(pattern, "", text)

    return cleaned_text


def main_keyword(text: str) -> str:
    llm = OpenAI(model_name="text-davinci-003", temperature=0.9)
    prompt = PromptTemplate(
        input_variables=["text"],
        template="Turn this sentence into a short search query for related articles: '{text}'. Return the query only."
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    chain_output = chain.run(text)
    return remove_punctuation(chain_output)


@on_message  # this function will be called every time a user inputs a message in the UI
def main(message: str):
    load_dotenv()
    # Initialise query
    visited_references.clear()
    print("\n\n\n#############################\n\n\n")
    send_message(
        content=f"Your article makes these claims:",
    )
    claims = main_claims(message)
    # TODO: regex out only ordered claims (with 1.)
    send_message(
        content=f"{claims}",
    )
    send_message(
        content=f"Analysing Claims...",
    )
    # Extract skills as a list
    claims = re.findall(r'\d+\.\s+(.+)', claims)
    keywords = []
    for claim in claims:
        # HACK: removing 'umu' from claim
        keywords.append(main_keyword(claim.replace("UMU", "")))

    keywords = [keyword.strip() for keyword in keywords]
    print(keywords)

    initialise_webdriver()
    for keyword in keywords:
        summarised_articles = main_scrape(keyword)
        articles_print = "\n\n".join([article["text"] for article in summarised_articles])
        reference_list = [article["src"] for article in summarised_articles]
        n_references = len(reference_list)
        visited_references.update(reference_list)
        references = "\n".join([f"{i}. {reference} Dig_Deeper {i}" for i, reference in enumerate(reference_list)])
        if articles_print and references:
            send_message(
                content=f"**{articles_print.strip()}**\n\nReferences:\n\n{references}",
            )
            for i_ref, ref in enumerate(reference_list):
                send_action(name="action0", trigger=f"Dig_Deeper {i_ref}",
                            description=ref)
    driver.quit()


@action("action0")
def on_action(action):
    url = action['description']
    next_article: str = scrape_article_only(url)
    send_message(content=f"### Fact checking new article at {url}...")
    main(next_article)
