# 環境變數設置指南

## 快速開始

### 1. 複製範例檔案
```bash
cp .env.example .env
```

### 2. 編輯 .env 檔案
使用你喜歡的編輯器打開 `.env` 檔案，填入實際的值：

```bash
nano .env
# 或
vim .env
# 或
code .env
```

### 3. 載入環境變數

#### 方法 1: 使用載入腳本（推薦）
```bash
source load_env.sh
```

#### 方法 2: 手動 export
```bash
export GEMINI_API_KEY="your-api-key-here"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

#### 方法 3: 在啟動服務器時自動載入
`start_server.sh` 腳本會自動載入 `.env` 檔案中的環境變數。

## 必需的環境變數

### GEMINI_API_KEY
用於生成簡報腳本的 Gemini API 金鑰。

**獲取方式：**
1. 訪問 https://ai.google.dev/
2. 登入 Google 帳號
3. 創建 API 金鑰
4. 複製金鑰並填入 `.env` 檔案

**範例：**
```bash
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### GOOGLE_CLOUD_PROJECT
Google Cloud 專案 ID，用於 Google Cloud Text-to-Speech API。

**獲取方式：**
1. 訪問 https://console.cloud.google.com/
2. 選擇或創建專案
3. 複製專案 ID

**範例：**
```bash
GOOGLE_CLOUD_PROJECT=my-project-id-123456
```

### GOOGLE_APPLICATION_CREDENTIALS
Google Cloud 服務帳戶憑證檔案路徑，用於 API 認證。

**獲取方式：**
1. 在 Google Cloud Console 中創建服務帳戶
2. 下載 JSON 憑證檔案
3. 將檔案保存在安全的位置
4. 填入檔案路徑

**範例：**
```bash
GOOGLE_APPLICATION_CREDENTIALS=/Users/username/credentials/google-cloud-key.json
```

## 驗證環境變數

### 檢查環境變數是否設置
```bash
echo $GEMINI_API_KEY
echo $GOOGLE_CLOUD_PROJECT
echo $GOOGLE_APPLICATION_CREDENTIALS
```

### 使用驗證腳本
```bash
conda activate p2v
python verify_backend.py
```

腳本會檢查環境變數是否正確設置。

## 在不同環境中使用

### 開發環境
使用 `.env` 檔案（已加入 `.gitignore`，不會被提交到 Git）。

### 生產環境
建議使用系統環境變數或容器環境變數，而不是 `.env` 檔案。

### Docker 環境
在 `docker-compose.yml` 或 Dockerfile 中設置環境變數：
```yaml
environment:
  - GEMINI_API_KEY=${GEMINI_API_KEY}
  - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
  - GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}
```

## 安全注意事項

1. **永遠不要提交 `.env` 檔案到 Git**
   - `.env` 已加入 `.gitignore`
   - 只提交 `.env.example` 作為範本

2. **保護 API 金鑰**
   - 不要分享 API 金鑰
   - 定期輪換 API 金鑰
   - 使用最小權限原則

3. **保護憑證檔案**
   - 將憑證檔案保存在安全位置
   - 設置適當的檔案權限：`chmod 600 credentials.json`
   - 不要將憑證檔案提交到 Git

4. **使用環境變數而非硬編碼**
   - 不要在代碼中硬編碼 API 金鑰
   - 使用環境變數或配置管理工具

## 故障排除

### 環境變數未生效
1. 確認已使用 `source load_env.sh` 或 `export` 命令
2. 檢查 `.env` 檔案格式是否正確（無空格、正確引號）
3. 重新啟動終端或服務器

### API 金鑰無效
1. 確認金鑰格式正確（無多餘空格）
2. 檢查 API 金鑰是否已啟用
3. 確認 API 服務已啟用（Gemini API、Cloud TTS API）

### 憑證檔案無法讀取
1. 確認檔案路徑正確（使用絕對路徑）
2. 檢查檔案權限：`ls -l $GOOGLE_APPLICATION_CREDENTIALS`
3. 確認檔案格式正確（有效的 JSON）

## 範例 .env 檔案

```bash
# Gemini API Configuration
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=my-project-id-123456
GOOGLE_APPLICATION_CREDENTIALS=/Users/username/credentials/google-cloud-key.json
```

## 相關文檔

- [Gemini API 文檔](https://ai.google.dev/docs)
- [Google Cloud TTS 文檔](https://cloud.google.com/text-to-speech/docs)
- [環境變數最佳實踐](https://12factor.net/config)

