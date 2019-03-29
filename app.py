# -*- coding: utf-8 -*-
"""
GUI app
@author: yanyongyu
"""

__author__ = "yanyongyu"
__version__ = "1.3.1"

import asyncio
import logging
import traceback
import threading
import webbrowser

import requests
from tkinter import *
from tkinter.ttk import *
from tkinter.messagebox import showinfo, askyesno

import api


class AutoShowScrollbar(Scrollbar):
    # 如果不需要滚动条则会自动隐藏
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("pack", "forget", self)
        else:
            self.pack(fill=Y,side=RIGHT,expand=False)
        Scrollbar.set(self, lo, hi)


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
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/72.0.3626.119 Safari/537.36'}
        self.sess.headers.update(headers)

        self.start_coroutine(self.scan_release())
        self.show()

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
        label1 = Label(frame1, text="请将题目复制到下方输入框，每一行一道题（不带题型）, 题目过长自动换行不影响")
        label1.pack(side=LEFT, fill=BOTH)
        options = list(self.api_list.keys())
        options.insert(0, "自动选择")
        self.v1 = StringVar()
        menu1 = OptionMenu(frame1, self.v1, options[0], *options)
        menu1.pack(side=RIGHT, fill=BOTH)
        label2 = Label(frame1, text="选择题库来源:")
        label2.pack(padx=3, side=RIGHT, fill=BOTH)

        self.isTop = IntVar()
        self.isTop.set(0)
        checkbutton = Checkbutton(frame1, text="窗口置顶", variable=self.isTop)
        checkbutton.pack(padx=3, side=RIGHT, fill=BOTH)
        checkbutton.bind("<ButtonRelease-1>", lambda x: self.root_top_show())

        # 输入框
        frame2 = Frame(self.root, style='White.TFrame')
        frame2.pack(side=TOP, fill=BOTH)
        self.text1 = Text(frame2, height=19, borderwidth=3, font=('微软雅黑', 15))
        self.text1.pack(padx=2, pady=5, side=LEFT, fill=BOTH, expand=True)
        self.text1.focus_set()
        vbar_y = AutoShowScrollbar(frame2, orient=VERTICAL)
        vbar_y.pack(fill=Y, side=RIGHT, expand=False)
        vbar_y.config(command=self.text1.yview)
        self.text1.configure(yscrollcommand=vbar_y.set)
        self.text1.bind("<ButtonRelease-2>", lambda x: self.start_search())

        # 界面鼠标滚动
        def _scroll_text(event):
            self.text1.yview_scroll(int(-event.delta / 60), 'units')

        def _unscroll_text(event):
            return 'break'

        self.text1.bind('<MouseWheel>', _scroll_text)

        # 查询按钮框
        frame3 = Frame(self.root, style='White.TFrame')
        frame3.pack(side=BOTTOM, fill=X)
        button1 = Button(frame3, text="查询", command=self.start_search, style='TButton')
        button1.pack(side=LEFT, expand=True)

        button2 = Button(frame3, text="加入我们", command=self.contact_us, style='TButton')
        button2.pack(side=RIGHT)

        self.root.update()
        self.root.mainloop()

    def root_top_show(self):
        if self.isTop.get():
            self.root.wm_attributes('-topmost', 1)
        else:
            self.root.wm_attributes('-topmost', 1)

    def contact_us(self):
        top = Toplevel(self.root)
        top.geometry('350x150')
        top.resizable(False, False)
        frame = Frame(top)
        frame.pack(fill=BOTH)

        Label(frame, text="全自动插件下载/作者：CodFrm").pack()
        self.plugin = StringVar()
        self.plugin.set("https://github.com/CodFrm/cxmooc-tools/releases")
        entry1 = Entry(frame, width=50, textvariable=self.plugin)
        entry1.pack()
        entry1['state'] = "readonly"
        entry1.bind("<ButtonRelease-1>", lambda x: webbrowser.open(self.plugin.get()))

        Label(frame, text="本软件更新下载地址/作者：Joker").pack()
        self.download = StringVar()
        self.download.set("https://github.com/yanyongyu/CXmoocSearchTool/releases")
        entry2 = Entry(frame, width=50, textvariable=self.download)
        entry2.pack()
        entry2['state'] = "readonly"
        entry2.bind("<ButtonRelease-1>", lambda x: webbrowser.open(self.download.get()))

        Label(frame, text="QQ群号：").pack(side=LEFT)
        self.qq = StringVar()
        self.qq.set("614202391")
        entry3 = Entry(frame, textvariable=self.qq)
        entry3.pack(side=LEFT)
        entry3['state'] = "readonly"

    def start_search(self):
        text = self.text1.get(1.0, END).strip(' \n\r').split('\n')
        logging.info("Text get: %s" % text)
        index = 0

        # 显示toplevel
        top = Toplevel(self.root)
        top.geometry('400x300')
        top.resizable(False, False)
        top.wm_attributes('-topmost', 1)

        # 根框架
        frame_root = Frame(top)
        frame_root.pack(fill=BOTH)

        # 上/下一题按钮
        frame_button = Frame(top)
        frame_button.pack(side=BOTTOM, fill=X)
        previous_button = Button(frame_button, text="上一题")
        previous_button.pack(side=LEFT, expand=True)
        next_button = Button(frame_button, text="下一题")
        next_button.pack(side=RIGHT, expand=True)

        frame_list = [self.show_frame(frame_root) for i in range(len(text))]
        frame_list[index].pack(side=TOP, fill=BOTH, expand=True)

        def _previous(event):
            nonlocal index, frame_list
            if index > 0:
                frame_list[index].pack_forget()
                index -= 1
                frame_list[index].pack(side=TOP, fill=BOTH, expand=True)

        def _next(event):
            nonlocal index, frame_list
            if index < len(frame_list) - 1:
                frame_list[index].pack_forget()
                index += 1
                frame_list[index].pack(side=TOP, fill=BOTH, expand=True)

        previous_button.bind('<ButtonRelease-1>', _previous)
        next_button.bind('<ButtonRelease-1>', _next)
        self.start_coroutine(self.search(frame_list))

    async def search(self, frame_list):
        text = self.text1.get(1.0, END).strip(' \n\r').split('\n')
        if self.v1.get() == "自动选择":
            generator_list = {}
            for api in self.api_list.keys():
                generator_list[api] = self.api_list[api](self.sess, *text)
                await generator_list[api].asend(None)
            for i in range(len(text)):
                label = frame_list[i].children['!canvas'].children['!frame'].children['!label']
                for generator in generator_list.keys():
                    label['text'] = label['text'] + "查询中。。。使用源%s\n" % generator
                    result = await generator_list[generator].asend(i)
                    if result and result[0]['correct']:
                        for answer in result:
                            label['text'] = label['text'] + answer['topic'] + '\n'
                            label['text'] = label['text'] + '答案:' + answer['correct'] + '\n'
                        break
        else:
            generator = self.api_list[self.v1.get()](self.sess, *text)
            await generator.asend(None)
            for i in range(len(text)):
                label = frame_list[i].children['!canvas'].children['!frame'].children['!label']
                label['text'] = label['text'] + "查询中。。。使用源%s\n" % self.v1.get()
                result = await generator.asend(None)
                if not result:
                    label['text'] = label['text'] + "源%s未查询到答案" % self.v1.get()
                elif not result[0]['correct']:
                    label['text'] = label['text'] + result[0]['topic'] + '\n'
                    label['text'] = label['text'] + "源%s未查询到答案" % self.v1.get()
                else:
                    for each in result:
                        label['text'] = label['text'] + each['topic'] + '\n'
                        label['text'] = label['text'] + '答案:' + each['correct'] + '\n'

        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(loop.stop)

    def show_frame(self, frame_root):
        # 总体框架
        frame_out = Frame(frame_root)

        # 显示画布
        canvas = Canvas(frame_out)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        # 内容框架
        frame = Frame(canvas)
        frame_id = canvas.create_window(0, 0, window=frame, anchor=NW)
        # 内容标签
        label1 = Label(frame, text="", wraplength=380)
        label1.pack(side=TOP, fill=BOTH)

        # 动态隐藏滚动条
        vbar = AutoShowScrollbar(frame_out, orient=VERTICAL)
        vbar.pack(fill=Y, side=RIGHT, expand=False)

        # 互相绑定滚动
        vbar.config(command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)

        # 界面鼠标滚动函数
        def _scroll_canvas(event):
            canvas.yview_scroll(int(-event.delta / 60), 'units')

        def _unscroll_canvas(event):
            return 'break'

        # 内容框架大小适配
        def _configure_frame(event):
            # 更新画布的滚动范围以适配内部框架
            size = (frame.winfo_reqwidth(), frame.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if frame.winfo_reqwidth() != canvas.winfo_width():
                # 更新画布大小以适配内部框架
                canvas.config(width=frame.winfo_reqwidth())
            if frame.winfo_reqheight() < canvas.winfo_height():
                canvas.bind_all('<MouseWheel>', _unscroll_canvas)
            else:
                canvas.bind_all('<MouseWheel>', _scroll_canvas)

        def _configure_canvas(event):
            if frame.winfo_reqwidth() != canvas.winfo_width():
                # 更新内部框架大小以适配画布大小
                canvas.itemconfigure(frame_id, width=canvas.winfo_width())

        frame.bind('<Configure>', _configure_frame)
        canvas.bind('<Configure>', _configure_canvas)
        canvas.bind_all('<MouseWheel>', _scroll_canvas)

        return frame_out

    def _start_loop(self, loop):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def start_coroutine(self, coroutine):
        new_loop = asyncio.new_event_loop()
        self.loop = new_loop
        t = threading.Thread(target=self._start_loop, args=(new_loop,))
        t.start()

        asyncio.run_coroutine_threadsafe(coroutine, self.loop)

    async def scan_release(self):
        URL = "https://api.github.com/repos/"\
            "yanyongyu/CXmoocSearchTool/releases/latest"
        try:
            res = self.sess.get(URL)
            res.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.info("Request Exception appeared: %s" % e)
            showinfo(title="超星查题助手",
                     message="检查更新失败了！")
        else:
            info = res.json()
            latest = info['tag_name'].strip("v").split('.')
            now = __version__.split('.')
            if len(latest) < len(now):
                latest.append('0')
            elif len(latest) > len(now):
                now.append('0')
            for i in range(len(now)):
                if latest[i] > now[i]:
                    if askyesno(title="超星查题助手",
                                message="发现新版本！是否前去更新？"):
                        webbrowser.open(info['html_url'])
                    break
        finally:
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(loop.stop)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        app = App()
    except Exception:
        traceback.print_exc()
