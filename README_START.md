# PPT2Preview 啟動指南

## 快速啟動

### 方法 1: 使用啟動腳本（推薦）

#### 啟動後端
```bash
./start_backend.sh
```
或
```bash
./start_server.sh
```

#### 啟動前端
```bash
./start_frontend.sh
```

### 方法 2: 手動啟動

#### 後端啟動步驟

1. **激活 conda 環境**
```bash
source /Users/cfh00896102/miniconda3/etc/profile.d/conda.sh
conda activate p2v
```

2. **設置環境變數（可選）**
```bash
# 如果使用 .env 檔案
source load_env.sh

# 或手動設置
export GEMINI_API_KEY="your-api-key"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

3. **設置 PYTHONPATH**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

4. **啟動服務器**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 前端啟動步驟

1. **進入前端目錄**
```bash
cd frontend
```

2. **安裝依賴（首次運行）**
```bash
npm install
```

3. **啟動開發服務器**
```bash
npm run dev
```

## 訪問地址

- **後端 API**: http://localhost:8000
- **API 文檔**: http://localhost:8000/docs
- **前端應用**: http://localhost:3000

## 故障排除

### 後端啟動錯誤：`ModuleNotFoundError: No module named 'backend'`

**解決方案**：
1. 確保從專案根目錄運行命令（不是從 `backend` 目錄）
2. 設置 `PYTHONPATH`：
   ```bash
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```
3. 使用提供的啟動腳本 `start_backend.sh`

### 前端啟動錯誤：端口被占用

**解決方案**：
1. 修改 `vite.config.ts` 中的端口號
2. 或停止占用端口的進程：
   ```bash
   lsof -ti:3000 | xargs kill -9
   ```

### 後端啟動錯誤：端口 8000 被占用

**解決方案**：
```bash
lsof -ti:8000 | xargs kill -9
```

### 環境變數未生效

**解決方案**：
1. 確認 `.env` 檔案存在於專案根目錄
2. 檢查 `.env` 檔案格式是否正確
3. 使用 `source load_env.sh` 載入環境變數
4. 或手動使用 `export` 命令

## 開發模式

### 後端自動重載
使用 `--reload` 參數，後端會在代碼變更時自動重啟。

### 前端熱重載
Vite 開發服務器支援熱模組替換（HMR），代碼變更會自動更新瀏覽器。

## 生產模式

### 後端
```bash
# 構建（如果需要）
# 使用生產級 WSGI 服務器，如 gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 前端
```bash
cd frontend
npm run build
# 構建產物在 dist/ 目錄
# 使用 nginx 或其他靜態文件服務器提供服務
```

## 同時運行前後端

在兩個終端視窗中分別運行：

**終端 1（後端）**：
```bash
./start_backend.sh
```

**終端 2（前端）**：
```bash
./start_frontend.sh
```

## 驗證安裝

### 驗證後端
```bash
curl http://localhost:8000/health
```

應該返回：
```json
{"status":"healthy"}
```

### 驗證前端
打開瀏覽器訪問 http://localhost:3000，應該看到應用程式界面。

