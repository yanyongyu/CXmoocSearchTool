# -*- coding: utf-8 -*-
"""
GUI app
@author: yanyongyu
"""

__author__ = "yanyongyu"
__version__ = "1.5.1"

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
    "会自动隐藏的滚动条"
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("pack", "forget", self)
        else:
            self.pack(fill=Y, side=RIGHT, expand=False)
        Scrollbar.set(self, lo, hi)


class App():
    PLUGIN_CX_URL = "https://github.com/CodFrm/cxmooc-tools/releases"
    TOOL_URL = "https://github.com/yanyongyu/CXmoocSearchTool/releases"
    ISSUE_URL = "https://github.com/yanyongyu/CXmoocSearchTool/issues"
    QQ_URL = "https://jq.qq.com/?_wv=1027&k=5FPg14d"

    UNFREEZE_JS = r"""
var a=function () {
    var _0x320a = ["body", "onselectstart", "oncopy", "onpaste", "onkeydown", "oncontextmenu", "onmousemove", "ondragstart", "onmousedown", "wrappedJSObject", "*", "getElementsByTagName", "length", "%u5DF2%u89E3%u9664%u590D%u5236%u4E0E%u53F3%u952E%u9650%u5236%uFF01", "\x0D", "%u6B22%u8FCE%u52A0%u5165QQ%u7FA4%u804A%uFF1A614202391", "", "webkitUserSelect", "style", "auto!important", "MozUserSelect", "normal!important"];
    var doc = document;
    var bd = doc[_0x320a[0]];
    bd[_0x320a[1]] = bd[_0x320a[2]] = bd[_0x320a[3]] = bd[_0x320a[4]] = bd[_0x320a[5]] = bd[_0x320a[6]] = bd[_0x320a[1]] = bd[_0x320a[7]] = doc[_0x320a[1]] = doc[_0x320a[2]] = doc[_0x320a[3]] = doc[_0x320a[4]] = doc[_0x320a[5]] = null;
    doc[_0x320a[1]] = doc[_0x320a[5]] = doc[_0x320a[8]] = doc[_0x320a[4]] = function () {
        return true;
    };
    with(document[_0x320a[9]] || document) {
        onmouseup = null;
        onmousedown = null;
        oncontextmenu = null;
    };
    var arAllElements = document[_0x320a[11]](_0x320a[10]);
    for (var i = arAllElements[_0x320a[12]] - 1; i >= 0; i--) {
        var elmOne = arAllElements[i];
        with(elmOne[_0x320a[9]] || elmOne) {
            onmouseup = null;
            onmousedown = null;
        };
    };
    alert(unescape(_0x320a[13]) + _0x320a[14] + unescape(_0x320a[15]));
    bd[_0x320a[18]][_0x320a[17]] = _0x320a[19];
    bd[_0x320a[18]][_0x320a[20]] = _0x320a[21];
}
a()
"""

    def __init__(self):
        # 加载api
        self.api_list = {}
        self.api_on = {}
        for attr in dir(api):
            if attr.startswith('_'):
                continue
            fn = getattr(api, attr)
            if callable(fn) and getattr(fn, '__annotations__', None):
                self.api_list[attr] = fn

        # 初始化session
        self.sess = requests.Session()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) '
                   'Chrome/72.0.3626.119 Safari/537.36'}
        self.sess.headers.update(headers)

        # 初始化text列表
        self.text = []

        self.start_coroutine(self.scan_release(True))
        self.show()

    def show(self):
        "显示主窗口"
        self.root = Tk()
        self.root.title(
                "超星查题助手v%s -designed by ShowTime-Joker" % __version__)
        # 窗口居中坐标
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - 1000) / 2 - 25
        y = (sh - 590) / 2 - 25
        # 宽、高、相对屏幕坐标
        self.root.geometry('%dx%d+%d+%d' % (600, 105, x, y))
        # 不允许缩放
        self.root.resizable(False, False)

        # style初始化
        style = Style()
        style.configure('White.TFrame', background='white')
        style.configure('TMenu', font=('微软雅黑', 12))
        style.configure('TLabel', font=('微软雅黑', 12))
        style.configure('TButton', font=('微软雅黑', 12))

        # 菜单栏
        # 顶级菜单
        menu = Menu(self.root)

        # api子菜单
        api_menu = Menu(menu, tearoff=0)
        for api in self.api_list.keys():
            self.api_on[api] = IntVar()
            self.api_on[api].set(1)
            api_menu.add_checkbutton(label=api, variable=self.api_on[api])
        menu.add_cascade(label="题库来源", menu=api_menu)

        # 插件菜单
        plugin_menu = Menu(menu, tearoff=0)
        plugin_menu.add_cascade(
                label="超星",
                command=lambda: webbrowser.open(App.PLUGIN_CX_URL)
                )
        plugin_menu.add_cascade(
                label="解除右键锁定",
                command=lambda: self.unfreeze_js()
                )
        menu.add_cascade(label="浏览器插件", menu=plugin_menu)

        # 选项菜单
        option_menu = Menu(menu, tearoff=0)
        self.isTop = IntVar()
        self.isTop.set(0)
        option_menu.add_checkbutton(
                label="窗口置顶", variable=self.isTop,
                command=lambda: self.root_top_show()
                )
        menu.add_cascade(label="选项", menu=option_menu)

        # 帮助菜单
        help_menu = Menu(menu, tearoff=0)
        help_menu.add_command(label="使用说明", command=self.usage)
        help_menu.add_command(
                label="检查更新",
                command=lambda: self.start_coroutine(self.scan_release(False))
                )
        help_menu.add_command(
                label="反馈问题",
                command=lambda: webbrowser.open(App.ISSUE_URL)
                )
        help_menu.add_command(
                label="加入我们",
                command=lambda: webbrowser.open(App.QQ_URL)
                )
        menu.add_cascade(label="帮助", menu=help_menu)

        self.root['menu'] = menu

        # 输入框
        frame2 = Frame(self.root, style='White.TFrame')
        frame2.pack(side=TOP, fill=BOTH, expand=True)
        # 显示画布
        canvas = Canvas(frame2, height=70)
        canvas.pack(side=LEFT, fill=X, expand=True)
        # 内容框架
        frame_in = Frame(canvas)
        frame_id = canvas.create_window(0, 0, window=frame_in, anchor=NW)

        # 动态隐藏滚动条
        vbar = AutoShowScrollbar(frame2, orient=VERTICAL)
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
            size = (frame_in.winfo_reqwidth(), frame_in.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if frame_in.winfo_reqwidth() != canvas.winfo_width():
                # 更新画布大小以适配内部框架
                canvas.config(width=frame_in.winfo_reqwidth())
            if len(self.text) <= 3:
                self.root.geometry('%dx%d' % (600, 35 + 70*len(self.text)))
                canvas.config(height=frame_in.winfo_reqheight())
                canvas.bind_all('<MouseWheel>', _unscroll_canvas)
            elif frame_in.winfo_reqheight() < canvas.winfo_height():
                canvas.bind_all('<MouseWheel>', _unscroll_canvas)
            else:
                canvas.bind_all('<MouseWheel>', _scroll_canvas)

        def _configure_canvas(event):
            if frame_in.winfo_reqwidth() != canvas.winfo_width():
                # 更新内部框架大小以适配画布大小
                canvas.itemconfigure(frame_id, width=canvas.winfo_width())

        frame_in.bind('<Configure>', _configure_frame)
        canvas.bind('<Configure>', _configure_canvas)
        canvas.bind_all('<MouseWheel>', _scroll_canvas)
        canvas.bind_all("<ButtonRelease-2>", lambda x: self.start_search())

        # 删除输入框
        def _delete_entry(event):
            button = event.widget
            frame = button.master
            if len(self.text) > 1:
                self.text.remove(frame.children['!text'])
                frame.forget()

        # 增加输入框
        def _create_entry():
            frame = Frame(frame_in)
            frame.pack(side=TOP, expand=True)
            text = Text(frame, height=2, width=45,
                        borderwidth=2, font=('微软雅黑', 15))
            text.grid(row=0, column=0, padx=2, pady=5, rowspan=2)
            delete_button = Button(frame, text="-", width=2)
            delete_button.grid(row=0, column=1, padx=2, pady=2)
            delete_button.bind("<Button-1>", _delete_entry)
            add_button = Button(frame, text="+", width=2,
                                command=_create_entry)
            add_button.grid(row=1, column=1, padx=2, pady=2)
            self.text.append(text)

        _create_entry()

        # 查询按钮框
        frame3 = Frame(self.root, style='White.TFrame')
        frame3.pack(side=BOTTOM, fill=X)
        button1 = Button(frame3, text="查询", command=self.start_search)
        button1.pack(side=LEFT, expand=True)
#        button2 = Button(frame3, text="一键粘贴", command=self.scan_clipboard)
#        button2.pack(side=RIGHT, expand=False)

        self.root.update()
        self.root.mainloop()

    def root_top_show(self):
        "窗口置顶切换"
        if self.isTop.get():
            self.root.wm_attributes('-topmost', 1)
        else:
            self.root.wm_attributes('-topmost', 0)

    def usage(self):
        "显示使用说明窗口"
        top = Toplevel(self.root)
        top.geometry('350x150')
        top.resizable(False, False)
        top.wm_attributes('-topmost', 1)
        frame = Frame(top)
        frame.pack(fill=BOTH)

        Label(frame, text="复制题目到输入框，一个输入框只能输入一题!").pack()
        Label(frame, text="如需多题查询点击 + 号增加输入框。").pack()
        Label(frame, text="本软件自动检测更新").pack()
        Label(frame, text="目前题库包含超星尔雅、知到智慧树。").pack()
        Label(frame, text="如遇到问题请点击帮助-反馈问题").pack()
        Label(frame, text="或点击加入我们加群反馈").pack()

    def unfreeze_js(self):
        "显示解除右键限制说明"
        top = Toplevel(self.root)
        top.geometry('350x150')
        top.resizable(False, False)
        top.wm_attributes('-topmost', 1)
        frame = Frame(top)
        frame.pack(fill=BOTH)

        # 复制到剪切板
        def _copy():
            self.root.clipboard_clear()
            self.root.clipboard_append(App.UNFREEZE_JS)

        Label(frame, text="点击复制按钮，到浏览器页面").pack()
        Label(frame, text="按F12或者Ctrl+Shift+i打开开发者工具").pack()
        Label(frame, text="切换到Console栏粘贴并回车").pack()
        Label(frame, text="提示成功即解除成功！部分浏览器可能不支持").pack()
        Button(frame, text="点我复制", command=_copy).pack()

    def scan_clipboard(self):
        print(self.root.clipboard_get().split('\n'))

    def start_search(self):
        "开始搜索，显示答案窗口"
        text = [each.get(1.0, END).strip(' \n\r') for each in self.text]
        text = list(set(text))
        try:
            text.remove('')
        except ValueError:
            pass
        logging.info("Text get: %s" % text)
        index = 0

        if text:
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

            # 上一题
            def _previous(event):
                nonlocal index, frame_list
                if index > 0:
                    frame_list[index].pack_forget()
                    index -= 1
                    frame_list[index].pack(side=TOP, fill=BOTH, expand=True)

            # 下一题
            def _next(event):
                nonlocal index, frame_list
                if index < len(frame_list) - 1:
                    frame_list[index].pack_forget()
                    index += 1
                    frame_list[index].pack(side=TOP, fill=BOTH, expand=True)

            previous_button.bind('<ButtonRelease-1>', _previous)
            next_button.bind('<ButtonRelease-1>', _next)

            # 开始搜索线程
            logging.info("Start search.")
            self.start_coroutine(self.search(frame_list))

    async def search(self, frame_list):
        text = [each.get(1.0, END).strip(' \n\r') for each in self.text]
        text = list(set(text))
        try:
            text.remove('')
        except ValueError:
            pass
        # 初始化async迭代器
        generator_list = {}
        for api in self.api_list.keys():
            if self.api_on[api].get():
                generator_list[api] = self.api_list[api](self.sess, *text)
                # 启动迭代器
                logging.info("Active generator %s" % api)
                await generator_list[api].asend(None)

        # 查询答案
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

        # 关闭event loop
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

    async def scan_release(self, silence):
        "检查更新"
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
            if latest == now:
                if not silence:
                    showinfo(title="超星查题助手",
                             message="已是最新版本！无需更新。")
                return
            if len(latest) < len(now):
                latest.append('0')
            elif len(latest) > len(now):
                now.append('0')
            for i in range(len(now)):
                if latest[i] > now[i]:
                    if askyesno(title="超星查题助手",
                                message="发现新版本%s！是否前去更新？"
                                % info['tag_name']):
                        webbrowser.open(info['html_url'])
                        if info['assets'][0]['name'].endswith('.exe'):
                            webbrowser.open(
                                    info['assets'][0]['browser_download_url'])
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
