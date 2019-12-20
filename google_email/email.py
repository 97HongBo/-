import re
import time
import datetime
from urllib.parse import urlparse,parse_qs
import pymysql
import requests
from user_agent import get_google_header
from multiprocessing import Process,cpu_count,Pool
import queue
import random

# import grequests_new as grequests
import grequests
from functools import wraps
from pyquery import PyQuery as pq

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# # 这个已经不用了
# max_content_size = 100000 # 最大文件大小

# 用来踢掉标签
sub_pt = re.compile("\<[\s\S]{1,}?\>")

# 用来匹配邮箱
mail_pattern = re.compile(r'(?<=[\s:：\<\(\>])[0-9a-zA-Z_\.\*-]{1,50}@[0-9a-zA-Z-\.]{1,50}\.[a-zA-Z0-9]{1,10}', re.I)

# 请求google的时间
google_timeout = (10, 10)

# 每个子链接的运行限制时间（包括建立tcp链接，下载等总的消耗时间，这是为了控制总体的时间消耗）
asynchronous_requests_timeout = 20

# 每个进程管理多少个协程
coroutine_size = 25

# 常用域名后缀
domain_tail_list = [
    ".com",
    ".net",
    ".org",
    ".cn",
    ".com.cn",
    ".net.cn",
    ".org.cn",
    ".gov.cn",
    ".biz",
    ".info",
    ".name",
    ".af",
    ".bh",
    ".bd",
    ".bt",
    ".bn",
    ".mm",
    ".kh",
    ".cy",
    ".kr",
    ".hk",
    ".in",
    ".id",
    ".ir",
    ".iq",
    ".il",
    ".jp",
    ".jo",
    ".kw",
    ".la",
    ".lb",
    ".mo",
    ".my",
    ".mv",
    ".mn",
    ".np",
    ".om",
    ".pk",
    ".ph",
    ".qa",
    ".sa",
    ".sg",
    ".kr",
    ".lk",
    ".sy",
    ".th",
    ".tr",
    ".ae",
    ".ye",
    ".vn",
    ".cn",
    ".tw",
    ".tp",
    ".kz",
    ".kg",
    ".tj",
    ".tm",
    ".uz",
    ".dz",
    ".ao",
    ".bj",
    ".bw",
    ".bi",
    ".cm",
    ".cv",
    ".td",
    ".km",
    ".cg",
    ".dj",
    ".eg",
    ".gq",
    ".et",
    ".ga",
    ".gh",
    ".gn",
    ".gw",
    ".ke",
    ".lr",
    ".ly",
    ".mg",
    ".mw",
    ".ml",
    ".mr",
    ".mu",
    ".ma",
    ".mz",
    ".na",
    ".ne",
    ".ng",
    ".re",
    ".rw",
    ".st",
    ".sn",
    ".sc",
    ".sl",
    ".so",
    ".za",
    ".eh",
    ".sd",
    ".tz",
    ".tg",
    ".tn",
    ".ug",
    ".bf",
    ".zm",
    ".zw",
    ".ls",
    ".sz",
    ".er",
    ".yt",
    ".be",
    ".gb",
    ".de",
    ".fr",
    ".ie",
    ".it",
    ".lu",
    ".nl",
    ".gr",
    ".pt",
    ".es",
    ".al",
    ".ad",
    ".at",
    ".bg",
    ".fi",
    ".gi",
    ".hu",
    ".is",
    ".li",
    ".mt",
    ".mc",
    ".no",
    ".pl",
    ".ro",
    ".sm",
    ".se",
    ".ch",
    ".ee",
    ".lv",
    ".lt",
    ".ge",
    ".am",
    ".az",
    ".by",
    ".md",
    ".ru",
    ".ua",
    ".si",
    ".hr",
    ".cz",
    ".sk",
    ".fo",
    ".rs",
    ".me",
    ".ar",
    ".aw",
    ".bs",
    ".bb",
    ".bz",
    ".br",
    ".ky",
    ".cl",
    ".co",
    ".dm",
    ".cr",
    ".cu",
    ".cw",
    ".do",
    ".ec",
    ".gf",
    ".gd",
    ".gp",
    ".gt",
    ".gy",
    ".ht",
    ".hn",
    ".jm",
    ".mq",
    ".mx",
    ".ms",
    ".ni",
    ".pa",
    ".py",
    ".pe",
    ".pr",
    ".lc",
    ".sv",
    ".sr",
    ".tt",
    ".tc",
    ".uy",
    ".ve",
    ".an",
    ".ca",
    ".us",
    ".gl",
    ".bm",
    ".au",
    ".ck",
    ".fj",
    ".nr",
    ".nc",
    ".vu",
    ".nz",
    ".nf",
    ".pg",
    ".sb",
    ".to",
    ".ws",
    ".ki",
    ".tv",
    ".fm",
    ".mh",
    ".pw",
    ".pf",
    ".wf",
    ".kr",
    ".cn",
    ".tp",
    ".cg",
    ".tz",
    ".cw",
    ".an",
    ".fm",
    ".uk",
]

