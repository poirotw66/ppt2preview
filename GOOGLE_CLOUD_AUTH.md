# Google Cloud 認證設置指南

## 方法 1: 使用 gcloud CLI（推薦，最簡單）

### 步驟 1: 安裝 gcloud CLI
如果還沒有安裝，請訪問：https://cloud.google.com/sdk/docs/install

### 步驟 2: 登入並設置應用程序默認憑證
```bash
gcloud auth application-default login
```

這會：
- 打開瀏覽器讓您登入 Google 帳號
- 自動設置應用程序默認憑證
- 不需要下載 JSON 文件

### 步驟 3: 設置專案 ID
```bash
gcloud config set project itr-aimasteryhub-lab
```

### 步驟 4: 更新 .env 文件
**重要：移除或註釋掉 `GOOGLE_APPLICATION_CREDENTIALS` 這一行**

編輯 `.env` 文件：
```bash
# Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=itr-aimasteryhub-lab
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/google-cloud-credentials.json  # 註釋掉或刪除這行
```

## 方法 2: 使用服務帳戶 JSON 文件

### 步驟 1: 創建服務帳戶
1. 訪問 https://console.cloud.google.com/iam-admin/serviceaccounts
2. 選擇專案：`itr-aimasteryhub-lab`
3. 點擊「建立服務帳戶」
4. 填寫服務帳戶名稱和說明
5. 點擊「建立並繼續」

### 步驟 2: 授予權限
1. 在「授予此服務帳戶對專案的存取權」中，選擇角色：
   - `Cloud Text-to-Speech API User`
2. 點擊「繼續」→「完成」

### 步驟 3: 建立並下載金鑰
1. 在服務帳戶列表中，點擊剛建立的服務帳戶
2. 切換到「金鑰」標籤
3. 點擊「新增金鑰」→「建立新金鑰」
4. 選擇「JSON」格式
5. 點擊「建立」，JSON 文件會自動下載

### 步驟 4: 保存憑證文件
將下載的 JSON 文件保存到安全的位置，例如：
```bash
mkdir -p ~/.config/google-cloud
mv ~/Downloads/your-project-xxxxx-xxxxx.json ~/.config/google-cloud/credentials.json
```

### 步驟 5: 更新 .env 文件
```bash
# Gemini API Configuration
GEMINI_API_KEY=your-gemini-api-key-here

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=itr-aimasteryhub-lab
GOOGLE_APPLICATION_CREDENTIALS=/Users/cfh00896102/.config/google-cloud/credentials.json
```

**注意：請將路徑替換為您實際保存 JSON 文件的路徑**

### 步驟 6: 設置文件權限（安全）
```bash
chmod 600 ~/.config/google-cloud/credentials.json
```

## 驗證設置

### 檢查認證是否正確
```bash
# 如果使用方法 1 (gcloud auth)
gcloud auth application-default print-access-token

# 如果使用方法 2 (JSON 文件)
python3 -c "from google.cloud import texttospeech; client = texttospeech.TextToSpeechClient(); print('✓ 認證成功')"
```

## 故障排除

### 錯誤：File /path/to/your/google-cloud-credentials.json was not found
**解決方案：**
1. 從 `.env` 文件中移除或註釋掉 `GOOGLE_APPLICATION_CREDENTIALS` 這一行
2. 使用 `gcloud auth application-default login` 設置認證
3. 重新啟動後端服務器

### 錯誤：DefaultCredentialsError
**解決方案：**
1. 確認已執行 `gcloud auth application-default login`
2. 或確認 `GOOGLE_APPLICATION_CREDENTIALS` 指向有效的 JSON 文件
3. 確認 JSON 文件格式正確

### 錯誤：Permission denied
**解決方案：**
1. 確認服務帳戶有 `Cloud Text-to-Speech API User` 權限
2. 確認 API 已啟用：https://console.cloud.google.com/apis/library/texttospeech.googleapis.com

## 推薦設置

**開發環境：** 使用方法 1（gcloud auth application-default login）
- 更簡單
- 不需要管理 JSON 文件
- 自動處理憑證更新

**生產環境：** 使用方法 2（服務帳戶 JSON）
- 更安全
- 可以精確控制權限
- 適合 CI/CD 環境

