import chardet
import pymysql
import requests
import re
from user_agent import get_google_header
from pyquery import PyQuery as pq
import traceback

def get_proxies():

    super_proxy_url = ""
    proxy_handler = {
        'http': super_proxy_url,
        'https': super_proxy_url,
    }
    return proxy_handler
def get_session():
    s = requests.session()
    s.allow_redirects = True
    s.verify = False
    s.timeout = 120
    s.proxies = get_proxies()
    s.headers = get_google_header()
    return s

def get_detail_html(url, s, data=""):

    print("detail url:", url)
    while 1:
        r = s.get(url,proxies=get_proxies())
        #print(r.status_code)
        if r.status_code == 200:
            break
        elif r.status_code == 404 or r.status_code == 403 or r.status_code == 410:
            return ""
        else:
            print(r.status_code)
            continue
    try:
        charset = chardet.detect(r.content)
        content = r.content.decode(charset['encoding'])
    except:
        traceback.print()
        content = r.content.decode('utf-8')
    return content

def parse_detail_html(html):
    """
    解析详情页
    :param html:
    :return:
    """
    result =[]

    doc = pq(html)

    info_list = doc('div[class="show-company"] ')
    for tag in info_list.items():
        info_dict = {}
        try:
            info_dict["logo"] = "http://www.thdirectory.com/"+tag('div >div>div>img').attr.src
        except:
            info_dict["logo"] = ""
        info_dict["company_name"] = tag('div >div >div >h2').text().strip().replace("\n","  ")
        info_list2 = tag('div>div>div> table>tr')
        for i in info_list2.items():
            k = i('td:nth-child(1)').text().replace(":","").replace("\n","").lower().strip()
            v = i('td:nth-child(2)').text().strip()
            info_dict[k] = v
            #print(k)

        # if k == "สินค้า และบริการ":
        #     print('!!!!!!')
        #     info_dict["products & services"] +="," + info_dict["สินค้า และบริการ"]
        #     info_dict.pop("สินค้า และบริการ")
        info_dict["product"] = info_dict.get("products & services","")+"," + info_dict.get("สินค้า และบริการ","")
        info_dict.pop("products & services","สินค้า และบริการ")
        info_dict["products_details"] = info_dict.get("products & servicesdetails","") + "," + info_dict.get("รายละเอียดสินค้า และบริการ","")
        info_dict.pop("products & servicesdetails","รายละเอียดสินค้า และบริการ")
        #print(info_dict["product"])
        result.append(info_dict)
    print(result)
    return result



def home_html(html,home_url):
    info=[]
    content =pq(html)
    info_list = content('body > section.blogIntro > div > div > div')
    for i in info_list.items():
        url = home_url + "/" + i('div>a').attr.href
        info.append(url)
    return info


def link_html(html, home_url):
    info = []
    content = pq(html)
    #print(content)
    info_list = content('ul[class = "list-group"] > li')
    for i in info_list.items():
        url = home_url + "/" +i('a').attr.href
        info.append(url)

    return info


def next_html(next_url, home_url):
    content = pq(next_url)
    next_page = content('ul[class="pagination"] > li >a[aria-label="Next"]').attr.href
    next_page = re.findall("\d$", next_page)[0]
    return next_page

if __name__ == "__main__":
    conn = pymysql.connect(host='', user='', passwd='', db='',
                           port=3306, charset='utf8',
                           cursorclass=pymysql.cursors.DictCursor)
    #conn = pymysql.connect(host="192.168.1.196",user="root",passwd = "1234",db ="lhb",port="3306",charset = "utf8", cursorclass=pymysql.cursors.DictCursor)
    cur = conn.cursor()
    sql = "insert into thdirectory_second(`company_name`,`logo`,`domain`,`address`,`email`,`phone`,`fax`,`product`,`products_details`,`new_url`) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    #sql = "insert ignore into th_1(`new_url`) VALUES (%s)"
    insert_sql = "insert into thdirectory_1(`company_name`,`logo`,`domain`,`items`,`item_values`) VALUES (%s,%s,%s,%s,%s)"
    #url_list = ["http://www.thdirectory.com/categorysub.php?categorysub=0101&name=%E0%B8%82%E0%B9%89%E0%B8%AD%E0%B8%95%E0%B9%88%E0%B8%AD%20%E0%B9%81%E0%B8%A5%E0%B8%B0%E0%B9%80%E0%B8%9E%E0%B8%A5%E0%B8%B2%20(Coupling%20&%20Expansion%20Joins%20-%20Axles)&category=01"]
    home_url = "http://www.thdirectory.com"
    try:
        s = get_session()
        url_1 = get_detail_html(home_url,s)
        home_result = home_html(url_1,home_url)
    except:
        home_result = []
    for home_page in home_result:
        try:
            link_url = get_detail_html(home_page,s)
            link_result = link_html(link_url,home_url)
        except:
            link_result =[]
        #print(link_result)
        for page in link_result:
            try:
                next_url = get_detail_html(page, s)
                result = next_html(next_url, home_url)
            except:
                result = 1

            for i in range(1,int(result)):
                return_result = []
                new_url = page + "&page=" + str(i)
                # return_result.append((new_url))
                # cur.executemany(sql,return_result)
                # conn.commit()
                try:
                    html = get_detail_html(new_url,s)
                    result_new = parse_detail_html(html)
                    #print(result_new)
                except:
                    result_new =[]
                    print("可能出错！！")
                for i in result_new:
                    #print(i)
                    return_result.append((i["company_name"],i["logo"],i.get("website"),i.get("address",""),i.get("e-mail",""),i.get("tel",""),i.get("fax",""),i.get("product",""),i.get("products_details"),new_url))
                cur.executemany(sql, return_result)
                conn.commit()

                # for i in result_new:
                #     for k , v in i.items():
                #         if k not in ["company_name","logo","website"]:
                #             return_result.append((i["company_name"],i["logo"],i.get("website"),k,v))
                #cur.executemany(insert_sql, return_result)
                #conn.commit()