# 数据库插入语句
save_sql = """
    insert ignore into `存储表`(domain,email,itemid) values(%s,%s,%s)
"""


# 把一个链接只留下主机名,比如：baidu.com-->baidu
def get_host_name_by_url(url):
    domain = get_pure_domain(url)
    host_name = exclude_domain_tail(domain)
    if host_name:
        return host_name.split(".")[-1]
    else:
        return ""

# baidu.com去掉后缀的
def exclude_domain_tail(link):
    link = link.strip("/")
    while True:
        for x in domain_tail_list:
            if link.endswith(x):
                link = link.replace(x, "")
                # print(link, x)
                break
        else:
            break
    return link

def purefy_string(ss):
    new_ss = ss.replace("@ ", "@")
    #return re.sub(sub_pt, "", new_ss)
    return new_ss

def get_google_session():
    """
    get session
    :return:
    """
    s = requests.session()
    s.allow_redirects = True
    s.verify = False
    s.timeout = 20
    s.headers = get_google_header()
    s.keep_alive = False
    s.proxies = {'https': 'https://127.0.0.1:1080', 'http': 'http://127.0.0.1:1080'}
    return s

# 去掉标签和不去掉标签的都匹配一次，避免漏掉
def get_email_from_string(a_string):
    text = purefy_string(a_string)
    email_list = mail_pattern.findall(text)
    email_list += mail_pattern.findall(a_string)
    return email_list

def get_pure_domain(link):
    if link:
        o = urlparse(link)
        if "http" in link:
            return o.netloc.replace("www.", "")
        else:
            return o.path.replace("www.", "")
    return ""

