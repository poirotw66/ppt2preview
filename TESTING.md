# PPT2Preview 後端 API 測試報告

## ✅ 驗證結果

### 後端結構驗證
所有後端模組已成功驗證：
- ✓ Config module
- ✓ Task manager
- ✓ API models
- ✓ File service
- ✓ Gemini service
- ✓ Script generator
- ✓ Video generator
- ✓ Video utils
- ✓ API routes
- ✓ Main app

### 配置檢查
- ✓ 所有目錄已創建（uploads, output）
- ✓ API 前綴配置正確：`/api/v1`
- ⚠️  GEMINI_API_KEY 未設置（需要設置才能生成腳本）

### FastAPI 應用
- ✓ 應用創建成功
- ✓ 14 個路由已註冊
- ✓ API 文檔可用於 `/docs`

## 🚀 啟動服務器

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

服務器啟動後訪問：
- API 文檔: http://localhost:8000/docs
- 健康檢查: http://localhost:8000/health

## 📋 API 端點列表

### 基礎端點
1. `GET /` - 根路徑
2. `GET /health` - 健康檢查
3. `GET /docs` - Swagger API 文檔

### 任務管理
4. `POST /api/v1/upload` - 上傳檔案（abstract.md 和 PDF）
5. `GET /api/v1/status/{task_id}` - 查詢任務狀態
6. `GET /api/v1/script/{task_id}` - 獲取生成的腳本
7. `PUT /api/v1/script/{task_id}` - 更新腳本
8. `POST /api/v1/generate-script` - 生成腳本
9. `POST /api/v1/generate-video` - 生成影片
10. `GET /api/v1/download/{task_id}` - 下載影片

### 即時通訊
11. `WS /api/v1/ws/{task_id}` - WebSocket 即時進度更新

## 🧪 運行測試

### 驗證後端代碼
```bash
conda activate p2v
python verify_backend.py
```

### 測試 API（需要服務器運行）
```bash
conda activate p2v
python test_api.py
```

## 📝 測試流程

### 1. 上傳檔案
```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "abstract_file=@three_pig_page_abstract.md" \
  -F "pdf_file=@three_pig_pdf.pdf"
```

回應：
```json
{
  "task_id": "uuid-here",
  "status": "uploading",
  "message": "Files uploaded successfully"
}
```

### 2. 生成腳本
```bash
curl -X POST "http://localhost:8000/api/v1/generate-script" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "your-task-id",
    "length_mode": "SHORT"
  }'
```

### 3. 查詢狀態
```bash
curl "http://localhost:8000/api/v1/status/your-task-id"
```

### 4. 獲取腳本
```bash
curl "http://localhost:8000/api/v1/script/your-task-id"
```

### 5. 生成影片
```bash
curl -X POST "http://localhost:8000/api/v1/generate-video" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "your-task-id",
    "video_params": {
      "fps": 5,
      "resolution_width": 1920,
      "resolution_height": 1080
    }
  }'
```

### 6. 下載影片
```bash
curl "http://localhost:8000/api/v1/download/your-task-id" \
  -o presentation.mp4
```

## 🔧 環境設置

### 必需的環境變數
```bash
export GEMINI_API_KEY="your-gemini-api-key"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"
```

### 安裝依賴
```bash
conda activate p2v
pip install -r backend/requirements.txt
```

## ⚠️ 注意事項

1. **GEMINI_API_KEY**: 必須設置才能生成腳本
2. **Google Cloud 憑證**: 必須設置才能生成語音和影片
3. **服務器端口**: 默認使用 8000，確保端口未被占用
4. **檔案路徑**: 確保測試檔案（`three_pig_page_abstract.md` 和 `three_pig_pdf.pdf`）存在

## 🐛 故障排除

### 服務器無法啟動
1. 確認 conda 環境已激活：`conda activate p2v`
2. 檢查依賴是否安裝：`pip list | grep fastapi`
3. 檢查端口是否被占用：`lsof -i :8000`

### API 請求失敗
1. 確認服務器正在運行
2. 檢查任務 ID 是否正確
3. 查看服務器終端日誌

### 腳本生成失敗
1. 確認 GEMINI_API_KEY 已設置
2. 檢查上傳的檔案格式是否正確
3. 查看任務狀態獲取詳細錯誤信息

## 📊 測試狀態

- ✅ 後端代碼結構驗證通過
- ✅ 所有模組導入成功
- ✅ FastAPI 應用創建成功
- ✅ 所有 API 路由已註冊
- ⏳ 需要啟動服務器進行端到端測試
- ⏳ 需要設置 GEMINI_API_KEY 進行完整功能測試

