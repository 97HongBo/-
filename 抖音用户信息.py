import requests
import re
import json

class DouYin:

    def __init__(self,url):
        self.url = url
        # self.sec_id = re.findall(r"sec_uid=(.*?)\&",s.get(sec_id).url)[0]

    def get_session(self):
        s = requests.Session()
        s.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
        }
        return s
    def get_real_url(self):
        s = self.get_session()
        sec_id = re.findall(r"sec_uid=(.*?)\&",s.get(self.url).url)[0]
        user_url = "https://www.iesdouyin.com/web/api/v2/user/info/?sec_uid={sec_id}".format(sec_id=sec_id)
        return user_url
    def parse_json(self,contents):
        info = {}
        #昵称
        info["nickname"] = contents["user_info"]["nickname"]
        #简介
        info["infomation"] = contents["user_info"]["signature"]
        #作品数量
        info["aweme_count"] = contents["user_info"]["aweme_count"]
        #粉丝
        info["follower_count"] = contents["user_info"]["follower_count"]
        #喜欢
        info["favoriting_count"] = contents["user_info"]["favoriting_count"]
        #抖音ID
        info["unique_id"] = contents["user_info"]["unique_id"]
        #获赞
        info["total_favorited"] = contents["user_info"]["total_favorited"]
        #大头像
        info["avatar_larger"] = contents["user_info"]["avatar_larger"]["url_list"][0]
        #关注
        info["following_count"] = contents["user_info"]["following_count"]
        return info
    def run(self):
        s = self.get_session()
        user_url =self.get_real_url()
        info = s.get(user_url).json()
        info = self.parse_json(info)
        print(info)


if __name__ == '__main__':
    url = input("请输入抖音用户链接...如：https://v.douyin.com/Jg2P4jy/ :\n")
    dy = DouYin(url)
    dy.run()