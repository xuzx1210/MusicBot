# MusicBot

## 安裝方式

1. 新增`.env`檔案，內容為`TOKEN=你的機器人token`
2. 新增`music`資料夾，音樂暫存檔將儲存於此
3. 安裝`ffmpeg`，ubuntu 系統可直接執行`sudo apt install ffmpeg`
4. 創建虛擬 python 環境：`python3 -m venv .venv`
5. 進入虛擬環境：`source .venv/bin/activate`
6. 安裝依賴套件：`pip install -r requirements.txt`

## 啟動方式

1. 進入虛擬環境：`source .venv/bin/activate`
2. 啟動機器人：`python server.py`

## 使用方式

### 語音頻道

1. 進入 Discord 語音頻道
2. `>join`：使機器人進入當前語音頻道
3. `>leave`：使機器人離開任何語音頻道

### 清單操作

1. `>play`：將 YouTube 音樂或清單加入機器人音樂清單
2. `>list`：顯示音樂清單
3. `>clear`：清空音樂清單
4. `>shuffle`：打亂音樂清單

### 音樂操作

1. `>pause`：暫停播放
2. `>resume`：繼續播放
3. `>skip`：跳過當前音樂
