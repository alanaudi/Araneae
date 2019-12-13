from scrapy import Spider
from spider.items import PTTItem
from scrapy import Request

class PTTSpider(Spider):
    name = 'ptt'
    allowed_domains = ['ptt.cc']
    start_urls = ['https://www.ptt.cc/bbs/Gossiping/index.html']

    def start_requests(self):
        yield Request(self.start_urls[0], callback=self.parse, cookies={'over18': 1})

    def parse(self, response):
        filename = response.url.split('/')[-1].strip('.html')
        print(filename)

