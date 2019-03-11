# -*- coding: utf-8 -*-
"""
This is the apis of searching the answer.
@author: yanyongyu
"""

__author__ = "yanyongyu"
__all__ = ["cxmooc_tool", "poxiaobbs", "forestpolice", "bankroft",
           "jiuaidaikan"]

import sys
import json
import logging
import asyncio
from hashlib import md5

import requests
from lxml import etree

requests.packages.urllib3.disable_warnings()


async def cxmooc_tool(sess: requests.Session,
                      *args: list) -> list:
    # 输入参数处理
    if not isinstance(sess, requests.Session):
        args = list(args)
        args.insert(0, sess)
        args = tuple(args)
        sess = requests.Session()

    # 接口
    url = "https://blog.icodef.com:8081/v2/answer"

    # 接口参数
    index = yield
    data = {}
    for i in range(len(args)):
        data['topic[%d]' % i] = args[i]

    # post请求
    logging.info("Post to cxmooc_tool api.")
    try:
        res = sess.post(url, data=data, verify=False)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.info("Request Exception appeared: %s" % e)
        for each in args:
            answer = []
            answer.append({'topic': str(e), 'correct': ''})
            yield answer
        raise StopIteration

    # 处理结果
    logging.info("Processing result")
    result = [[] for i in range(len(args))]
    for each in res.json():
        for answ in each['result']:
            temp = {}
            temp['topic'] = answ['topic']
            temp['correct'] = ''
            for option in answ['correct']:
                temp['correct'] = temp['correct'] + str(option['option'])
            result[each['index']].append(temp)

    for i in range(len(result)):
        if index and i < index:
            continue
        logging.info("Yield question %s: %s" % (i+1, result[i]))
        index = yield result[i]
    raise StopIteration


async def poxiaobbs(sess: requests.Session,
                    *args: list) -> list:
    # 输入参数处理
    if not isinstance(sess, requests.Session):
        args = list(args)
        args.insert(0, sess)
        args = tuple(args)
        sess = requests.Session()

    # 接口
    url = "https://cx.poxiaobbs.com/index.php"

    # 接口参数
    index = yield
    data = {}
    for i in range(len(args)):
        if index and i < index:
            continue
        data['tm'] = args[i]

        # post请求
        logging.info("Post to poxiao bbs php. Question %d" % i+1)
        try:
            res = sess.post(url, data=data, verify=False)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.info("Request Exception appeared: %s" % e)
            answer = []
            answer.append({'topic': str(e), 'correct': ''})
            index = yield answer
            continue

        # 处理结果
        logging.info("Processing result")
        answer = []
        selector = etree.HTML(res.text)
        answer_div = selector.xpath('/html/body/div[1]/div[@class="ans"]')
        for each in answer_div:
            temp = {}
            answer_text = each.xpath('string(.)')\
                .strip().replace('  ', '').replace('\n', '')
            if "答案：" in answer_text:
                temp['topic'] = answer_text.split("答案：")[0]
                temp['correct'] = answer_text.split("答案：")[1]
                answer.append(temp)

        logging.info("Yield question %s: %s" % (i+1, answer))
        index = yield answer

        await asyncio.sleep(0.5)

    raise StopIteration


async def forestpolice(sess: requests.Session,
                       *args: list) -> list:
    # 输入参数处理
    if not isinstance(sess, requests.Session):
        args = list(args)
        args.insert(0, sess)
        args = tuple(args)
        sess = requests.Session()

    # 接口
    url = "http://mooc.forestpolice.org/cx/0/"

    # 接口参数
    index = yield
    data = {}
    for i in range(len(args)):
        if index and i < index:
            continue
        data['course'] = ""
        data['type'] = ""
        data['option'] = ""

        # post请求
        logging.info("Post to forest police. Question %d" % i)
        try:
            res = sess.post(url + args[i], data=data, verify=False)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.info("Request Exception appeared: %s" % e)
            answer = []
            answer.append({'topic': str(e), 'correct': ''})
            index = yield answer
            continue

        # 处理结果
        logging.info("Processing result")
        answer = []
        temp = {}
        temp['topic'] = args[i]
        temp['correct'] = res.json()['data']
        if temp['correct'] != '未找到答案':
            answer.append(temp)

        logging.info("Yield question %s: %s" % (i+1, answer))
        index = yield answer

        await asyncio.sleep(0.5)

    raise StopIteration


