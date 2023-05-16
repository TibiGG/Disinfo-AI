#%%
from typing import List, Dict

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from util import filter_out_nones

NUM_LINKS = 3


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
