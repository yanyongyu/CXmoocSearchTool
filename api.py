# -*- coding: utf-8 -*-
"""
This is the apis of searching the answer.
@author: yanyongyu
"""

__author__ = "yanyongyu"
__all__ = ["cxmooc_tool", "poxiaobbs", "forestpolice", "bankroft"]

import time
import logging
from hashlib import md5

from lxml import etree
import requests

logging.basicConfig(level=logging.INFO)


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
    data = {}
    for i in range(len(args)):
        data['topic[%d]' % i] = args[i]

    # post请求
    logging.info("Post to cxmooc_tool api.")
    res = sess.post(url, data=data, verify=False)

    # 处理结果
    logging.info("Processing result")
    result = []
    if res.status_code == 200:
        for each in res.json():
            answer = []
            for answ in each['result']:
                temp = {}
                temp['topic'] = answ['topic']
                temp['correct'] = answ['correct'][0]['option']
                answer.append(temp)
            result.append(answer)

    logging.info("Return result: %s" % result)

    return result


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
    data = {}
    result = []
    for i in range(len(args)):
        data['tm'] = args[i]

        # post请求
        logging.info("Post to poxiao bbs php. Question %d" % i)
        res = sess.post(url, data=data, verify=False)

        # 处理结果
        logging.info("Processing result")
        answer = []
        if res.status_code == 200:
            temp = {}
            selector = etree.HTML(res.text)
            answer_div = selector.xpath('//div[@class="ans"]')
            answer_text = answer_div[0].xpath('string(.)')\
                .strip().replace('  ', '').replace('\n', '')
            if "答案：" in answer_text:
                temp['topic'] = answer_text.split("答案：")[0]
                temp['correct'] = answer_text.split("答案：")[1]
                answer.append(temp)
        result.append(answer)

        time.sleep(0.5)

    logging.info("Return result: %s" % result)

    return result


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
    result = []
    data = {}
    for i in range(len(args)):
        data['course'] = ""
        data['type'] = ""
        data['option'] = ""

        # post请求
        logging.info("Post to forest police. Question %d" % i)
        res = sess.post(url + args[i], data=data, verify=False)

        # 处理结果
        logging.info("Processing result")
        answer = []
        if res.status_code == 200:
            temp = {}
            temp['topic'] = args[i]
            temp['correct'] = res.json()['data']
            answer.append(temp)
        result.append(answer)

        time.sleep(0.5)

    logging.info("Return result: %s" % result)

    return result


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
    result = []
    payload = {}
    for i in range(len(args)):
        md = md5()
        md.update((args[i]+string_enc).encode())

        payload['title'] = args[i]
        payload['enc'] = md.hexdigest()

        # post请求
        logging.info("Get bankroft api. Question %d" % i)
        res = sess.get(url, params=payload, verify=False)

        # 处理结果
        logging.info("Processing result")
        answer = []
        if res.status_code == 200:
            json_text = res.json()
            if json_text['code'] == 100:
                temp = {}
                temp['topic'] = args[i]
                temp['correct'] = json_text['data']
                answer.append(temp)
            elif json_text['code'] == 101:
                print(json_text)
                temp = {}
                temp['topic'] = "题目输入不完整！bankroft接口需要除题目类型外完整题目\n"
                temp['correct'] = ""
                answer.append(temp)
            else:
                temp = {}
                temp['topic'] = "bankroft接口查询次数已达上限！\n"
                temp['correct'] = ""
                answer.append(temp)
        result.append(answer)

        time.sleep(0.5)

    logging.info("Return result: %s" % result)

    return result


def cmd():
    pass


if __name__ == "__main__":
    cmd()
