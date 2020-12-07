import requests
import re
import json
from base64 import b64decode
from contextlib import closing

def get_session():
    s = requests.Session()
    s.headers = {
        'Referer': 'https://www.ixigua.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
    }
    return s
#解析页面
def parse_html(url):
    s =get_session()
    req = s.get(url)
    #将乱码进行编码
    req.encoding = req.apparent_encoding
    #正则匹配，匹配页面源码中需要的内容
    pattern = r'\<script.*?\>window\._SSR_HYDRATED_DATA=(.*?)\</script\>'

    result = re.findall(pattern,req.text)
    #对不规则内容进行修改，然后进行json序列化
    result = result[0].replace(':undefined', ':"undefined"')
    result = json.loads(result)
    #提取电影名字
    title = result["anyVideo"]["gidInformation"]["packerData"]["albumInfo"]["title"]
    #进行base64解码然后对其进行utf-8编码
    video_url = b64decode(result["anyVideo"]["gidInformation"]["packerData"]["videoResource"]["normal"]["video_list"]["video_4"]["main_url"]).decode("utf-8")

    print(title,video_url)
    video_download(title,video_url)

#视频下载
def video_download(title,video_url):
    file_path = r'腾讯视频/{name}.mp4'.format(name=title)
    with closing(requests.get(video_url,  stream=True)) as response:
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


if __name__ == '__main__':
    #电影大赢家视频连接
    url = "https://www.ixigua.com/6802462540510003726"
    #url = "https://www.ixigua.com/api/albumv2/details?_signature=_02B4Z6wo00f01ID.XPAAAIBBIJaTlL.6qiSA.lhAAH-Z80&albumId=6802462540510003726&episodeId=6802476259302441479&block=1"

    parse_html(url)

