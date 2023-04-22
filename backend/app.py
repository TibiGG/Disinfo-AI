from chainlit import send_message, on_message
from dotenv import load_dotenv
from langchain import OpenAI, PromptTemplate, LLMChain

from typing import List, Dict

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

NUM_LINKS = 3

sites = [
    {
        "link": "https://fullfact.org/search",
        "id": "gsc-i-id1",
        "urls_class": "gs-title",
    }
]


visited_references = set()


def filter_out_nones(l: list):
    return [x for x in l if x is not None]


def scrape_link(link: str, id: str, urls_class: str, query: str = "immigration healthcare") -> List[Dict[str, str]]:
    # create a new instance of the Firefox driver
    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    # navigate to your website
    driver.get(link)

    # locate the search input field and enter your search query
    search_input = driver.find_element(by="id", value=id)
    search_input.send_keys(query)
    search_input.send_keys(Keys.RETURN)

    # wait for the search results to appear
    wait = WebDriverWait(driver, 2)
    try:
        search_results: list = wait.until(EC.presence_of_all_elements_located((By.XPATH,
                                                                           f"//a[contains(@class, '{urls_class}')]")))
    except TimeoutException:
        print("Timed out: nothing found!")
        driver.quit()
        return []

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

    # close the browser
    driver.quit()
    # time.sleep(1000)
    return articles


# Press the green button in the gutter to run the script.
def summarise(text: str) -> str:
    llm = OpenAI(temperature=0.9)
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
        articles.extend(scrape_link(link=site["link"], id=site["id"], urls_class=site["urls_class"], query=query))
    # print(articles)
    summaries = []
    for article in articles:
        summaries.append({"src": article["src"], "text": summarise(article["text"])})
    return summaries


# See PyCharm help at https://www.jetbrains.com/help/pycharm/


def main_claims(text: str) -> str:
    llm = OpenAI(temperature=0.9)
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


def main_keyword(text: str) -> str:
    llm = OpenAI(temperature=0.9)
    prompt = PromptTemplate(
        input_variables=["text"],
        template="Turn this sentence into a short search query for related articles: '{text}'. Return the unquoted query only."
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    chain_output = chain.run(text)
    return chain_output


@on_message  # this function will be called every time a user inputs a message in the UI
def main(message: str):
    load_dotenv()
    send_message(
        content=f"Your article makes these claims:",
    )
    claims = main_claims(message)
    send_message(
        content=f"{claims}",
    )
    send_message(
        content=f"Analysing Claims...",
    )
    claims = [claim for claim in claims.split('\n') if claim != '']
    keywords = []
    for claim in claims:
        keywords.append(main_keyword(claim))

    keywords = [keyword.replace("\n", "") for keyword in keywords]
    print(keywords)

    for keyword in keywords:
        summarised_articles = main_scrape(keyword)
        articles_print = "\n\n".join([article["text"] for article in summarised_articles])
        reference_list = [article["src"] for article in summarised_articles]
        visited_references.update(reference_list)
        references = "\n".join(reference_list)
        if articles_print and references:
            send_message(
                content=f"{articles_print}\n\nReferences:\n{references}",
            )

    """
    send_message(
      content=f"Received: {summarised_articles}",
    )
    """
