# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class SpiderItem(scrapy.Item):
    html = scrapy.Field()
    aid = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    nickname = scrapy.Field()
    timestamp = scrapy.Field()
    content = scrapy.Field()
    ip = scrapy.Field()
    location = scrapy.Field()
    reply = scrapy.Field()
