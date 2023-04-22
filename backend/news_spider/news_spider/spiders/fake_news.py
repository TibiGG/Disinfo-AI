# -*- coding: utf-8 -*-
import scrapy


class FakeNewsSpider(scrapy.Spider):
    name = 'fake_news'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com/']

    def parse(self, response):
        # Extract the URL of the news article from the website
        news_url = response.css('a.news-link::attr(href)').get()

        # Follow the link to the news article page and parse its content
        yield scrapy.Request(news_url, callback=self.parse_article)

    def parse_article(self, response):
        # Extract the content of the news article and print it
        article_content = response.css('div').get()
        print(article_content)
