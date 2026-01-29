# Camera Control GUI (V4L2-GUI) - 開發計畫

## 專案目標
開發一個基於 Ubuntu 的 GUI 工具，透過包裝 `v4l2-ctl` 指令來調整攝影機參數（亮度、對比、曝光等）。

## 技術棧
- **Language:** Python 3
- **GUI Framework:** PyQt6
- **Tooling:** `v4l2-ctl` (來自 `v4l2-utils`)
- **Process Communication:** `subprocess`

## 安裝需求

### 1. 系統工具
確保你的 Ubuntu 安裝了 `v4l2-utils` 與 `ffmpeg`（預覽功能需要）：
```bash
sudo apt update
sudo apt install v4l2-utils ffmpeg python3
```

### 2. Python 依賴
建議在虛擬環境中安裝：
```bash
# 安裝 PyQt6
pip install -r requirements.txt
```

## 如何使用
執行主程式：
```bash
python3 main.py
```

## 功能特點
- 自動偵測攝影機裝置。
- 動態生成調整面板（Slider, Checkbox, Menu）。
- 支援數值同步與連動更新（例如自動曝光開關後鎖定手動數值）。
- 即時畫面預覽 (Live Preview)。