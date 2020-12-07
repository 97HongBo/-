import hashlib
import re
import time

import execjs
import requests
def md5(data):
    return hashlib.md5(data.encode('utf-8')).hexdigest()
def get_pc_js( rid,cdn='ws-h5', rate=0):
    """
    通过PC网页端的接口获取完整直播源。
    :param cdn: 主线路ws-h5、备用线路tct-h5
    :param rate: 1流畅；2高清；3超清；4蓝光4M；0蓝光8M或10M
    :return: JSON格式
    """
    s = requests.Session()
    t10 = str(int(time.time()))
    res = s.get('https://m.douyu.com/' + str(rid)).text
    rid = re.search(r'rid":(\d{1,7}),"vipId', res).group(1)
    # did = '10000000000000000000000000001501'
    did = 'bb82646f751229dcf6b3f07d00031601'
    res = s.get('https://www.douyu.com/' + str(rid)).text
    result = re.search(r'(vdwdae325w_64we[\s\S]*function ub98484234[\s\S]*?)function', res).group(1)

    func_ub9 = re.sub(r'eval.*?;}', 'strc;}', result)
    # js = execjs.compile(result)

    js = execjs.compile(func_ub9)

    res = js.call('ub98484234')

    v = re.search(r'v=(\d+)', res).group(1)
    rb = md5(rid + did + t10 + v)

    func_sign = re.sub(r'return rt;}\);?', 'return rt;}', res)
    func_sign = func_sign.replace('(function (', 'function sign(')
    func_sign = func_sign.replace('CryptoJS.MD5(cb).toString()', '"' + rb + '"')

    js = execjs.compile(func_sign)
    params = js.call('sign', rid, did, t10)
    params += '&cdn={}&rate={}'.format(cdn, rate)
    url = 'https://www.douyu.com/lapi/live/getH5Play/{}'.format(rid)
    res = s.post(url, params=params).json()
    return res
if __name__ == '__main__':
    r = input('输入斗鱼直播间号：\n')
    data = get_pc_js(r)
    rtmp_live = data["data"]['rtmp_live']
    print(rtmp_live)
    key = re.search(r'(\d{1,7}[0-9a-zA-Z]+)_?\d{0,4}(/playlist|.m3u8|.flv)', rtmp_live).group(1)
    print(key)
    live_url = "http://tx2play1.douyucdn.cn/live/{}.flv?uuid=".format(key)
    print(live_url)