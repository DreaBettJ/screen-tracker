#!/usr/bin/env python3
"""
屏幕活动追踪器
每隔30秒截图 -> AI识别活动 -> 记录时间分配
"""

import os
import time
import json
import base64
from datetime import datetime
from pathlib import Path
import mss
import mss.tools

# DeepSeek API
DEEPSEEK_API_KEY = "sk-..."
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# 配置
SCREENSHOT_INTERVAL = 30  # 秒
SCREENSHOT_DIR = Path.home() / "screen-tracker" / "screenshots"
DATA_DIR = Path.home() / "screen-tracker" / "data"
DATA_FILE = DATA_DIR / "activity_log.json"

# 确保目录存在
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


def take_screenshot():
    """截取屏幕截图"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = SCREENSHOT_DIR / f"screenshot_{timestamp}.png"
    
    with mss.mss() as sct:
        sct.shot(output=str(filename))
    
    return filename, timestamp


def encode_image(image_path):
    """将图片转为 base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')


def analyze_activity(image_path):
    """使用 DeepSeek AI 分析屏幕活动"""
    base64_image = encode_image(image_path)
    
    prompt = """分析这张屏幕截图，判断用户当前在做什么活动。

请将活动分类为以下类别之一：
- coding (写代码/编程)
- browsing (浏览网页)
- watching_video (看视频)
- reading (阅读文档/文章)
- chatting (聊天/社交)
- gaming (玩游戏)
- working (其他工作/办公)
- idle (空闲/无操作 - 屏幕锁定或长时间无活动)
- unknown (无法判断)

只返回一个词，例如：coding

注意：如果屏幕看起来是锁定的、黑的、或者没有任何操作迹象，返回 idle"""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 50
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        import requests
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        activity = result["choices"][0]["message"]["content"].strip().lower()
        
        # 清理结果
        if "coding" in activity:
            return "coding"
        elif "browsing" in activity:
            return "browsing"
        elif "watching_video" in activity:
            return "watching_video"
        elif "reading" in activity:
            return "reading"
        elif "chatting" in activity:
            return "chatting"
        elif "gaming" in activity:
            return "gaming"
        elif "working" in activity:
            return "working"
        elif "idle" in activity:
            return "idle"
        else:
            return "unknown"
            
    except Exception as e:
        print(f"API 调用失败: {e}")
        return "unknown"


def load_existing_data():
    """加载已有数据"""
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_data(data):
    """保存数据"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def log_activity(timestamp, activity, screenshot_path):
    """记录活动"""
    data = load_existing_data()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if today not in data:
        data[today] = []
    
    data[today].append({
        "timestamp": timestamp,
        "activity": activity,
        "screenshot": str(screenshot_path)
    })
    
    save_data(data)
    print(f"[{timestamp}] 活动: {activity}")


def generate_daily_report():
    """生成每日报告"""
    data = load_existing_data()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if today not in data or not data[today]:
        print("今天还没有数据")
        return
    
    activities = {}
    for entry in data[today]:
        act = entry["activity"]
        if act not in activities:
            activities[act] = 0
        activities[act] += 1
    
    print(f"\n=== {today} 活动统计 ===")
    total = sum(activities.values())
    sorted_activities = sorted(activities.items(), key=lambda x: x[1], reverse=True)
    
    for act, count in sorted_activities:
        percentage = (count / total) * 100
        print(f"{act}: {count} 次 ({percentage:.1f}%)")
    
    print(f"总计记录: {total} 条")


def main():
    """主循环"""
    print("🖥️ 屏幕活动追踪器启动")
    print(f"📁 截图目录: {SCREENSHOT_DIR}")
    print(f"📁 数据目录: {DATA_DIR}")
    print(f"⏱️ 截图间隔: {SCREENSHOT_INTERVAL} 秒")
    print("按 Ctrl+C 停止\n")
    
    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{timestamp}] 截取屏幕...")
            
            # 截图
            screenshot_path, _ = take_screenshot()
            print(f"   截图已保存: {screenshot_path}")
            
            # AI 分析
            print("   AI 分析中...")
            activity = analyze_activity(screenshot_path)
            print(f"   识别结果: {activity}")
            
            # 跳过 idle
            if activity == "idle":
                print("   ⏭️ 空闲状态，跳过记录")
            else:
                # 记录
                log_activity(timestamp, activity, screenshot_path)
            
            # 等待下一次截图
            time.sleep(SCREENSHOT_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n停止追踪器...")
        generate_daily_report()


if __name__ == "__main__":
    main()
