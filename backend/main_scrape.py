from dotenv import load_dotenv
from langchain import OpenAI, PromptTemplate, LLMChain

from scraping import scrape_link

NUM_LINKS = 3

sites = [
    {
        "link": "https://fullfact.org/search",
        "id": "gsc-i-id1",
        "urls_class": "gs-title",
    }
]


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


if __name__ == '__main__':
    # Load environment variables (the OpenAI env var in particular)
    load_dotenv()
    articles = []
    for site in sites:
        articles.extend(scrape_link(link=site["link"], id=site["id"], urls_class=site["urls_class"]))
    # print(articles)
    summaries = []
    for article in articles:
        summaries.append({"src": article["src"], "text": summarise(article["text"])})
    print(summaries)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
