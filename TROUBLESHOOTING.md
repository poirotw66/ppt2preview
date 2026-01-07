# 故障排除指南

## 常見問題

### 1. `ModuleNotFoundError: No module named 'backend'`

**問題**: 啟動後端時無法找到 backend 模組

**解決方案**:
```bash
# 確保從專案根目錄運行
cd /Users/cfh00896102/Github/ppt2preview

# 設置 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 使用啟動腳本（推薦）
./start_backend.sh
```

### 2. `google-generativeai package is not installed`

**問題**: Gemini 服務無法初始化，提示套件未安裝

**解決方案**:
```bash
# 激活 conda 環境
source /Users/cfh00896102/miniconda3/etc/profile.d/conda.sh
conda activate p2v

# 安裝套件
pip install google-generativeai

# 或安裝所有依賴
pip install -r backend/requirements.txt

# 驗證安裝
python -c "import google.generativeai; print('✓ Installed')"
```

**注意**: 如果使用 conda 環境，確保使用 `python -m pip install` 而不是直接使用 `pip`，以確保安裝到正確的環境。

### 3. `GEMINI_API_KEY environment variable is not set`

**問題**: Gemini API 金鑰未設置

**解決方案**:
```bash
# 方法 1: 使用 .env 檔案
cp .env.example .env
# 編輯 .env 檔案，填入 GEMINI_API_KEY

# 方法 2: 手動設置
export GEMINI_API_KEY="your-api-key-here"

# 方法 3: 在啟動腳本中自動載入
# start_backend.sh 會自動載入 .env 檔案
```

### 4. 套件安裝在錯誤的 Python 環境

**問題**: 套件安裝了但無法導入

**解決方案**:
```bash
# 確認當前 Python 環境
which python
python --version

# 確認 conda 環境已激活
conda activate p2v

# 使用 python -m pip 確保安裝到正確環境
python -m pip install google-generativeai

# 驗證安裝位置
python -m pip show google-generativeai
```

### 5. 後端日誌顯示正常但實際失敗

**問題**: API 請求返回 200，但實際操作失敗

**解決方案**:
1. 檢查後端終端的完整錯誤訊息
2. 檢查任務狀態 API: `GET /api/v1/status/{task_id}`
3. 查看錯誤訊息欄位
4. 檢查環境變數是否正確設置
5. 運行依賴檢查腳本: `./check_dependencies.sh`

### 6. WebSocket 連接失敗

**問題**: 前端無法連接到 WebSocket

**解決方案**:
1. 確認後端正在運行
2. 檢查 WebSocket URL 配置（應為 `ws://localhost:8000/api/v1/ws/{task_id}`）
3. 檢查瀏覽器控制台的錯誤訊息
4. 確認 CORS 設置正確

### 7. 檔案上傳失敗

**問題**: 無法上傳檔案

**解決方案**:
1. 檢查檔案大小限制
2. 確認檔案格式正確（Markdown 和 PDF）
3. 檢查後端日誌中的錯誤訊息
4. 確認 `uploads/` 和 `temp/` 目錄有寫入權限

## 診斷工具

### 檢查依賴
```bash
./check_dependencies.sh
```

### 驗證後端
```bash
conda activate p2v
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python verify_backend.py
```

### 測試 API
```bash
# 健康檢查
curl http://localhost:8000/health

# 檢查 API 文檔
open http://localhost:8000/docs
```

## 重新安裝依賴

如果遇到依賴問題，可以重新安裝：

```bash
# 激活環境
source /Users/cfh00896102/miniconda3/etc/profile.d/conda.sh
conda activate p2v

# 重新安裝所有依賴
pip install -r backend/requirements.txt --force-reinstall

# 或使用安裝腳本
./install_backend_deps.sh
```

## 環境變數檢查

```bash
# 檢查環境變數
echo $GEMINI_API_KEY
echo $GOOGLE_CLOUD_PROJECT
echo $GOOGLE_APPLICATION_CREDENTIALS

# 如果未設置，載入 .env 檔案
source load_env.sh
```

## 日誌檢查

### 後端日誌
- 查看終端輸出
- 檢查錯誤堆疊追蹤
- 確認任務狀態 API 返回的錯誤訊息

### 前端日誌
- 打開瀏覽器開發者工具（F12）
- 查看 Console 標籤的錯誤訊息
- 查看 Network 標籤的請求/回應

## 常見錯誤訊息

| 錯誤訊息 | 原因 | 解決方案 |
|---------|------|---------|
| `ModuleNotFoundError: No module named 'backend'` | PYTHONPATH 未設置 | 設置 PYTHONPATH 或使用啟動腳本 |
| `google-generativeai package is not installed` | 套件未安裝 | `pip install google-generativeai` |
| `GEMINI_API_KEY environment variable is not set` | API 金鑰未設置 | 設置環境變數或使用 .env 檔案 |
| `Failed to initialize Gemini service` | API 金鑰無效或網路問題 | 檢查 API 金鑰和網路連接 |
| `Port 8000 is already in use` | 端口被占用 | 停止占用端口的進程或更改端口 |

## 獲取幫助

如果問題仍然存在：

1. 運行診斷腳本並保存輸出
2. 檢查後端和前端日誌
3. 確認所有環境變數已正確設置
4. 確認所有依賴已正確安裝
5. 檢查 Python 和 Node.js 版本是否符合要求