async def bankroft(sess: requests.Session,
                   *args: list) -> list:
    """
    该接口只有当题目完整时可用！
    并且有频率限制！
    """
    # 输入参数处理
    if not isinstance(sess, requests.Session):
        args = list(args)
        args.insert(0, sess)
        args = tuple(args)
        sess = requests.Session()

    # 接口
    string_enc = "-b?M#JvMg2y3$JMk"
    url = "http://123.207.19.72/api/query?"

    # 接口参数
    index = yield
    payload = {}
    for i in range(len(args)):
        if index and i < index:
            continue
        md = md5()
        md.update((args[i]+string_enc).encode())

        payload['title'] = args[i]
        payload['enc'] = md.hexdigest()

        # post请求
        logging.info("Get bankroft api. Question %d" % i)
        try:
            res = sess.get(url, params=payload, verify=False)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.info("Request Exception appeared: %s" % e)
            answer = []
            answer.append({'topic': str(e), 'correct': ''})
            index = yield answer
            continue

        # 处理结果
        logging.info("Processing result")
        answer = []
        json_text = res.json()
        if json_text['code'] == 100:
            temp = {}
            temp['topic'] = args[i]
            temp['correct'] = json_text['data']
            answer.append(temp)
        elif json_text['code'] == 101:
            temp = {}
            temp['topic'] = "题目输入不完整！bankroft接口需要除题目类型外完整题目"
            temp['correct'] = ""
            answer.append(temp)
        else:
            temp = {}
            temp['topic'] = "bankroft接口查询次数已达上限！"
            temp['correct'] = ""
            answer.append(temp)

        logging.info("Yield question %s: %s" % (i+1, answer))
        index = yield answer

        await asyncio.sleep(0.5)

    raise StopIteration


async def jiuaidaikan(sess: requests.Session,
                      *args: list) -> list:
    """
    本题库不支持所有可能题目搜索！
    """
    # 输入参数处理
    if not isinstance(sess, requests.Session):
        args = list(args)
        args.insert(0, sess)
        args = tuple(args)
        sess = requests.Session()

    # 接口
    url = "http://www.92daikan.com/tiku.aspx"

    # 获取接口参数
    try:
        res = sess.get(url, verify=False)
        res.raise_for_status()
        selector = etree.HTML(res.text)
        viewstate = selector.xpath('//*[@id="__VIEWSTATE"]/@value')
        viewstategenerator = selector.xpath(
                '//*[@id="__VIEWSTATEGENERATOR"]/@value')
        eventvalidation = selector.xpath(
                '//*[@id="__EVENTVALIDATION"]/@value')
    except requests.exceptions.RequestException as e:
        logging.info("Request Exception appeared: %s" % e)
        index = yield
        for i in range(len(args)):
            if index and i < index:
                continue
            answer = []
            answer.append({'topic': str(e), 'correct': ''})
            yield answer
        raise StopIteration

    # 接口参数
    index = yield
    data = {}
    data['__VIEWSTATE'] = viewstate
    data['__VIEWSTATEGENERATOR'] = viewstategenerator
    data['__EVENTVALIDATION'] = eventvalidation
    data['ctl00$ContentPlaceHolder1$gen'] = '查询'
    for i in range(len(args)):
        if index and i < index:
            continue
        data['ctl00$ContentPlaceHolder1$timu'] = args[i]

        # post请求
        logging.info("Post to 92daikan. Question %d" % i)
        try:
            res = sess.post(url, data=data, verify=False)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.info("Request Exception appeared: %s" % e)
            answer = []
            answer.append({'topic': str(e), 'correct': ''})
            index = yield answer
            continue

        # 处理结果
        logging.info("Processing result")
        answer = []
        selector = etree.HTML(res.text)
        temp = {}
        temp['topic'] = args[i]
        temp['correct'] = selector.xpath('//*[@id="daan"]/text()')[0]
        if temp['correct'] != '未找到答案':
            answer.append(temp)

        logging.info("Yield question %s: %s" % (i+1, answer))
        index = yield answer

        await asyncio.sleep(0.5)

    raise StopIteration


