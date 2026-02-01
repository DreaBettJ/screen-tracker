#!/usr/bin/env python3
"""
屏幕活动追踪器 - GUI 版本
支持：开始/暂停/停止、API Key 配置、实时状态显示
"""

import os
import sys
import time
import json
import base64
import threading
from datetime import datetime
from pathlib import Path
from tkinter import *
from tkinter import messagebox, filedialog
import mss
import requests

# ============== 配置 ==============
CONFIG_FILE = Path(__file__).parent / "config.json"
DATA_DIR = Path.home() / "screen-tracker" / "data"
DATA_FILE = DATA_DIR / "activity_log.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_config():
    """加载配置"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"api_key": "", "interval": 30}


def save_config(config):
    """保存配置"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ============== 核心功能 ==============
class ScreenTracker:
    def __init__(self):
        self.running = False
        self.paused = False
        self.current_activity = None
    
    def take_screenshot(self):
        """截取屏幕"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = Path.home() / "screen-tracker" / "screenshots" / f"screenshot_{timestamp}.png"
        filename.parent.mkdir(parents=True, exist_ok=True)
        
        with mss.mss() as sct:
            sct.shot(output=str(filename))
        return filename
    
    def analyze_activity(self, image_path, api_key):
        """AI 分析活动"""
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
        
        prompt = """分析这张屏幕截图，判断用户当前在做什么活动。

活动类别：
- coding (写代码)
- browsing (浏览网页)
- watching_video (看视频)
- reading (阅读)
- chatting (聊天)
- gaming (游戏)
- working (其他工作)
- idle (空闲/无操作)
- unknown (无法判断)

