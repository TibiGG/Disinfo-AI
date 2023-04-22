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
    wait = WebDriverWait(driver, 5)
    search_results: list = wait.until(EC.presence_of_all_elements_located((By.XPATH,
                                                                           f"//a[contains(@class, '{urls_class}')]")))

    urls = list(dict.fromkeys(filter_out_nones([result.get_attribute("href") for result in search_results])))
    print(urls)
    articles_scraped = 0
    articles = []
    for url in urls:
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
    load_dotenv()
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


@on_message  # this function will be called every time a user inputs a message in the UI
def main(message: str):
    load_dotenv()

    summarised_articles = main_scrape(message)

    # send back a reply to the user
    send_message(
      content=f"Received: {summarised_articles}",
    )
