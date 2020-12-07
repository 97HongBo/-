from selenium import webdriver
import time
import requests
import json

driver_path = r"E:\工作文件\chromedriver.exe"
temp_url = "http://vv.video.qq.com/getinfo?vids={}&platform=101001&charge=0&otype=json"

def get_brower():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-setuid-sandbox")
    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--window-size=1920,1080")
    # chrome_options.add_argument("--disable-accelerated-2d-canvas")
    # chrome_options.add_argument("==user-agent=" + userAgent)
    # chrome_options.add_argument("--proxy-server=http://192.168.1.196:1080")
    browser = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
    time.sleep(3)
    return browser
def get_page_source(url,browser):
    browser.get(url)
    page_list = browser.find_elements_by_xpath('//div[@id="postlist"]/div[@class="list_item "]')

    for i in page_list:
        title = i.find_element_by_xpath('.//div[@class="figure_detail"]/a').get_attribute("title")
        #vid = i.get_attribute("__wind")
        vid = i.find_element_by_xpath('./a').get_attribute("data-qpvid")
        print(title,"------",vid)
        get_json(title,vid)

def get_json(title,vid):
    new_url = temp_url.format(vid)
    res = requests.get(new_url)
    res_json = json.loads(res.text[len("QZOutputJson="):-1])
    try:
        mp4_url = res_json["vl"]["vi"][0]["ul"]["ui"][0]["url"] + res_json['vl']['vi'][0]['fn'] +"?vkey=" + res_json['vl']['vi'][0]['fvkey']
        reqs = requests.get(mp4_url)
        with open(r'腾讯视频/{name}.mp4'.format(name=title), 'ab') as fp:
            fp.write(reqs.content)
        print(mp4_url)
    except:
        pass

    pass


if __name__ == '__main__':
    url = "http://v.qq.com/s/videoplus/401605311"
    browser = get_brower()
    get_page_source(url,browser)