def get_domain():
    domain_list = ['www.google.ac', 'www.google.ad', 'www.google.ae', 'www.google.com.af', 'www.google.com.ag',
                   'www.google.com.ai', 'www.google.al', 'www.google.am', 'www.google.co.ao', 'www.google.com.ar',
                   'www.google.as', 'www.google.at', 'www.google.com.au', 'www.google.az', 'www.google.ba',
                   'www.google.com.bd', 'www.google.be', 'www.google.bf', 'www.google.bg', 'www.google.com.bh',
                   'www.google.bi', 'www.google.bj', 'www.google.com.bn', 'www.google.com.bo', 'www.google.com.br',
                   'www.google.bs', 'www.google.bt', 'www.google.co.bw', 'www.google.by', 'www.google.com.bz',
                   'www.google.ca', 'www.google.com.kh', 'www.google.cc', 'www.google.cd', 'www.google.cf',
                   'www.google.cat', 'www.google.cg', 'www.google.ch', 'www.google.ci', 'www.google.co.ck',
                   'www.google.cl',
                   'www.google.cm', 'www.google.com.co', 'www.google.co.cr', 'www.google.com.cu', 'www.google.cv',
                   'www.google.com.cy', 'www.google.cz', 'www.google.de', 'www.google.dj', 'www.google.dk',
                   'www.google.dm',
                   'www.google.com.do', 'www.google.dz', 'www.google.com.ec', 'www.google.ee', 'www.google.com.eg',
                   'www.google.es', 'www.google.com.et', 'www.google.fi', 'www.google.com.fj', 'www.google.fm',
                   'www.google.fr', 'www.google.ga', 'www.google.ge', 'www.google.gg', 'www.google.com.gh',
                   'www.google.com.gi', 'www.google.gl', 'www.google.gm', 'www.google.gp', 'www.google.gr',
                   'www.google.com.gt', 'www.google.gy', 'www.google.com.hk', 'www.google.hr',
                   'www.google.ht', 'www.google.hu', 'www.google.co.id', 'www.google.iq', 'www.google.ie',
                   'www.google.co.il', 'www.google.im', 'www.google.co.in', 'www.google.is', 'www.google.it',
                   'www.google.je', 'www.google.com.jm', 'www.google.jo', 'www.google.co.jp', 'www.google.co.ke',
                   'www.google.ki', 'www.google.kg', 'www.google.co.kr', 'www.google.com.kw', 'www.google.kz',
                   'www.google.la', 'www.google.com.lb', 'www.google.li', 'www.google.lk',
                   'www.google.co.ls', 'www.google.lt', 'www.google.lu', 'www.google.lv', 'www.google.com.ly',
                   'www.google.co.ma', 'www.google.md', 'www.google.me', 'www.google.mg', 'www.google.mk',
                   'www.google.ml',
                   'www.google.mn', 'www.google.ms', 'www.google.com.mt', 'www.google.mu',
                   'www.google.mv', 'www.google.mw', 'www.google.com.mx', 'www.google.com.my', 'www.google.co.mz',
                   'www.google.com.na', 'www.google.ne', 'www.google.com.nf', 'www.google.com.ng', 'www.google.com.ni',
                   'www.google.nl', 'www.google.no', 'www.google.com.np', 'www.google.nr', 'www.google.nu',
                   'www.google.co.nz', 'www.google.com.om', 'www.google.com.pk', 'www.google.com.pa',
                   'www.google.com.pe',
                   'www.google.com.ph', 'www.google.pl', 'www.google.com.pg', 'www.google.pn', 'www.google.com.pr',
                   'www.google.ps', 'www.google.pt', 'www.google.com.py', 'www.google.com.qa', 'www.google.ro',
                   'www.google.rs', 'www.google.ru', 'www.google.rw', 'www.google.com.sa', 'www.google.com.sb',
                   'www.google.sc', 'www.google.se', 'www.google.com.sg', 'www.google.sh', 'www.google.si',
                   'www.google.sk',
                   'www.google.com.sl', 'www.google.sn', 'www.google.sm', 'www.google.so', 'www.google.st',
                   'www.google.sr',
                   'www.google.com.sv', 'www.google.td', 'www.google.tg', 'www.google.co.th', 'www.google.tk',
                   'www.google.tl', 'www.google.tm', 'www.google.to', 'www.google.tn', 'www.google.com.tr',
                   'www.google.tt', 'www.google.com.tw', 'www.google.co.tz', 'www.google.com.ua', 'www.google.co.ug',
                   'www.google.co.uk', 'www.google.com.uy', 'www.google.co.uz', 'www.google.com.vc', 'www.google.co.ve',
                   'www.google.vg', 'www.google.co.vi', 'www.google.com.vn', 'www.google.vu', 'www.google.ws',
                   'www.google.co.za', 'www.google.co.zm', 'www.google.co.zw', 'www.google.net']
    chooser = random.choice(domain_list)
    return chooser


# 一直请求google，直到成功
def get_html(url, s):
    while True:
        new_url = "https://" + get_domain() + url
        print(new_url)
        try:
            r = s.get(new_url,timeout=google_timeout)
            if r.status_code == 200:
                return pq(r.content)
            else:
                s = get_google_session()
                print(r.status_code)
        except Exception as e:
            s = get_google_session()
            # print(e.__traceback__.tb_lineno,e.__class__,e)
            continue

def init_db():
    """
    init databases
    :return:
    """

    conn = pymysql.connect(host='localhost', user='root', passwd='', db='',
                           port=3306, charset='utf8',
                           cursorclass=pymysql.cursors.DictCursor)
    cur = conn.cursor()
    return cur,conn

def save_db(cur,conn,res,domain,itemid):
    """
    SAVE DB
    :param cur:
    :param conn:
    :param res:
    :return:
    """
    insert_sql = save_sql
    a_list = []
    for m in res:
        a_list.append((domain,m,itemid))
    print("domain results：")
    cur.executemany(insert_sql, a_list)
    conn.commit()

