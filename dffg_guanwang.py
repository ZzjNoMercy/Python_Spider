from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from lxml import etree
import requests
import time
import csv

class Dffg_spider(object):
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.base_url = 'https://www.dffengguang.com.cn/dealer'
        self.province_url = []
        # self.city_url = []
        self.headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}

    def run(self):
        self.driver.get(self.base_url)
        WebDriverWait(self.driver,20).until(
            EC.presence_of_element_located((By.XPATH,"//span[@class='city-change']"))
        )
        click_btn = self.driver.find_element_by_xpath("//span[@class='city-change']")
        click_btn.click()
        self.get_province_list(self.driver.page_source)
        self.get_city_url(self.province_url)


    def get_province_list(self,page_source):
        html = etree.HTML(page_source)
        div_tag = html.xpath('//div[@id = "mCSB_1_container"]')[0]
        province_list = div_tag.xpath('./div[@class = "p-item"]')
        for province in province_list:
            province_dict = {}
            province_id = province.xpath('@data-id')[0]
            province_name = province.xpath('@data-name')[0]
            url = 'https://www.dffengguang.com.cn/ajax/city_ajax/?id={}&name={}'.format(province_id,province_name)
            province_dict['url'] = url
            province_dict['省份'] = province_name
            self.province_url.append(province_dict)

    def get_city_url(self,province_url_list):
        while province_url_list:
            city_dict = {}
            city_list_dict = self.province_url.pop()
            city_list_url = city_list_dict['url']
            try:
                r = requests.get(city_list_url,headers = self.headers)
                time.sleep(1)
                html = etree.HTML(r.text)
                city_list = html.xpath('//div[@class = "p-item"]')
                for city in city_list:
                    city_id = city.xpath('@data-id')[0]
                    city_name = city.xpath('@data-name')[0]
                    url = 'https://www.dffengguang.com.cn/ajax/store_ajax/?id={}&name={}'.format(city_id,city_name)
                    print(url,city_list_dict['省份'])
                    self.parse_store_detail(url,city_list_dict['省份'] )
            except:
                self.province_url.append(city_list_url)

    def parse_store_detail(self,city_url,province):
        store_info = {}
        try:
            r = requests.get(city_url,headers = self.headers)
            time.sleep(1)
            html = etree.HTML(r.text)
            store_list = html.xpath('//div[@class = "li-item"]')
            for store in store_list:
                store_name = store.xpath('./div[@class = "tit-name"]/text()')[0]
                store_addr_list = store.xpath('./div[@class = "tit-add"]/text()')
                if store_addr_list:
                    store_addr = store_addr_list[0]
                else:
                    store_addr = '未知'
                store_tel_list = store.xpath('./div[@class = "tit-tel"]/text()')
                if store_tel_list:
                    store_tel = store_tel_list[0]
                else:
                    store_tel = '未知'
                store_info['省份'] = province
                store_info['经销商名称'] = store_name
                store_info['经销商地址'] = store_addr
                store_info['经销商电话'] = store_tel
                print(store_info)
                # self.write_details(store_info)
        except:
            self.parse_store_detail(city_url,province)

    def write_details(self,store_info):
        f = open('dffgdealer_info20190405.csv', 'a')
        w = csv.DictWriter(f, store_info.keys())
        w.writerow(store_info)
        f.close()

if __name__ == '__main__':
    spider= Dffg_spider()
    spider.run()