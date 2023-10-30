# D3D4D9, 4B88A2,                FFF9FB b
#                 BB0A21, 252627 w

import tkinter as tk
from tkinter import filedialog
import tkcalendar as tkc
import pyglet, os
from ctypes import windll
from PIL import ImageTk, Image
import sqlite3
import requests

def parse_request(s):
    words = s.split()
    if words[0].upper() != "SELECT":
        return tuple(["Raw data"])
    if words[1] == "*":
        if words[3] == "videos":
            return ("id", "date", "preview", "msg_cnt")
        elif words[3] == "messages":
            return ("id", "text", "date", "user_id", "video_id")
        elif words[3] == "users":
            return ("id", "name", "username", "pfp")
    else:
        return tuple(s[len("SELECT "):s.upper().find(" FROM")].split(", "))

def divide_str(s):
    i = 0
    k = 0
    flag = False
    while i < len(s):
        if k % 65 == 0 and k != 0:
            flag = True
        if s[i] == '\n':
            k = 0
        if flag and s[i] == ' ':
            s = s[:i:] + '\n' + s[i + 1::]
            flag = False
            k = 0
        i += 1
        k += 1
    return s

class Style:
    def __init__(self, pad=4, bg='#4B88A2', ol='#D3D4D9', bright='#BB0A21', bol='#252627', add='#FFF9FB', \
                 font='JetBrains Mono Regular', font_path='bin/JBM.ttf'):
        self.pad = pad       # padding
        self.bg = bg         # background
        self.ol = ol         # outline
        self.bright = bright # bright (important)
        self.bol = bol       # bright outline
        self.add = add       # additional
        self.font = font

        self.normal = 11 # font sizes
        self.small = 10  #

        if len(font_path) > 0:
            pyglet.font.add_file(font_path)

