import customtkinter as ctk
import requests
from PIL import Image
import yt_dlp
import threading
from io import BytesIO
import re
from tkinter import messagebox
from tkinter import filedialog
import sys
import os
import traceback

if sys.stdout is None:
    sys.stdout=open(os.devnull,"w")
if sys.stderr is None:
    sys.stderr=open(os.devnull,"w")

def runsafely(func, *args):
    try:
        func(*args)
    except Exception as e:
        logpath=os.path.join(os.path.expanduser("~"), "videodownloader_crash.log")
        with open(logpath,"w") as f:
            f.write(traceback.format_exc())
        app.after(0,lambda:messagebox.showerror("Unexpected Error",f"{e}\n\n Details saved to: \n {logpath}"))

#The code is made by Xiao Yi
def resourcepath(rp):
    bp=getattr(sys,"_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(bp,rp)
#The code is made by Xiao Yi
FFMPEG_PATH=resourcepath("ffmpeg.exe")
#The code is made by xiaoyi
app=ctk.CTk()
w=app.winfo_screenwidth()
h=app.winfo_screenheight()
app.title("Video downloader")
if os.path.exists(resourcepath("favicon.ico")):
    app.iconbitmap(resourcepath("favicon.ico"))
app.geometry(f"{w}x{h}")
sframe=ctk.CTkScrollableFrame(app,width=w,height=h)
sframe.pack(fill="both",expand=True)
app.update()
fw=sframe.winfo_screenwidth()-10
fh=sframe.winfo_screenheight()-10
currentframe=None
#The code is made by Xiao Yi
def clean_description(text):
    if not text:
        return ""
    text=re.sub(r'\n{3,}','\n\n', text.strip())
    return text
#The code is made by Xiao Yi
class vid:
    def __init__(self,url):
        self.url=url
        self.quality=None
        self.format=None
        self.format_var=None
        self.progressbar=None
        self.percentlabel=None
        self.downloaddir=os.path.join(os.path.expanduser("~"),"Downloads")
        os.makedirs(self.downloaddir,exist_ok=True)
        self.titleentry=None
        self.downloadtitle=None

    def getinfo(self):
        try:
            with yt_dlp.YoutubeDL() as ydl:
                info=ydl.extract_info(self.url,download=False)
                title=info["title"]
                duration=info["duration"]
                uploader=info["uploader"]
                description=clean_description(info["description"])
                tnjpg=info["thumbnail"]

            r=requests.get(tnjpg)
            image=Image.open(BytesIO(r.content))

            app.after(0,self.buildui,title,duration,uploader,description,image)
        except  Exception as e:
            errmsg=str(e)
            app.after(0, lambda: messagebox.showinfo("Error",errmsg))

    def choosefolder(self):
        folder=filedialog.askdirectory(initialdir=self.downloaddir)
        if folder:
            self.downloaddir=folder
            self.folderlabel.configure(text=f"Save to: {self.downloaddir}")

    def buildui(self,title,duration,uploader,description,image):
        global currentframe
        if currentframe is not None:
            currentframe.destroy()
        tn=ctk.CTkImage(light_image=image,dark_image=image, size=(320,180))
        frame=ctk.CTkFrame(sframe,fg_color="transparent")
        frame.pack(fill="x",padx=15, pady=15)
        currentframe=frame
        tnlabel=ctk.CTkLabel(frame,text="",image=tn)
        tnlabel.pack()
        tnlabel.image=tn
        titlelabel=ctk.CTkLabel(frame,text=f"Title: {title}",font=("Arial",13))
        titlelabel.pack(anchor="w")
        durationlabel=ctk.CTkLabel(frame,text=f"Duration: {duration} secs",font=("Arial",13))
        durationlabel.pack(anchor="w")
        uploaderlabel=ctk.CTkLabel(frame, text=f"Uploader: {uploader}", font=("Arial",13))
        uploaderlabel.pack(anchor="w")
        descriptionlabel=ctk.CTkLabel(frame, text=f"Description: ", font=("Arial",13),wraplength=max(100,sframe.winfo_width()-30),justify="left")
        descriptionlabel.pack(anchor="w")
        descbox=ctk.CTkTextbox(frame,wrap="word",font=("Arial",13))
        descbox.pack(fill="x",pady=(0,5))
        descbox.insert("1.0",description if description else "(no description)")
        descbox.configure(state="disabled")

        formatlabel=ctk.CTkLabel(frame,text="Format: ", font=("Arial",13))
        formatlabel.pack(anchor="w",pady=(5,0))
        self.format_var=ctk.StringVar(value="best")
        radio_frame=ctk.CTkFrame(frame, fg_color="transparent")
        radio_frame.pack(anchor="w")
        options=[("Best quality","bestvideo+bestaudio/best"),("720p","bestvideo[height<=720]+bestaudio/best[height<=720]"),("Audio only(mp3)","bestaudio")]
        for text, value in options:
            rb=ctk.CTkRadioButton(radio_frame,text=text,variable=self.format_var,value=value)
            rb.pack(side="left",padx=(0,15))

        titlelabel=ctk.CTkLabel(frame,text="Title: ", font=("Arial",13))
        titlelabel.pack(anchor="w",pady=(5,0))
        self.titleentry=ctk.CTkEntry(frame, width=400, placeholder_text="Enter the title of vid here(or leave it empty)...")
        self.titleentry.pack(anchor="w",pady=(5,0))

        def downloadbutton():
            threading.Thread(target=runsafely, args=(self.download,),daemon=True).start()
        downloadbtn=ctk.CTkButton(frame, text="Download",command=downloadbutton)
        downloadbtn.pack(anchor="w",pady=(10,0))
        folderbtn=ctk.CTkButton(frame, text="Choose folder...",command=self.choosefolder)
        folderbtn.pack(anchor="w", pady=(5,0))
        self.folderlabel=ctk.CTkLabel(frame,text=f"Save to: {self.downloaddir}", font=("Arial",11))
        self.folderlabel.pack(anchor="w")
        self.progressbar=ctk.CTkProgressBar(frame,width=400)
        self.progressbar.pack(pady=(10,0),anchor="w")
        self.progressbar.set(0)
        self.percentlabel=ctk.CTkLabel(frame,text="0% downloaded")
        self.percentlabel.pack(anchor="w",pady=(10,0))

    def progresshook(self,d):
        app.after(0,self.downloadprogress,d)

    def downloadprogress(self,d):
        if self.progressbar is None or self.percentlabel is None:
            return
        if d["status"]=="downloading":
            percentstr=d.get("_percent_str","0%")
            percentstr=re.sub(r'\x1b\[[0-9;]*m','',percentstr).strip()
            try:
                value=float(percentstr.replace("%",""))
            except ValueError:
                value=0.0
            self.progressbar.set(value/100)
            self.percentlabel.configure(text=f"{percentstr} downloaded")
        elif d["status"]=="finished":
            self.progressbar.set(1.0)
            self.percentlabel.configure(text="Processing...")

    def download(self):
        self.format= self.format_var.get() if self.format_var else "best"
        self.downloadtitle=self.titleentry.get()
        if self.downloadtitle=="":
            titledownload="%(title)s.%(ext)s"
        else:
            titledownload=f"{self.downloadtitle}.%(ext)s"

        options={"format":self.format,
            "progress_hooks":[self.progresshook],
            "outtmpl":os.path.join(self.downloaddir,titledownload),
            "noplaylist":True,
            "color":"no_color",
            "quiet":True,
            "no_warnings":True,
            "overwrites":True,
            "merge_output_format":"mp4"}
        if os.path.exists(FFMPEG_PATH):
            options["ffmpeg_location"]=FFMPEG_PATH
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info=ydl.extract_info(self.url, download=True)
                filename=ydl.prepare_filename(info)
                if os.path.exists(filename):
                    app.after(0, lambda: messagebox.showinfo("Success!", f"Download complete!!! \nSaved to: {filename}"))
                else:
                    app.after(0, lambda: messagebox.showinfo("Warning", "Download finished but the output file isn't found -- check the format/ffmpeg setup"))
        except Exception as e:
            app.after(0, lambda: messagebox.showinfo("Error",f"Couldn't download video: {e}"))

#The code is made by Xiao Yi
lb=ctk.CTkLabel(sframe, text="Video downloader",font=("Arial",40))
lb.pack(pady=20)

def button():
    url=entrybox.get()
    video=vid(url)
    threading.Thread(target=runsafely, args=(video.getinfo,),daemon=True).start()
    entrybox.delete(0,"end")

entrybox=ctk.CTkEntry(sframe, placeholder_text="Enter URL",width=350)
entrybox.pack(pady=10)
search=ctk.CTkButton(sframe, text="Search", width=70,height=30,command=button)
search.pack()

def onenter(event):
    button()
    return "break"
entrybox.bind("<Return>", onenter)

app.mainloop()
