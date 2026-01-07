# 快速設置 Google Cloud 認證

## 最簡單的方法（推薦）

### 步驟 1: 安裝 gcloud CLI（如果還沒有）
```bash
# macOS
brew install google-cloud-sdk

# 或訪問：https://cloud.google.com/sdk/docs/install
```

### 步驟 2: 登入並設置認證
```bash
gcloud auth application-default login
```

這會打開瀏覽器，讓您登入 Google 帳號並授權。

### 步驟 3: 設置專案
```bash
gcloud config set project itr-aimasteryhub-lab
```

### 步驟 4: 更新 .env 文件
編輯 `.env` 文件，**註釋掉或刪除** `GOOGLE_APPLICATION_CREDENTIALS` 這一行：

```bash
# Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=itr-aimasteryhub-lab
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/google-cloud-credentials.json  # 註釋掉這行
```

### 步驟 5: 重新啟動後端
```bash
./start_backend.sh
```

## 驗證設置

運行以下命令測試認證是否正確：
```bash
python3 -c "from google.cloud import texttospeech; client = texttospeech.TextToSpeechClient(); print('✓ 認證成功！')"
```

## 如果遇到問題

1. **確認 gcloud CLI 已安裝**：
   ```bash
   gcloud --version
   ```

2. **確認已登入**：
   ```bash
   gcloud auth list
   ```

3. **確認專案設置正確**：
   ```bash
   gcloud config get-value project
   ```

4. **重新設置認證**：
   ```bash
   gcloud auth application-default login
   ```

## 詳細說明

更多詳細說明請參考：`GOOGLE_CLOUD_AUTH.md`
