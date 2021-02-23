import requests
import json
import random
from fake_useragent import UserAgent
from xpinyin import Pinyin

class TuJia:
    def __init__(self,city):
        self.city = city
        self.url = "https://www.tujia.com/bingo/pc/search/searchhouse"
        self.data = self.data_params()
        self.headers = self.ua()
    def ua(self):
        ua = UserAgent()
        userAgent = ua.random
        print(userAgent)
        headers ={
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,my;q=0.8",
            "Connection": "keep-alive",
            "Content-Length": "1101",
            "Content-Type": "application/json;charset=UTF-8",
            # "Cookie": "_fas_uuid=bdd0efbe-7698-4f61-ac2a-2a7e13295cb5-1613639420946; tujia_out_site_landingUrl=https%3A%2F%2Fwww.tujia.com%2F; tujia_out_site_referrerUrl=https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3D7awz0WxWjKxQwJ9xplXysDidu2jWycRxs_bbgVLFTKG%26wd%3D%26eqid%3Daefc3c670001e29700000002602e31a3; gr_user_id=f96b3289-bf4f-4c1d-9af3-3c6a265bbaf2; tujia.com_MobileContext_StartDate=2021-02-20; tujia.com_MobileContext_EndDate=2021-02-21; _fas_session_id=mJKMThbzGSMBeS1AnGn6HtN9ehFh1613814365798; gr_flag=MC45MzA5NjcwNzgxODkzMDA0XzU1MV9wcmluY2U=; tujia.com_PortalContext_UserToken=00000000-0000-0000-0000-000000000000; tujia.com_PortalContext_UserId=0",
            # "Host": "m.tujia.com",
            # "Origin": "https://m.tujia.com",
            # "Referer": "",
            # "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
            "User-Agent":userAgent
        }
        return headers
    def data_params(self):
        pin = Pinyin()
        city_ = pin.get_pinyin(self.city,"")
        data = {
            "pageIndex": 1,
            "pageSize": 20,
            "conditions": [
                {"label": self.city, "type": 1, "value": "66", "hotRecommend": "null", "pingYin": city_, "longitude": 0,
                 "latitude": 0, "conditionType": -1, "redPoint": "false", "selectedType": 0, "scope": 0,
                 "pinYin": city_, "gType": 0},
                {"label": "离店日期", "type": 3, "value": "2021-02-24", "hotRecommend": "null", "longitude": 0,
                 "latitude": 0, "conditionType": -1, "redPoint": "false", "selectedType": 0, "scope": 0, "gType": 0},
                {"label": "入住日期", "type": 2, "value": "2021-02-23", "hotRecommend": "null", "longitude": 0,
                 "latitude": 0, "conditionType": -1, "redPoint": "false", "selectedType": 0, "scope": 0, "gType": 0},
                {"label": "推荐排序", "type": 4, "value": "1", "hotRecommend": "null", "longitude": 0, "latitude": 0,
                 "conditionType": -1, "redPoint": "false", "selectedType": 0, "scope": 0, "gType": 4,
                 "selected": "true"}
            ],
            # "excludeUnitIdSet": [],
            "returnFilterConditions": "false",
            "returnGeoConditions": "false",
            "specialKeyType": 0,
            "returnNavigations": "true"
        }
        # print(data)
        return data
    def req(self):
        data_dict = {}
        try:
            res = requests.post(url=self.url,headers=self.headers,data=json.dumps(self.data))
            res.encoding = res.apparent_encoding
            try:
                data = json.loads(res.text)['data']['items']

                for i in data:
                    data_dict["name"] = i["unitName"]
                    #地址
                    data_dict["address"] = i["address"]
                    #城市名称
                    data_dict["cityName"] = i["cityName"]
                    #区域
                    data_dict["district"] = i["districtName"]
                    #原价
                    data_dict["productPrice"] = i["productPrice"]
                    #成交价
                    data_dict["finalPrice"] = i["finalPrice"]
                    #距离
                    data_dict["distance"] = i["distanceTip"]
                    #摘要
                    summany=[]
                    try:
                        for summ in i["unitSummeries"]:
                            summany.append(summ["text"])
                        data_dict["summany"] = summany
                    except:
                        data_dict["summany"] = ""
                    #标签
                    try:
                        tags = []
                        for tag in i["houseTags"]:
                            tags.append(tag["text"])
                        data_dict["tag"] = tags
                    except:
                        data_dict["tag"] = ""
                    print(data_dict)
            except:

                print("刷新太快，稍后重试...")
        except Exception as e:
            print(e)
            print("请求地址获取出错...")



if __name__ == '__main__':
    # url = "https://www.tujia.com/bingo/pc/search/searchhouse"
    TJ = TuJia("天津")
    TJ.req()


