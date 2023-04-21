# This is a sample Python script.
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

def print_hi(name):
    load_dotenv()
    llm = OpenAI(temperature=0.9)
    prompt = PromptTemplate(
        input_variables=["product"],
        template="What would be a good company name for a company that makes {product}?"
    )
    product = "colorful socks"
    print(prompt.format(product=product))

    chain = LLMChain(llm=llm, prompt=prompt)
    chain_output = chain.run(product)
    print(chain_output)



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
