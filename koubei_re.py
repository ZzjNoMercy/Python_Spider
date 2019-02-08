# -*- coding:utf-8 -*-

import requests
from lxml import etree
import time
import random
import csv
import re
from requests import ReadTimeout, ConnectionError

class Spider(object):
    num_url = 'https://k.autohome.com.cn/{}/'
    parse_url = 'https://k.autohome.com.cn/{}/index_{}.html#dataList'
    code_list = ['4139','3465']
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Host': 'k.autohome.com.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'
    }
    PROXY_POOL_URL = 'http://127.0.0.1:5555/random'
    total_num_url_list = []
    request_list = []

    def get_proxy(self):
        # 从代理池获取随机代理
        try:
            response = requests.get(self.PROXY_POOL_URL)
            if response.status_code == 200:
                print('更换代理',response.text)
                return response.text
            return None
        except requests.ConnectionError:
            return None

    def forge_total_num_url(self,code):
        # 方法作用：构造获得每个车型总页数的链接
        url = self.num_url.format(code)
        self.total_num_url_list.append(url)

    def get_total_page_num(self, url):
        # 方法作用：获取车型口碑总页数,并遍历页数，将链接加入到待爬取的request_list中
        p = re.compile('\d+')
        code_num_str = p.findall(url)[0]
        # 获取可用代理
        proxy = self.get_proxy()
        proxies = {'http': proxy,
                   'https': proxy}
        try:
            response = requests.get(url=url,headers = self.headers,proxies = proxies)
            time.sleep(random.randint(1, 3))
            if response.status_code == 200:
                html = etree.HTML(response.text)
                page_num_str_list = html.xpath('//span[@class = "page-item-info"]//text()')
                if page_num_str_list:
                    p = re.compile('\d+')
                    page_num_str = p.findall(page_num_str_list[0])[0]
                    total_num = int(page_num_str)
                    for i in range(total_num):
                        index = i+1
                        new_url = self.parse_url.format(code_num_str,index)
                        self.request_list.append(new_url)
            else:
                # 失败链接重新加入list
                self.total_num_url_list.append(url)
        except (ReadTimeout, ConnectionError):
            self.total_num_url_list.append(url)

    def parse_koubei_detail(self,url):
        # 获取可用代理
        proxy = self.get_proxy()
        proxies = {'http': proxy,
                   'https': proxy}
        try:
            response = requests.get(url=url,headers = self.headers,proxies = proxies)
            time.sleep(random.randint(1,3))
            if response.status_code ==200:
                html = etree.HTML(response.text)
                div_list = html.xpath('//div[@class="choose-con mt-10"]')
                item = {}
                for div in div_list:
                    dl_list = div.xpath('./dl[@class="choose-dl"]')
                    modle = dl_list[0].xpath('./dd//text()')[1]
                    modle_type = dl_list[0].xpath('./dd//text()')[4]
                    city = dl_list[1].xpath('./dd//text()')[0].strip()
                    bought_time = dl_list[3].xpath('./dd//text()')[0].strip()
                    item['车型'] = modle
                    item['款型'] = modle_type
                    item['购车地点'] = city
                    item['购买时间'] = bought_time
                    dl = div.xpath('./dl[@class="choose-dl border-b-no"]')[0]
                    aims_list = dl.xpath('.//p/text()')
                    aims = ','.join(aims_list)
                    item['购车目的'] = aims
                    print(item)
                    self.save_to_csv(item)
            else:
                self.request_list.append(url)
        except (ReadTimeout, ConnectionError):
            self.request_list.append(url)

    def save_to_csv(self,item):
        f = open('口碑-购车目的190208.csv', 'a')
        w = csv.DictWriter(f, item.keys())
        w.writerow(item)
        f.close()

    def schedule(self):
        # 调度方法执行
        while self.total_num_url_list:
            url = self.total_num_url_list.pop(0)
            self.get_total_page_num(url)

        while self.request_list:
            url = self.request_list.pop(0)
            self.parse_koubei_detail(url)

    def run(self):
        for code in self.code_list:
            self.forge_total_num_url(code)
        self.schedule()


if __name__ =='__main__':
    spider = Spider()
    spider.run()