async def wangke120(sess: requests.Session,
                    *args: list) -> list:
    # 输入参数处理
    if not isinstance(sess, requests.Session):
        args = list(args)
        args.insert(0, sess)
        args = tuple(args)
        sess = requests.Session()

    # 接口
    url = "https://wangke120.com/selectCxDb.php"

    # 接口参数
    index = yield
    data = {}
    for i in range(len(args)):
        if index and i < index:
            continue
        data['question'] = args[i]

        # post请求
        logging.info("Post to wangke120. Question %d" % i)
        try:
            res = sess.post(url, data=data, verify=False)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.info("Request Exception appeared: %s" % e)
            answer = []
            answer.append({'topic': str(e), 'correct': ''})
            index = yield answer
            continue

        # 处理结果
        logging.info("Processing result")
        answer = []
        temp = {}
        temp['topic'] = args[i]
        temp['correct'] = res.text
        if temp['correct'] != '未找到':
            answer.append(temp)
        logging.info("Yield question %s: %s" % (i+1, answer))
        index = yield answer

        await asyncio.sleep(0.5)

    raise StopIteration


async def cmd():
    # 获取所有api
    api_list = {}
    for each in globals().keys():
        if each.startswith('_'):
            continue
        fn = globals()[each]
        if callable(fn):
            if getattr(fn, '__annotations__', None):
                api_list[each] = fn

    args = sys.argv[1:]
    if not args or "-h" in args:
        print("超星查题助手\n\tpython api.py [-json] [-api=] -text=\nusage:")
        print("\t-h\tPrint help")
        print("\t-json\tReturn json data at last")
        print("\t-api\tUsing the specified api\n\t\tapi list:")
        for each in api_list.keys():
            print("\t\t\t%s" % each)
        print("\t-text\tquestion(-text can be used more than one time)")
    else:
        # 接收命令行参数
        text = []
        search = None
        JSON = False
        for each in args:
            if each.startswith("-json"):
                JSON = True
            elif each.startswith("-api="):
                if search is not None:
                    raise ValueError("More than one specified api.")
                if each[5:] in api_list:
                    search = api_list[each[5:]]
                else:
                    raise ValueError("Unknow api. Use -h for help.")
            elif each.startswith("-text="):
                text.append(each[6:])
            else:
                ValueError("Unknow option %s. Use -h for help"
                           % each.split("=")[0])

        # 获取答案
        answer = [[] for i in range(len(text))]
        if not search:
            for each in api_list.keys():
                remain = [text[i] for i in range(len(text)) if not answer[i]]
                if remain:
                    generator = api_list[each](*remain)
                    for i in range(len(text)):
                        result = await generator.asend(None)
                        if not result or not result[0]['correct']:
                            continue
                        else:
                            answer[i] = result
        else:
            if text:
                generator = search(*text)
                for i in range(len(text)):
                    result = await generator.asend(None)
                    if not result or not result[0]['correct']:
                        answer.append([])
                    else:
                        answer.append(result)

        if not JSON:
            print(answer)
        else:
            print(json.dumps(answer))
#        json.dump(answer, open("anwser.json", "w"))


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARN)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cmd())
