# Standard import
import re
from datetime import datetime
from functools import partial
from dateutil import parser

# Scrapy import
from scrapy import Request, Spider
from spider.items import PTTItem

# Third-party import
from baseconv import base16, base64


class PTTSpider(Spider):
    name = 'ptt'
    allowed_domains = ['ptt.cc']

    PTT_URL = "https://www.ptt.cc/bbs"
    _pages = 0

    def __init__(self, **kwargs): # {{{
        super().__init__(**kwargs)
        self.url = f'{self.PTT_URL}/{self.board}'
    # }}}

    def start_requests(self): # {{{
        self.start_urls = [F'https://www.ptt.cc/bbs/{self.board}/index.html']
        yield Request(self.start_urls[0], callback=self.parse, cookies={'over18': 1})
    # }}}

    def parse(self, response):# {{{

        self._pages += 1
        divs = response.css('.r-list-container > div')
        flags = [idx+1 for idx, d in enumerate(divs) if d.xpath('@class').extract()[0] in ['search-bar', 'r-list-sep']]
        divs = divs[flags[0]:(flags[1]-1 if len(flags) == 2 else len(divs))]
        divs = sorted([self._parse_rent(d) for d in divs], key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=True)
        dates = [d['date'] for d in divs]
        divs = list(filter(partial(self._check_date, self.start, self.end), divs))
        for meta in divs:
            yield Request(F'{self.url}/{meta["filename"]}.html', callback=self.parse_post, meta=meta)
    # }}}

    def parse_post(self, response):# {{{
        content_selector = response.css('div#main-content')[0]
        author_selector = response.css('div.article-metaline')[0]
        title_selector = response.css('div.article-metaline')[1]
        time_selector = response.css('div.article-metaline')[2]
        span_f2_selector = content_selector.css('span.f2::text')
        reply_selector = response.css('div.push')

        post = PTTItem()

        _author = author_selector.css('span.article-meta-value::text').extract()[0]
        _timestamp = time_selector.css('span.article-meta-value::text').extract()[0]
        _ip_string = span_f2_selector.extract()[0]
        _ip_result = re.findall(r'※ 發信站: 批踢踢實業坊\(ptt.cc\), 來自: (.*) \((.*)\)', _ip_string)

        post['filename'] = response.meta['filename']
        post['aid'] = self._filename2aid(response.meta['filename'])
        post['title'] = title_selector.css('span.article-meta-value::text').extract()[0]
        post['author'], post['nickname'] = re.findall(r'(.*) \((.*)\)', _author)[0]
        post['timestamp'] = parser.parse(_timestamp)
        if len(_ip_result) > 0:
            post['ip'], post['location'] = _ip_result[0]
        else:
            post['ip'], post['location'] = '', ''

        post['reply'] = {str(i+1):self._parse_reply(item) for i, item in enumerate(reply_selector)}
        post['content'] = content_selector.xpath('//div[@id="main-content"]/text()')[0].extract()
        yield post
    # }}}

    def _parse_rent(self, r): # {{{
        try:
            href = r.css('div.title > a::attr(href)').extract()[0]
            filename = re.search(F'/bbs/{self.board}/(.*).html', href).group(1)
            t, _ = re.findall(r'M\.(.*)\.A\.(.*)', filename)[0]
            date = datetime.fromtimestamp(int(t)).strftime("%Y-%m-%d")
        except:
            filename = ''
            date = '1900-01-01'
        try:
            title = r.css('div.title > a::text').extract()[0]
        except:
            title = r.css('div.title::text').extract()[0]
        author = r.css('div.author::text').extract()[0]

        return {
                    'filename': filename,
                    'date': date,
                    'author': author,
                    'title': title
                }
    # }}}

    @staticmethod
    def _parse_reply(r): # {{{
        tag = r.css("span.push-tag::text").extract()[0].strip()
        userid = r.css("span.push-userid::text").extract()[0].strip()
        content = r.css("span.push-content::text").extract()[0].strip().lstrip(" :")
        ip_datetime = r.css("span.push-ipdatetime::text").extract()[0].strip()
        ip_datetime_term = re.findall(r'([0-9]+(?:\.[0-9]+){3}) (.*)', ip_datetime)
        if len(ip_datetime_term) > 0:
            ip, _datetime = ip_datetime_term[0]
            _datetime = parser.parse(_datetime)
        else:
            ip, _datetime = '', ''

        return {
            "types": tag,
            "username": userid,
            "content": content,
            "ip": ip,
            "datetime": _datetime
        }
    # }}}

    @staticmethod
    def _check_date(start, end, d): # {{{
        if datetime.strptime(d['date'], '%Y-%m-%d') > datetime.strptime(end, '%Y-%m-%d') and \
           datetime.strptime(d['date'], '%Y-%m-%d') <= datetime.strptime(start, '%Y-%m-%d'):
            return True
    # }}}

    @staticmethod
    def _filename2aid(filename): # {{{
        """ Convert ptt filename to aid

        Parameters
        ----------
        filename : str

        Yields
        ------
        str | Article IDentifier in 8 base64 char

        Example
        -------
        M.timestamp.A.random{0xfff} --> #[base64][base64]
        ex: 1197864962.A.476 --> #17PVW2Hs
                                 #12345612

        """

        t, r = re.findall(r'M\.(.*)\.A\.(.*)', filename)[0]

        return base64.encode(t) + base64.encode(base16.decode(r))
    # }}}
