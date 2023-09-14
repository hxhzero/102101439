import re
import os
import sys
import csv
import time
import random
import requests
from tqdm import tqdm
from lxml import etree
from bs4 import BeautifulSoup
from openpyxl import workbook


class Spider(object):

    def __init__(self):
        # 搜索页接口请求地址
        self.k_url = 'https://api.bilibili.com/x/web-interface/wbi/search/type?__refresh__=true&_extra=&context=&page={}&page_size=42&order=dm&from_source=&from_spmid=333.337&platform=pc&highlight=1&single_column=0&keyword=%E6%97%A5%E6%9C%AC%E6%A0%B8%E6%B1%A1%E6%9F%93%E6%B0%B4%E6%8E%92%E6%B5%B7&qv_id=kXsLUl6EKJaq5iNfdicro5ipuBMEthQT&ad_resource=5654&source_tag=3&gaia_vtoken=&category_id=&search_type=video&dynamic_offset=0&web_location=1430654&w_rid=8ea24daad5b04ba3e45bc43e7c0e2cf4&wts=1694408151'
        # 弹幕数据请求地址
        self.s_url = 'https://api.bilibili.com/x/v1/dm/list.so?oid={}'
        # 构造请求头 反爬之一
        self.headers = {
            'authority': 'api.bilibili.com',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9',
            # cookie具有时效性 需要定期更换 复制浏览器的headers信息
            'cookie': 'buvid3=80F61146-7F4D-40A2-C006-868F0C0DE34094941infoc; b_nut=1693150094; i-wanna-go-back=-1; b_ut=7; _uuid=5335995D-CF1F-D721-FE6F-2F5C22DB492697030infoc; buvid_fp=066f2bbc6a5d3b7e231799ef88b3d92d; buvid4=6B590103-05E2-5B2C-88B9-F7AE2BD6E5CE96250-023082723-dd0vAJ%2Bkw%2BSgDfXS%2BFpY%2BPZSFFN8mlXc9smFP8Sk0SHGQKyYZceGQw%3D%3D; DedeUserID=395117837; DedeUserID__ckMd5=50032623987aeb6f; header_theme_version=CLOSE; rpdid=0zbfAGUNle|2CITEDNC|2C9|3w1QAhHG; CURRENT_FNVAL=4048; CURRENT_QUALITY=80; home_feed_column=5; browser_resolution=1600-843; bp_video_offset_395117837=839213459785646097; LIVE_BUVID=AUTO8316942363157019; SESSDATA=51c644e7%2C1709912218%2C87ed2%2A91CjBnPIyNej1l9pscs-32_fdSjJ_ckuwWvgdGC2Emzl43AKaI5Q_TZ6fY7MTHoid7RzUSVnFHamQ2VGRBam4tclVoYVc3RnBYWll2SXE5RF9KTDVfdXZsWmlReC1GTmhxS2NtNVZQemJlb1kyeXdHdUgyTF9peWYzcjNxd0pRT1NVLWl4bjZGTUh3IIEC; bili_jct=59a5397cac5fb3f40699889682474f4e; sid=63lt151r; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTQ2ODU1ODcsImlhdCI6MTY5NDQyNjM4NywicGx0IjotMX0.Or9dIcKNAe04hrmaHI2v141Or87MhDyOBFqgW2aBaVA; bili_ticket_expires=1694685587; b_lsid=1094452D3_18A84454398; PVID=1',
            'origin': 'https://www.bilibili.com',
            'referer': 'https://www.bilibili.com/video/BV1Ch411Q73Y/?share_source=copy_web&vd_source=8b17d89fa082dc1a594b586860d2e8ec',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
        }

    def main(self):
        # 翻页采集
        for page in range(1, 11):
            print(f'正在采集第{page}页的数据(一页30视频)————')
            # 提取每一页的URL
            url = self.k_url.format(page)
            # 发送请求
            data = self.get_response(url).json()
            if data:
                # 解析数据 提取数据
                self.parse_detail(data)
            else:
                continue

    def get_response(self, url):
        # 延时请求 (反爬)
        random_t = random.uniform(1, 3)
        time.sleep(random_t)
        # 发送请求
        try:
            # 发送get请求
            response = requests.get(url, headers=self.headers)
            # 编码
            response.encoding = response.apparent_encoding
            if response.status_code == 200:
                return response
            else:
                print(response.status_code, '请求异常')
                return
        except Exception as e:
            print(f'except Exception as e:\n{e}')
            sys.exit(0)

    def parse_detail(self, data):
        # 获取数据列表
        result = data['data']['result']
        # 循环取每个视频的链接地址
        for mes in result:
            arcurl = mes['arcurl']
            # 提取aid号的URL链接
            str_list = list(arcurl)
            str_list.insert(11, 'i')
            url = ''.join(str_list)

            # 发送详情页请求
            data = self.get_response(url).text
            # 获取弹幕cid号
            cid = self.parse_cid(data)
            # 提取弹幕链接
            so_url = self.s_url.format(cid)
            # 发送请求获取弹幕列表
            data = self.get_response(so_url).text

            # 解析并提取弹幕数据
            self.parse_subtitles(data, so_url)
            print(arcurl)
            print('='*100, '\n')

    @staticmethod
    def parse_cid(data):
        # xpath使用
        xml = etree.HTML(data)
        # cid号定位提取
        cid = xml.xpath('//div[@id="dtl"]/div[2]/input[@class="form-control"]/@value')[0]
        return cid

    def parse_subtitles(self, data, url):
        barrages = re.findall('<d\sp=".*?">(.*?)</d>', data)
        for mes in barrages:
            content = re.sub(' |\n|\u200b|', '', mes)
            self.save_csv(content, url)

    def save_csv(self, content, url):
        # 存储弹幕文件
        dir_path = 'subtitles'
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        # 文件名
        file_name = url.split('=')[-1] + '弹幕.csv'
        # 写入数据
        with open(os.path.join(dir_path, file_name), 'a+', encoding='utf-8-sig', newline='') as csvh:
            writer = csv.writer(csvh)
            with open(os.path.join(dir_path, file_name), 'r', encoding='utf-8-sig', newline='') as csvg:
                reader = csv.reader(csvg)
                if not [row for row in reader]:
                    writer.writerow(['弹幕内容'])
                    writer.writerows([[content]])
                else:
                    writer.writerows([[content]])


if __name__ == '__main__':
    # 爬虫程序入口
    Spider().main()
