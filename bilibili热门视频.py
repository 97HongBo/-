import requests
import json
from contextlib import closing
import time
import threading
import queue
# print(reqs["data"]["next_offset"])

class bili(threading.Thread):
    def __init__(self,url,next_offset,video_queue):
        threading.Thread.__init__(self)
        self.url = url
        self.next_offset = next_offset
        self.video_queue = video_queue
    def ua(self):
        headers = {
            "origin": "https://vc.bilibili.com",
            "referer": "https://vc.bilibili.com/p/eden/hot",
            "user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        }
        return headers
    def get_req(self,url):
        response = requests.get(url,headers=self.ua())
        if response.status_code == 200:
            response = response.content.decode('utf-8')
            #response = response.text
        else:
            response = None
        return response
    def get_video(self,res):
        res = res["data"]["items"]
        for i in res:
            video_name = i["item"]["description"]
            video_name = video_name.replace(" ", "")
            video_url = i["item"]["video_playurl"]
            self.video_queue.put((video_name,video_url))
            print(video_name)
            # print(video_url)

    def run(self):
        #while True:
        url = self.url.format(next_offset=self.next_offset)
        res = self.get_req(url)
        if res:
            res = json.loads(res)
            try:
                self.next_offset = res["data"]["next_offset"]
            except:
                print("可能无next_offset")
                return ""
        try:
            self.get_video(res)
        except:
            print("视频获取出错...")


class download(threading.Thread):
    def __init__(self,video_queue):
        threading.Thread.__init__(self)
        self.video_queue=video_queue
    def ua(self):
        headers = {
            "origin": "https://vc.bilibili.com",
            "referer": "https://vc.bilibili.com/p/eden/hot",
            "user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        }
        return headers
    def run(self):
        while True:
            if video_queue.empty():
                break
            try:
                video_desc = video_queue.get()
                video_name = video_desc[0]
                video_url = video_desc[1]
                print("准备下载！")
                file_path = '抖音/{name}.mp4'.format(name=video_name)

                # proxies={'https': 'https://127.0.0.1:1080', 'http': 'http://127.0.0.1:1080'},
                with closing(requests.get(video_url, headers=self.ua(), stream=True)) as response:
                    chunk_size = 1024  # 单次请求最大值
                    print(response.status_code)
                    content_size = int(response.headers['content-length'])  # 内容体总大小
                    print(content_size)
                    data_count = 0
                    with open(file_path, "wb") as file:
                        for data in response.iter_content(chunk_size=chunk_size):
                            file.write(data)
                            data_count = data_count + len(data)
                            now_jd = (data_count / content_size) * 100
                            print("\r 文件下载进度：%d%%(%d/%d) - %s" % (now_jd, data_count, content_size, file_path), end=" ")
                        print("\n>>> 获取视频成功了！")
            except Exception as e:
                print("视频下载出错：", e)
                with open(r"抖音/log.txt", 'a+', encoding='utf-8') as f:
                    f.write("视频下载出错，错误代码：{error}，采集视频：{video_url}|{video_name}内容".format(error=e, video_url=video_url,video_name=video_name))


            time.sleep(2)
if __name__ == '__main__':
    video_queue = queue.Queue()

    next_offset = "178718"
    url = "https://api.vc.bilibili.com/clip/v1/video/search?page_size=30&next_offset={next_offset}&tag=&need_playurl=1&order=new&platform=pc"
    thread_url = bili(url, next_offset, video_queue)
    thread_video = download(video_queue)
    thread_video1 = download(video_queue)
    thread_video2 = download(video_queue)
    thread_url.start()
    thread_url.join()
    thread_video.start()
    thread_video1.start()
    thread_video2.start()


    # new_video = bili(url,next_offset,video_queue)
    # new_video.run()

