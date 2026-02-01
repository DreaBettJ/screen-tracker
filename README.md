# 屏幕活动追踪器 🖥️

自动截屏 → AI 识别活动 → 统计时间分配

## 功能

- **GUI 界面** - 简洁直观
- **开始/暂停/停止** - 完全控制
- **实时显示** - 当前活动状态
- **每日统计** - 时间分配一目了然
- **API 配置** - DeepSeek Key 可配置
- **跳过空闲** - 自动忽略无操作状态

## 安装

```bash
cd screen-tracker
pip install -r requirements.txt
```

## 运行

```bash
# GUI 版本（推荐）
python screen-tracker-gui.py

# 命令行版本
python screen-tracker.py
```

## 配置

首次运行会提示配置 DeepSeek API Key，或点击 "⚙ API Key 配置" 按钮设置。

## 打包成 Windows 应用

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包 GUI 版本（单文件，无控制台窗口）
pyinstaller --onefile --windowed screen-tracker-gui.py

# 打包后的 exe 在 dist/ 目录下
```

## 输出

- **截图**: `~/screen-tracker/screenshots/`
- **数据**: `~/screen-tracker/data/activity_log.json`
- **配置**: `screen-tracker/config.json`

## 数据示例

```json
{
  "2026-02-01": [
    {
      "timestamp": "2026-02-01 15:30:00",
      "activity": "coding"
    }
  ]
}
```

## 快捷键

- **开始** - 点击按钮
- **暂停/继续** - 点击按钮
- **停止** - 点击按钮
