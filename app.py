# -*- coding: utf-8 -*-
"""
GUI app
@author: yanyongyu
"""

__author__ = "yanyongyu"

import asyncio
import logging
import traceback
import threading

import requests
from tkinter import *
from tkinter.ttk import *

import api


class App():

    def __init__(self):
        # 加载api
        self.api_list = {}
        for attr in dir(api):
            if attr.startswith('_'):
                continue
            fn = getattr(api, attr)
            if callable(fn):
                if getattr(fn, '__annotations__', None):
                    self.api_list[attr] = fn

        # 初始化session
        self.sess = requests.Session()

        # 答案显示窗口list
        self.toplevel_list = []

    def show(self):
        self.root = Tk()
        self.root.title("超星查题助手 -designed by ShowTime-Joker")
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - 1000) / 2 - 25
        y = (sh - 590) / 2 - 25
        self.root.geometry('%dx%d+%d+%d' % (1000, 590, x, y))
        self.root.resizable(False, False)

        # style初始化
        style = Style()
        style.configure('White.TFrame', background='white')
        style.configure('TLabel', font=('微软雅黑', 12))
        style.configure('TButton', font=('微软雅黑', 12))

        # 提示框
        frame1 = Frame(self.root)
        frame1.pack(side=TOP, fill=X)
        label1 = Label(frame1, text="请将题目复制到下方输入框，每行一道题（不带题型）")
        label1.pack(side=LEFT, fill=BOTH)
        options = list(self.api_list.keys())
        options.insert(0, "自动选择")
        self.v1 = StringVar()
        menu1 = OptionMenu(frame1, self.v1, options[0], *options)
        menu1.pack(side=RIGHT, fill=BOTH)
        label2 = Label(frame1, text="选择题库来源:")
        label2.pack(padx=3, side=RIGHT, fill=BOTH)

        # 输入框
        frame2 = Frame(self.root, style='White.TFrame')
        frame2.pack(side=TOP, fill=BOTH)
        self.text1 = Text(frame2, height=19, borderwidth=3, font=('微软雅黑', 15))
        self.text1.pack(padx=2, pady=5, side=TOP, fill=BOTH)

        frame3 = Frame(self.root, style='White.TFrame')
        frame3.pack(side=BOTTOM, fill=X)
        button1 = Button(frame3, text="查询", command=self.start_search, style='TButton')
        button1.pack(side=TOP)

        self.root.update()
        self.root.mainloop()

    async def search(self):
        text = self.text1.get(1.0, END).strip(' \n\r').split()
        for each in text:
            await self.show_result(each)
        if self.v1.get() == "自动选择":
            for each in self.api_list.keys():
                if text:
                    index = 0
                    label = self.toplevel_list[index].children['!label']
                    label['text'] = label['text'] + "查询中。。。使用源%s\n" % each
                    result = await self.api_list[each](self.sess, *text)
                    for i in range(len(text)):
                        if not result[i]:
                            label['text'] = label1['text'] + "源%s未查询到答案\n" % each
                            index += 1
                        else:
                            for each in result[i]:
                                if not each['correct']:
                                    label['text'] = label['text'] + each['topic\n']
                                    index += 1
                                else:
                                    label['text'] = label['text'] + each['topic'] + '\n'
                                    label['text'] = label['text'] + '答案:' + each['correct']
                                    self.toplevel_list.pop(index)
                                    text.pop(index)
        else:
            result = await self.api_list[self.v1.get()](self.sess, *text)
            for i in range(len(text)):
                label = self.toplevel_list[0].children['!label']
                if not result[i]:
                    label['text'] = label['text'] + "源%s未查询到答案" % self.v1.get()
                else:
                    for each in result[i]:
                        label['text'] = label['text'] + each['topic'] + '\n'
                        label['text'] = label['text'] + '答案:' + each['correct']
                self.toplevel_list.pop(0)

    async def show_result(self, text):
        top = Toplevel(self.root)
        top.geometry('400x300')
        top.resizable(False, False)
        label1 = Label(top, text="", wraplength=400)
        label1.pack(side=TOP, fill=BOTH)
        self.toplevel_list.append(top)

    def start_loop(self, loop):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def start_search(self):
        coroutine = self.search()
        new_loop = asyncio.new_event_loop()
        self.loop = new_loop
        t = threading.Thread(target=self.start_loop, args=(new_loop,))
        t.start()

        asyncio.run_coroutine_threadsafe(coroutine, self.loop)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        app = App()
        app.show()
    except Exception:
        traceback.print_exc()
