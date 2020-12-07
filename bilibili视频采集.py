import requests
import re
from pyquery import PyQuery as pq
import json
import time

class bili():
    def __init__(self,url):
        self.url = url
    def ua(self):
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
            "Referer": self.url
        }

        return headers

    def get_req(self,url):
        req = requests.get(url,headers=self.ua(),verify=False)
        if req.status_code == 200:
            req =  req.content.decode("utf-8")
        else:
            req = None
        return req
    def download(self,title,video_url):
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
            "Referer": self.url
        }
        file_path = r'bilibili/{name}.flv'.format(name=title)
        begin = 0
        end = 1024*1024-1
        flag = 0
        print("正在下载")
        while True:
            headers.update({"range": "bytes=" + str(begin) + "-" + str(end)})
            print("字节区间："+ str(begin) + "-" + str(end))
            res = requests.get(video_url, headers=headers,verify=False)
            print(res.status_code)
            time.sleep(2)
            if res.status_code != 416:
                begin = end +1
                end = end +1024*1024
            else:
                headers = headers.update({"range":str(end + 1)+"-"})
                res = requests.get(video_url,headers=headers,verify=False)
                flag= 1
            with open(file_path, 'ab') as fp:
                fp.write(res.content)
                fp.flush()
            print("下载中...")
            if flag == 1:
                fp.close()
                print("下载完成")
                break

    def get_html(self,res):
        pattern = r"window.__playinfo__=(.*?)</script>"
        content = pq(res)
        title = content("span.tit").text()
        print(title)
        try:
            video_url = re.findall(pattern, res)[0]
            video_url = json.loads(video_url)
            video_url = video_url["data"]["dash"]["video"][0]["baseUrl"]
            self.download(title,video_url)
        except Exception as e:
            print("视频获取出错...",e)
            with open(r"bilibili/log.txt", 'a+', encoding='utf-8') as f:
                f.write("视频下载出错，错误代码：{error}，采集视频：{video_url}|{video_name}内容".format(error=e, video_url=video_url,video_name=title))

    def run(self):
        res = self.get_req(self.url)
        if res:
            self.get_html(res)




if __name__ == '__main__':
    #视频地址（BV号）
    url = "https://www.bilibili.com/video/BV1PW411o7sZ"
    bili_video = bili(url)
    bili_video.run()


