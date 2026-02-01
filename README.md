# 屏幕活动追踪器 🖥️

自动截屏 → AI 识别活动 → 统计时间分配

## 功能

- 每隔 30 秒截取屏幕截图
- 使用 DeepSeek AI 分析当前活动
- 自动识别：写代码、浏览网页、看视频、阅读、聊天、游戏、工作、空闲
- 跳过空闲/无操作状态
- 每日活动统计报告

## 安装

```bash
cd screen-tracker
pip install -r requirements.txt
```

## 配置

编辑 `screen-tracker.py`，修改 DeepSeek API Key：

```python
DEEPSEEK_API_KEY = "your-api-key-here"
```

## 运行

```bash
python screen-tracker.py
```

## 输出

- **截图**: `~/screen-tracker/screenshots/`
- **数据**: `~/screen-tracker/data/activity_log.json`
- **格式**: JSON，按日期组织

## 数据示例

```json
{
  "2026-02-01": [
    {
      "timestamp": "2026-02-01 15:30:00",
      "activity": "coding",
      "screenshot": "/home/user/screen-tracker/screenshots/screenshot_20260201_153000.png"
    }
  ]
}
```

## 停止

按 `Ctrl+C` 停止，会自动生成当日统计报告。

## 自定义

- 修改截图间隔：编辑 `SCREENSHOT_INTERVAL = 30`
- 修改截图目录：编辑 `SCREENSHOT_DIR`
- 添加新的活动类型：修改 `analyze_activity()` 函数中的分类
