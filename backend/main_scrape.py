# This is a sample Python script.
import time
from typing import List, Dict

from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

NUM_LINKS = 3


def filter_out_nones(l: list):
    return [x for x in l if x is not None]


sites = [
    {
        "link": "https://fullfact.org/search",
        "id": "gsc-i-id1",
        "urls_class": "gs-title",
    }

]


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
    wait = WebDriverWait(driver, 10)
    search_results: list = wait.until(EC.presence_of_all_elements_located((By.XPATH,
                                                                           f"//a[contains(@class, '{urls_class}')]")))

    urls = filter_out_nones([result.get_attribute("href") for result in search_results])[:NUM_LINKS]
    print(urls)
    articles = []
    for url in urls:
        driver.get(url)
        try:
            main_div = wait.until(EC.presence_of_element_located((By.TAG_NAME, "article")))
            text = main_div.text
            articles.append({"src": url, "text": text})
            # print(text)
        except TimeoutException:
            # print("NO ARTICLE IN THIS LINK")
            pass

    # close the browser
    driver.quit()
    # time.sleep(1000)
    return articles


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    articles = []
    for site in sites:
        articles.extend(scrape_link(link=site["link"], id=site["id"], urls_class=site["urls_class"]))
    print(articles)
    # print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