def google_url(items,email_list,domain):
    for item in items.items():
        link = item("div.r>a").attr('href')
        if not link:
            link = item("h3.r>a").attr('href')
        if link:
            o = urlparse(link, 'http')
            if o.netloc:
                link = link
            else:
                if link.startswith('/url?') or link.startswith('/interstitial?'):
                    link = parse_qs(o.query)['url'][0]
                    o = urlparse(link, 'http')
                    if o.netloc:
                        link = link
                else:
                    if o.path.startswith('/url'):
                        link = parse_qs(o.query)['url'][0]
                        o = urlparse(link, 'http')
                        if o.netloc:
                            link = link
                        else:
                            link = None
            text = item.text()
            #print(text)
            tt = ".".join(domain.split(".")[0:-1])
            email = mail_pattern.findall(text)
            if email:
                for i in email:
                     if i.find(tt) > -1:
                         email_list.add(i)
            print(link)
            if link:
                link = link.replace("\n", "").replace("\r", "")
                if len(link.split(".")) > 1:
                    if not link.split(".")[-1].lower() in (
                    "pdf", "xls", "doc", "lsx", "exe", "rar", "zip", "iso", "ppt", "wps", "txt", "mvb", "mp3", "wma",
                    "wav", "jpg", "bmp", "gif", "wfs"):
                        yield grequests.get(link,headers=headers,timeout=(5,10))
                else:
                    yield grequests.get(link, headers=headers,timeout=(5,10))

def exception_handler(request, exception):
    print(request.url, exception)

def log_time(fn):
    @wraps(fn)
    def decorators(args):
        start_time = time.time()
        fn(args)
        print(args["domain"] + " 用时 " + str(int(time.time() - start_time))+ " s")
        print(datetime.datetime.now())
    return decorators

def loop_domain():
    """
    loop domain
    :return:
    """
    while True:
        # 这里为什么是False
        print("waitting a task...")
        task = q.get(block=True)
        print(q.qsize())
        start_fn(task)

@log_time
def start_fn(task):
    """
    :param domain:
    :return:
    """
    domain, itemid = task["domain"], task["itemid"]
    http_domain = task["l_domain"]
    email_list = set()
    print(domain)
    origin_domain = domain
    domain = get_pure_domain(domain)
    kw = 'mail "@' + domain + '"' + " -rocketreach.co"
    url = '/search?num=100&q={query}'.format(query=kw)
    # url = 'https://www.google.com/search?q={query}'.format(query=kw)
    content = get_html(url, s)
    items = content("div.g")
    # gtimeout 就是单独一个协程运行的限定时间
    response_list = grequests.map([m for m in google_url(items,email_list,domain)],stream=False,size=coroutine_size,exception_handler=exception_handler,gtimeout=asynchronous_requests_timeout)
    # domain's host name
    tt = get_host_name_by_url(domain)
    print("host name:", tt)
    for response in response_list:
        if response:
            email = get_email_from_string(response.text)
            # tt = ".".join(domain.split(".")[0:-1])
            # print(email)
            if email:
                for i in email:
                    # 因为这是泛搜索，所以要求对邮箱检查一下
                    if i.find(tt) > -1 and not i.find("**") > -1:
                        email_list.add(i)
            print(response.url, " ", response.status_code)

    google_search_email_list = get_email_from_string(content.text())

    #print(email)
    if google_search_email_list:
        for i in google_search_email_list:
            # 因为这是泛搜索，所以要求对邮箱检查一下
            if i.find(tt) > -1 and not i.find("**")>-1:
                email_list.add(i)

    ####
    print(email_list, domain)
    # return True
    ####
    #save_db(cur, conn, email_list, origin_domain, itemid)
    save_db(cur, conn, email_list, http_domain, itemid)
#本地请求头，已停用
headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
    'Accept-Encoding': "gzip, deflate",
    'Accept': "text/html"
}


if __name__ == '__main__':
    print("getting mysql connection...")
    cur,conn = init_db()
    print("mysql ok!")
    sql = """
        SELECT * FROM `查询表`WHERE  l_domain NOT  in (SELECT  DISTINCT(`domain`) FROM `存储表`)
        """
    #
    cur.execute(sql)
    domain_list = cur.fetchall()
    s = get_google_session()
    # domain_list = [
    #     {"domain": "http://www.digitalputty.com"},
    #     {"domain": "http://www.snavelyforest.com"},
    # ]

    q = queue.Queue()
    print("gen queue ok!")
    for _ in domain_list:
        # print(_["domain"])
        q.put(_)
    print("qsize:", q.qsize())
    print("内核数:"+str(cpu_count()))

    p = Pool(cpu_count())
    p.map(loop_domain())
    p.close()
    p.join()

