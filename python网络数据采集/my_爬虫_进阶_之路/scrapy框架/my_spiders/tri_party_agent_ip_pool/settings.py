# coding:utf-8

'''
@author = super_fazai
@File    : settings.py
@connect : superonesfazai@gmail.com
'''

from fzutils.common_utils import json_2_dict

# 并发量
CONCURRENCY_NUM = 30

# 初始分值
INIT_SCORE = 100

# 最小分值, 小于即被删除
MIN_SCORE = 65

# 每隔2分钟检验一次库内proxy可用性
CHECKED_PROXY_SLEEP_TIME = 2 * 60

# ip_pool中的最小ip数量, 由于tri有时效
# 蜻蜓代理测试实时的可设置为: 100个(比较友好并保证更新监控)
# 蘑菇代理可设置: 500
MIN_IP_POOl_NUM = 150

# server port(默认:8001)
SERVER_PORT = 8001

# 蜻蜓代理api_url
# local
horocn_info_path = '/Users/afa/myFiles/pwd/horocn_info.json'
# server
# horocn_info_path = '/root/horocn_info.json'
with open(horocn_info_path, 'r') as f:
    _ = json_2_dict(f.read())
    HOROCN_API_URL = _['api_url']
    HOROCN_TOKEN = _['token']