class Window(tk.Tk):   
    def __init__(self, W, H):
        # database interface
        self.con = sqlite3.connect("youtube.db")
        self.cur = self.con.cursor()
        self.default_req = "SELECT video_id, username, date, pfp, text FROM messages INNER JOIN users ON messages.user_id = users.id"
        self.req_params = dict()
        
        # GUI
        super().__init__()
        self.title("Data base manager")
        self.geometry(f"{int(W)}x{int(H)}")
        self.config(bg=style.bg)
        self.attributes("-fullscreen", True)

        self.bind("<Escape>", self.pressed_exit)

        self.flags = {"user": tk.IntVar(), "vid": tk.IntVar(), "date": tk.IntVar(), "substr": tk.IntVar()}

        # setup the control panel frame
        control_frame = tk.Frame(self, height=60, width=W, bg=style.ol, highlightthickness=1, highlightbackground=style.bol)
        control_frame.pack_propagate(0)
        control_frame.pack(fill=tk.BOTH)

        # setup the control panel itself
        self.button_reset = tk.Button(control_frame, text='Reset', font=(style.font, style.normal), bg=style.add, fg=style.bol, command=self.reset_table)
        self.button_reset.pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, pady=(style.pad, style.pad))
        
        txt = tk.Label(control_frame, text='Username:', font=(style.font, style.normal), bg=style.ol, fg=style.bol)
        txt.pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, pady=(style.pad, style.pad))

        self.un = tk.StringVar()
        self.un.trace("w", self.un_update)
        self.entry_un = tk.Entry(control_frame, width=15, textvariable=self.un, font=(style.font, style.normal), bg=style.add, fg=style.bol)
        self.entry_un.pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, pady=(style.pad, style.pad))

        txt = tk.Label(control_frame, text=' Video (url/id):', font=(style.font, style.normal), bg=style.ol, fg=style.bol)
        txt.pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, pady=(style.pad, style.pad))

        self.vid = tk.StringVar()
        self.vid.trace("w", self.vid_update)
        self.entry_vid = tk.Entry(control_frame, width=15, textvariable=self.vid, font=(style.font, style.normal), bg=style.add, fg=style.bol)
        self.entry_vid.pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, pady=(style.pad, style.pad))

        txt = tk.Label(control_frame, text=' From:', font=(style.font, style.normal), bg=style.ol, fg=style.bol)
        txt.pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, pady=(style.pad, style.pad))

        self.from_date = tk.StringVar()
        self.to_date = tk.StringVar()
        self.from_date.trace("w", self.date_update)
        self.to_date.trace("w", self.date_update)
        self.cal_from = tkc.DateEntry(control_frame, date_pattern='yyyy-mm-dd', font=(style.font, style.normal), \
                                      width=12, background=style.bright, foreground=style.ol, textvariable=self.from_date)
        self.cal_from.pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, pady=(style.pad, style.pad))

        txt = tk.Label(control_frame, text='To:', font=(style.font, style.normal), bg=style.ol, fg=style.bol)
        txt.pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, pady=(style.pad, style.pad))

        self.cal_to = tkc.DateEntry(control_frame, date_pattern='yyyy-mm-dd', font=(style.font, style.normal), \
                                    width=12, background=style.bright, foreground=style.ol, textvariable=self.to_date)
        self.cal_to.pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, pady=(style.pad, style.pad))

        txt = tk.Label(control_frame, text='Search for:', font=(style.font, style.normal), bg=style.ol, fg=style.bol)
        txt.pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, padx=(style.pad * 10, 0), pady=(style.pad, style.pad))

        self.substr = tk.StringVar()
        self.substr.trace("w", self.substr_update)
        self.entry_substr = tk.Entry(control_frame, width=15, textvariable=self.substr, font=(style.font, style.normal), bg=style.add, fg=style.bol)
        self.entry_substr.pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, pady=(style.pad, style.pad), expand=1)

        self.button_exit = tk.Button(control_frame, text='Exit', font=(style.font, style.normal), bg=style.bright, fg=style.add, command=self.pressed_exit)
        self.button_exit.pack(side=tk.RIGHT, anchor=tk.NE, padx=(style.pad * 10, style.pad), pady=(style.pad, style.pad))

        # setup the checkbox panel frame
        checkbox_frame = tk.Frame(self, height=40, width=W, bg=style.ol, highlightthickness=1, highlightbackground=style.bol)
        checkbox_frame.pack_propagate(0)
        checkbox_frame.pack(fill=tk.BOTH)

        # setup the panel itself
        self.flags["date"].trace("w", self.date_update)
        self.flags["user"].trace("w", self.un_update)
        self.flags["vid"].trace("w", self.vid_update)
        self.flags["substr"].trace("w", self.substr_update)
        self.checks = dict()
        
        self.checks['user'] = tk.Checkbutton(checkbox_frame, text='username', variable=self.flags['user'], font=(style.font, style.small), bg=style.ol, fg=style.bol)
        self.checks['user'].pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, expand=1)

        self.checks['vid'] = tk.Checkbutton(checkbox_frame, text='video', variable=self.flags['vid'], font=(style.font, style.small), bg=style.ol, fg=style.bol)
        self.checks['vid'].pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, expand=1)

        self.checks['date'] = tk.Checkbutton(checkbox_frame, text='date', variable=self.flags['date'], font=(style.font, style.small), bg=style.ol, fg=style.bol)
        self.checks['date'].pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, expand=1)

        self.checks['substr'] = tk.Checkbutton(checkbox_frame, text='search', variable=self.flags['substr'], font=(style.font, style.small), bg=style.ol, fg=style.bol)
        self.checks['substr'].pack(fill=tk.BOTH, side=tk.LEFT, anchor=tk.NW, expand=1)

        # setup the preview panel frame
        preview_frame = tk.Frame(self, height=60, width=60, bg=style.bg, highlightthickness=1, highlightbackground=style.bol)
        preview_frame.pack_propagate(0)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # setup the preview panel itself
        load_frame = tk.Frame(preview_frame, height=400, bg=style.bg)
        load_frame.pack_propagate(0)
        load_frame.pack(side=tk.TOP, fill=tk.X)
        
        img_data = ImageTk.PhotoImage(Image.open('bin/placeholder.png').resize((640, 480)))
        self.img = tk.Label(preview_frame, image=img_data, bg=style.bg, borderwidth=2, relief='solid')
        self.img.image = img_data
        self.img.bind("<ButtonRelease-1>", self.save_image)
        self.img.pack(side=tk.TOP, anchor=tk.CENTER)
        s = "Choose data entry from right"
        s = divide_str(s)
        
        self.descr = tk.Label(preview_frame, bg=style.bol, fg=style.add, text=s, font=(style.font, 10), anchor='w', justify='left')
        self.descr.pack(anchor=tk.CENTER, expand=1)

        # setup the result panel frame
        result_frame = tk.Frame(self, height=60, width=60, bg=style.bg, highlightthickness=1, highlightbackground=style.bol)
        result_frame.pack_propagate(0)
        result_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # setup the result panel itself
        s = tk.ttk.Style()
        s.theme_use("clam")
        s.map('Treeview', background=[('selected', style.bright)])
        s.configure('Treeview', rowheight=40)
        s.configure("Treeview.Heading", font=(style.font, style.normal), background=style.ol, foreground=style.bol)
        s.configure("Treeview", font=(style.font, style.small))
        s.configure("Treeview", background=style.ol, foreground=style.bol)
        
        self.columns = ("video", "date", "author", "preview")
        self.table = tk.ttk.Treeview(result_frame, show='headings', height=25, columns=self.columns)
        self.table.pack_propagate(0)

        self.reset_table()

        scroll = tk.ttk.Scrollbar(self.table, orient=tk.VERTICAL, command=self.table.yview)
        self.table.configure(yscroll=scroll.set)

        self.table.bind("<ButtonRelease-1>", self.selected_row)
        self.table.bind("<KeyRelease>", self.selected_row)
        
        self.table.pack(anchor=tk.CENTER, expand=1, fill=tk.X)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.req = tk.StringVar()
        self.entry_req = tk.Entry(result_frame, width=15, textvariable=self.req, font=(style.font, style.normal), bg=style.add, fg=style.bol)
        self.bind("<Return>", self.req_update)
        self.entry_req.pack(fill=tk.X, anchor=tk.CENTER, padx=(style.pad * 10, style.pad * 10), pady=(style.pad * 10, style.pad * 10))

    def save_image(self, e):
        f = filedialog.asksaveasfile(mode='wb')
        if f is None:
            return
        with open("image.jpg", "rb") as src:
            f.write(src.read())
        f.close()
        return

    def substr_update(self, *args):
        txt = self.substr.get()
        if len(txt) == 0 or self.flags['substr'].get() == 0:
            if 'substr' in self.req_params.keys():
                self.req_params['substr'] = ''
                self.apply_filters()
                return
            return
        self.req_params['substr'] = f'text LIKE "{txt}"'
        self.apply_filters()
        return

    def date_update(self, *args):
        from_date = self.from_date.get()
        to_date = self.to_date.get()
        if len(from_date) == 0 or len(to_date) == 0 or self.flags['date'].get() == 0:
            if 'date' in self.req_params.keys():
                self.req_params['date'] = ''
                self.apply_filters()
                return
            return
        self.req_params['date'] = f'date > "{from_date}" AND date < "{to_date}"'
        self.apply_filters()
        return

    def vid_update(self, *args):
        txt = self.vid.get()
        if len(txt) == 0 or self.flags['vid'].get() == 0:
            if 'vid' in self.req_params.keys():
                self.req_params['vid'] = ''
                self.apply_filters()
                return
            return
        if '/' in txt:
            txt = txt[txt.rfind("?v=") + 3::]
            txt = txt[:txt.find("&"):]
        self.req_params['vid'] = f'video_id LIKE "{txt}"'
        self.apply_filters()
        return

    def un_update(self, *args):
        txt = self.un.get()
        if len(txt) == 0 or self.flags['user'].get() == 0:
            if 'user' in self.req_params.keys():
                self.req_params['user'] = ''
                self.apply_filters()
                return
            return
        self.req_params['user'] = f'username LIKE "{txt}"'
        self.apply_filters()
        return

    def apply_filters(self):
        keys = list(self.req_params.keys())
        for k in keys:
            if self.req_params[k] == "":
                self.req_params.pop(k)
        if len(self.req_params) == 0:
            req = self.default_req
        else:
            req = self.default_req + " WHERE " + " AND ".join(self.req_params.values())
        data = self.make_request(req)
        self.update_table(parse_request(req), data)
        return

    def req_update(self, e):
        txt = self.req.get()
        if len(txt) == 0:
            txt = self.default_req
        data = self.make_request(txt)
        if isinstance(data, Exception):
            return
        self.update_table(parse_request(txt), data)
        self.entry_req.delete(0, 'end')
        return

    def make_request(self, request):
        try:
            self.cur.execute(request)
        except Exception as e:
            return e
        return self.cur.fetchall()

    def reset_table(self):
        self.entry_un.delete(0, "end")
        self.entry_vid.delete(0, "end")
        self.entry_substr.delete(0, "end")
        for k in self.flags:
            self.flags[k].set(0)
        self.update_table(("video_id", "username", "date", "pfp", "text"),
                          self.make_request("SELECT video_id, username, date, pfp, text FROM messages INNER JOIN users ON messages.user_id = users.id"))

    def update_table(self, cols, data):
        self.columns = cols
        self.table.delete(*self.table.get_children())
        self.table.configure(columns=cols)
        
        for i in range(len(cols)):
            if cols[i] != "pfp" and cols[i] != "preview" and cols[i] != "text":
                self.table.column(f"# {i + 1}", anchor = tk.CENTER, stretch=0)
            self.table.heading(f"# {i + 1}", text=cols[i])

        for row in data:
            self.table.insert("", tk.END, values=row)
        return

    def selected_row(self, event):
        info = self.table.focus()
        data = self.table.item(info)
        row = data['values']
        n = len(self.columns)
        text = ""
        for i in range(n):
            if self.columns[i] == "pfp" or self.columns[i] == "preview":
                # img_data = ImageTk.PhotoImage(Image.open('data_viewer.png').resize((640, 480)))
                url = row[i]
                response = requests.get(url)
                with open("image.jpg", "wb") as f:
                    f.write(response.content)
                img_data = ImageTk.PhotoImage(Image.open('image.jpg'))
                self.img.config(image=img_data)
                self.img.image = img_data
            else:
                text += f"{self.columns[i]}: {row[i]}\n"
        text = divide_str(text)[:-1:]
        self.descr.configure(text=text)
        self.descr.text = text
        return

    def pressed_exit(self, e=None):
        self.destroy()

    def pressed_save(self):
        return

if __name__ == "__main__":
    windll.shcore.SetProcessDpiAwareness(1)
    style = Style()
    window = Window(800, 800)
    window.mainloop()
