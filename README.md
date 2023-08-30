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

-   `>join`：使機器人進入當前語音頻道
-   `>leave`：使機器人離開任何語音頻道

### 清單操作

-   `>play`：將 YouTube 音樂或清單加入機器人音樂清單
-   `>show`：顯示當前音樂
-   `>list`：顯示音樂清單，可選擇顯示數量
-   `>clear`：清空音樂清單
-   `>shuffle`：打亂音樂清單
-   `>loop`：重複一首音樂或整個清單
-   `>unloop`：解除任何重複狀態

### 音樂操作

-   `>pause`：暫停播放
-   `>resume`：繼續播放
-   `>skip`：跳過當前音樂
