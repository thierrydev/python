# coding:utf-8

'''
@author = super_fazai
@File    : utils.py
@connect : superonesfazai@gmail.com
'''

from requests import session
from scrapy.selector import Selector
from fzutils.common_utils import json_2_dict
from fzutils.internet_utils import get_random_phone_ua

def judge_ip_is_anonymity(ip_address='', port=0, httpbin=True, use_proxy=True, timeout=10):
    '''
    返回当前IP地址(用于判断ip地址是否高匿)
    :param ip_address:
    :param port:
    :return:
    '''
    def _get_proxies():
        return {
            # 'http': ip_address + ':' + str(port),     # 暴露原地址
            'https': ip_address + ':' + str(port),
        }

    url = 'https://www.whatismybrowser.com/' if not httpbin else 'https://www.httpbin.org/get'
    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': get_random_phone_ua(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    with session() as s:
        with s.get(url=url, headers=headers, proxies=_get_proxies() if use_proxy else {}, timeout=timeout, verify=False) as response:
            if not httpbin:
                now_ip = Selector(text=response.text).css('div#ip-address:nth-child(2) .detected-column a:nth-child(1) ::text').extract_first() or ''
            else:
                now_ip = json_2_dict(response.text).get('origin', '')

            return now_ip
