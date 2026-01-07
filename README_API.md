# PPT2Preview API 測試指南

## 啟動服務器

### 方法 1: 使用啟動腳本
```bash
./start_server.sh
```

### 方法 2: 手動啟動
```bash
source /Users/cfh00896102/miniconda3/etc/profile.d/conda.sh
conda activate p2v
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

服務器啟動後，可以訪問：
- API 文檔: http://localhost:8000/docs
- 健康檢查: http://localhost:8000/health
- API 根路徑: http://localhost:8000/

## 運行測試

```bash
source /Users/cfh00896102/miniconda3/etc/profile.d/conda.sh
conda activate p2v
python test_api.py
```

## API 端點

### 1. 健康檢查
```bash
curl http://localhost:8000/health
```

### 2. 上傳檔案
```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "abstract_file=@three_pig_page_abstract.md" \
  -F "pdf_file=@three_pig_pdf.pdf"
```

### 3. 查詢任務狀態
```bash
curl "http://localhost:8000/api/v1/status/{task_id}"
```

### 4. 生成腳本
```bash
curl -X POST "http://localhost:8000/api/v1/generate-script" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "{task_id}",
    "length_mode": "SHORT"
  }'
```

### 5. 獲取腳本
```bash
curl "http://localhost:8000/api/v1/script/{task_id}"
```

### 6. 更新腳本
```bash
curl -X PUT "http://localhost:8000/api/v1/script/{task_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "script_content": "更新後的腳本內容..."
  }'
```

### 7. 生成影片
```bash
curl -X POST "http://localhost:8000/api/v1/generate-video" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "{task_id}",
    "video_params": {
      "fps": 5,
      "resolution_width": 1920,
      "resolution_height": 1080,
      "bitrate": "2000k",
      "preset": "ultrafast"
    }
  }'
```

### 8. 下載影片
```bash
curl "http://localhost:8000/api/v1/download/{task_id}" \
  -o presentation.mp4
```

### 9. WebSocket 連接（即時進度）
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/{task_id}');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress:', data);
};
```

## 環境變數

確保設置以下環境變數：

```bash
export GEMINI_API_KEY="your-gemini-api-key"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
```

## 故障排除

### 服務器無法啟動
1. 檢查是否在正確的 conda 環境中（p2v）
2. 確認所有依賴已安裝：`pip install -r backend/requirements.txt`
3. 檢查端口 8000 是否被占用：`lsof -i :8000`

### API 請求失敗
1. 確認服務器正在運行
2. 檢查任務 ID 是否正確
3. 查看服務器日誌以獲取錯誤信息

### 腳本生成失敗
1. 確認 GEMINI_API_KEY 已設置
2. 檢查上傳的檔案是否正確
3. 查看任務狀態以獲取錯誤信息