只返回一个词。"""

        payload = {
            "model": "deepseek-chat",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }],
            "max_tokens": 50
        }
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        try:
            response = requests.post("https://api.deepseek.com/chat/completions", 
                                   headers=headers, json=payload)
            result = response.json()
            activity = result["choices"][0]["message"]["content"].strip().lower()
            
            # 清理结果
            for keyword in ["coding", "browsing", "watching_video", "reading", 
                          "chatting", "gaming", "working", "idle"]:
                if keyword in activity:
                    return keyword
            return "unknown"
        except Exception as e:
            print(f"API 错误: {e}")
            return "unknown"
    
    def log_activity(self, activity):
        """记录活动"""
        if activity == "idle":
            return
        
        data = load_existing_data()
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in data:
            data[today] = []
        
        data[today].append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "activity": activity
        })
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def run(self, config, callback):
        """主循环"""
        interval = config.get("interval", 30)
        api_key = config.get("api_key", "")
        
        while self.running:
            if not self.paused:
                try:
                    screenshot = self.take_screenshot()
                    activity = self.analyze_activity(screenshot, api_key)
                    self.current_activity = activity
                    
                    if activity != "idle":
                        self.log_activity(activity)
                    
                    callback(activity)
                    
                except Exception as e:
                    callback(f"错误: {e}")
            
            time.sleep(interval)


def load_existing_data():
    """加载数据"""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


# ============== GUI ==============
class App:
    def __init__(self):
        self.root = Tk()
        self.tracker = ScreenTracker()
        self.thread = None
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """设置 UI"""
        self.root.title("屏幕活动追踪器 🖥️")
        self.root.geometry("400x500")
        self.root.resizable(False, False)
        
        # 标题
        Label(self.root, text="屏幕活动追踪器", font=("Microsoft YaHei", 18, "bold")).pack(pady=20)
        
        # 状态显示
        self.status_label = Label(self.root, text="就绪", font=("Microsoft YaHei", 14))
        self.status_label.pack(pady=10)
        
        self.activity_label = Label(self.root, text="当前活动: -", font=("Microsoft YaHei", 12))
        self.activity_label.pack(pady=5)
        
        # 按钮区域
        btn_frame = Frame(self.root)
        btn_frame.pack(pady=20)
        
        self.start_btn = Button(btn_frame, text="▶ 开始", font=("Microsoft YaHei", 12), 
                                width=10, command=self.start)
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.pause_btn = Button(btn_frame, text="⏸ 暂停", font=("Microsoft YaHei", 12), 
                               width=10, command=self.pause, state=DISABLED)
        self.pause_btn.grid(row=0, column=1, padx=5)
        
        self.stop_btn = Button(btn_frame, text="⏹ 停止", font=("Microsoft YaHei", 12), 
                              width=10, command=self.stop, state=DISABLED)
        self.stop_btn.grid(row=0, column=2, padx=5)
        
        # 统计区域
        stats_frame = LabelFrame(self.root, text="今日统计", font=("Microsoft YaHei", 11))
        stats_frame.pack(pady=20, padx=20, fill=X)
        
        self.stats_text = Text(stats_frame, height=8, width=45, font=("Microsoft YaHei", 9))
        self.stats_text.pack(pady=10, padx=10)
        
        # 配置按钮
        config_btn = Button(self.root, text="⚙ API Key 配置", font=("Microsoft YaHei", 10),
                           command=self.show_config)
        config_btn.pack(pady=10)
        
        # 退出提示
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def load_settings(self):
        """加载设置"""
        self.api_key_entry = None
    
    def show_config(self):
        """显示配置对话框"""
        config = load_config()
        
        top = Toplevel()
        top.title("配置")
        top.geometry("400x250")
        top.transient(self.root)
        top.grab_set()
        
        Label(top, text="DeepSeek API Key", font=("Microsoft YaHei", 12)).pack(pady=10)
        
        api_key_var = StringVar(value=config.get("api_key", ""))
        api_key_entry = Entry(top, textvariable=api_key_var, width=50, show="*")
        api_key_entry.pack(pady=5, padx=20)
        
        Label(top, text="截图间隔（秒）", font=("Microsoft YaHei", 12)).pack(pady=10)
        
        interval_var = StringVar(value=str(config.get("interval", 30)))
        interval_entry = Entry(top, textvariable=interval_var, width=10)
        interval_entry.pack()
        
        def save():
            config["api_key"] = api_key_var.get()
            try:
                config["interval"] = int(interval_var.get())
            except:
                config["interval"] = 30
            save_config(config)
            top.destroy()
            messagebox.showinfo("成功", "配置已保存！")
        
        Button(top, text="保存", font=("Microsoft YaHei", 11), command=save).pack(pady=20)
    
    def update_stats(self):
        """更新统计"""
        data = load_existing_data()
        today = datetime.now().strftime("%Y-%m-%d")
        
        if today not in data or not data[today]:
            self.stats_text.delete(1.0, END)
            self.stats_text.insert(END, "今天还没有记录")
            return
        
        activities = {}
        for entry in data[today]:
            act = entry["activity"]
            activities[act] = activities.get(act, 0) + 1
        
        total = sum(activities.values())
        sorted_acts = sorted(activities.items(), key=lambda x: x[1], reverse=True)
        
        text = f"{today} 活动统计\n"
        text += f"总计: {total} 条记录\n\n"
        
        for act, count in sorted_acts:
            pct = (count / total) * 100
            text += f"{act}: {count} 次 ({pct:.1f}%)\n"
        
        self.stats_text.delete(1.0, END)
        self.stats_text.insert(END, text)
    
    def start(self):
        """开始"""
        config = load_config()
        if not config.get("api_key"):
            messagebox.showwarning("提示", "请先配置 DeepSeek API Key！")
            self.show_config()
            return
        
        self.tracker.running = True
        self.tracker.paused = False
        
        self.start_btn.config(state=DISABLED)
        self.pause_btn.config(state=NORMAL)
        self.stop_btn.config(state=NORMAL)
        self.status_label.config(text="运行中...", fg="green")
        
        self.thread = threading.Thread(target=self.tracker.run, args=(config, self.on_activity))
        self.thread.daemon = True
        self.thread.start()
        
        self.update_stats()
    
    def pause(self):
        """暂停"""
        if self.tracker.paused:
            self.tracker.paused = False
            self.pause_btn.config(text="⏸ 暂停")
            self.status_label.config(text="运行中...", fg="green")
        else:
            self.tracker.paused = True
            self.pause_btn.config(text="▶ 继续")
            self.status_label.config(text="已暂停", fg="orange")
    
    def stop(self):
        """停止"""
        self.tracker.running = False
        self.start_btn.config(state=NORMAL)
        self.pause_btn.config(state=DISABLED)
        self.stop_btn.config(state=DISABLED)
        self.status_label.config(text="已停止", fg="red")
        self.activity_label.config(text="当前活动: -")
        self.update_stats()
    
    def on_activity(self, activity):
        """活动更新回调"""
        self.root.after(0, lambda: self.activity_label.config(text=f"当前活动: {activity}"))
        self.root.after(0, self.update_stats)
    
    def on_close(self):
        """关闭"""
        if self.tracker.running:
            if messagebox.askyesno("确认", "追踪器正在运行，确定要退出吗？"):
                self.tracker.running = False
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    app = App()
    app.root.mainloop()


if __name__ == "__main__":
    main()
