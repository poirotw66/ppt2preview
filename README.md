# PPT2Preview - 投影片影片生成平台

一個現代化的 SaaS 服務，將投影片和大綱自動轉換為帶有 AI 語音解說的專業影片。

## ✨ 功能特色

### 核心功能
- 📤 **智能上傳** - 支援 PDF/PPTX 投影片 + Markdown 大綱同時上傳
- 🤖 **AI 腳本生成** - 使用 Google Gemini 2.0 Flash 根據投影片內容和大綱自動生成解說腳本
- ✏️ **腳本優化** - 支援三種長度模式（短/中/長），可手動編輯調整
- 🎙️ **多音色 TTS** - 支援 30 種 Google Cloud TTS 音色（14 女性 + 16 男性），使用 Gemini 2.5 Flash TTS
- 🎬 **自動合成影片** - 逐頁同步語音與投影片，生成專業影片
- 📊 **實時進度追蹤** - WebSocket 實時顯示生成進度
- 📁 **歷史專案管理** - 查看並重新開啟過去的專案

### 技術亮點
- ⚡ 多線程音訊處理，加速生成速度
- 🎨 Glassmorphism 現代化 UI 設計
- 🌓 完整響應式設計，支援桌面/平板/手機
- 💾 本地持久化設定（音色選擇）
- 🔄 自動狀態恢復，支援中斷後繼續

## 🏗️ 技術架構

### 後端 (Python + FastAPI)
- **框架**: FastAPI + Uvicorn
- **AI 模型**: Google Gemini 2.0 Flash（腳本生成與優化）
- **TTS**: Google Cloud Text-to-Speech API (Gemini 2.5 Flash TTS)
- **影片處理**: MoviePy
- **檔案處理**: pdf2image, python-pptx, Pillow
- **通訊**: WebSocket (實時進度推送)

### 前端 (React + TypeScript)
- **框架**: React 18 + TypeScript + Vite
- **樣式**: CSS Variables + Glassmorphism
- **字體**: Poppins (標題) + Open Sans (內文)
- **狀態管理**: Zustand
- **路由**: React Router v6
- **圖標**: SVG (Heroicons 風格)

## 📋 系統需求

### 後端需求
- Python 3.10+
- Google Cloud 專案（啟用 Text-to-Speech API）
- Gemini API Key（Gemini 2.0 Flash 模型）
- 以下環境變數：
  ```bash
  GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
  GEMINI_API_KEY=your_gemini_api_key
  ```

### 前端需求
- Node.js 16+
- npm 或 yarn

## 🚀 快速開始

### 1. 克隆專案
```bash
git clone https://github.com/poirotw66/ppt2preview.git
cd ppt2preview
```

### 2. 後端設置
```bash
# 安裝依賴
pip install -r backend/requirements.txt

# 設定 Google Cloud 憑證
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
export GEMINI_API_KEY="your_gemini_api_key"

# 啟動後端服務 (端口 3001)
cd backend
uvicorn main:app --host 0.0.0.0 --port 3001 --reload
```

### 3. 前端設置
```bash
# 安裝依賴
cd frontend
npm install

# 啟動開發伺服器 (端口 3000)
npm run dev
```

### 4. 訪問應用
打開瀏覽器訪問：`http://localhost:3000`

## 📖 使用流程

1. **上傳檔案** 
   - 上傳投影片 (PDF/PPTX)
   - 上傳大綱 (Markdown)

2. **生成腳本**
   - AI 自動根據內容生成解說腳本
   - 查看和複製生成的腳本

3. **優化腳本**
   - 選擇長度模式（短/中/長）
   - 手動編輯調整內容
   - 保存最終版本

4. **生成影片**
   - 設定影片參數（背景音樂音量、淡入淡出時間等）
   - 實時查看生成進度
   - 自動合成影片

5. **下載影片**
   - 預覽完成的影片
   - 下載 MP4 檔案

## 🎨 設計系統

### 色彩方案
- **主色**: 信任藍 (#2563EB)
- **次要色**: 藍色調 (#3B82F6)
- **CTA**: 活力橙 (#F97316)
- **背景**: 漸變色 (藍紫到粉紅)

### UI 特點
- Glassmorphism (玻璃態效果)
- 流暢的過渡動畫
- 無障礙設計 (WCAG AA 標準)
- 支援 `prefers-reduced-motion`

## 📂 專案結構

```
ppt2preview/
├── backend/
│   ├── api/              # API 路由和模型
│   ├── services/         # 業務邏輯服務
│   ├── utils/            # 工具函數
│   └── main.py           # FastAPI 入口
├── frontend/
│   ├── src/
│   │   ├── components/   # React 組件
│   │   ├── pages/        # 頁面組件
│   │   ├── services/     # API 客戶端
│   │   ├── store/        # 狀態管理
│   │   └── types/        # TypeScript 類型
│   └── public/
│       └── voice/        # TTS 音色試聽檔案
├── output/               # 生成的專案輸出
└── requirements.txt      # Python 依賴
```

## 🎙️ 支援的音色

- **女性音色 (14 種)**: Achernar, Aoede, Autonoe, Callirrhoe, Despina, Erinome, Gacrux, Kore, Laomedeia, Leda, Pulcherrima, Sulafat, Vindemiatrix, Zephyr
- **男性音色 (16 種)**: Achird, Algenib, Algieba, Alnilam, Charon, Enceladus, Fenrir, Iapetus, Orus, Puck, Rasalgethi, Sadachbia, Sadaltager, Schedar, Umbriel, Zubenelgenubi

所有音色均支援繁體中文，可在設定頁面試聽和選擇。

## 🔧 API 端點

### REST API
- `POST /api/v1/upload` - 上傳檔案
- `GET /api/v1/task/{task_id}/status` - 獲取任務狀態
- `POST /api/v1/generate-script` - 生成腳本
- `POST /api/v1/optimize-script` - 優化腳本
- `POST /api/v1/generate-video` - 生成影片
- `GET /api/v1/history` - 獲取歷史專案列表
- `GET /api/v1/download/{task_id}` - 下載影片

### WebSocket
- `WS /api/v1/ws/{task_id}` - 實時進度推送

## 📊 輸出檔案

每個專案在 `output/{task_id}/` 目錄下生成：
```
output/{task_id}/
├── slides/              # 投影片圖片
├── audio_segments/      # 音訊片段
├── outline.md           # 原始大綱
├── script.json          # 生成的腳本
├── optimized_script.json # 優化後的腳本
└── final_video.mp4      # 最終影片
```

## 🐛 故障排除

### 常見問題

1. **TTS API 錯誤**
   - 確認 `GOOGLE_APPLICATION_CREDENTIALS` 設定正確
   - 檢查 Google Cloud 專案是否啟用 Text-to-Speech API

2. **Gemini API 錯誤**
   - 確認 `GEMINI_API_KEY` 設定正確
   - 檢查 API 配額是否充足

3. **影片生成失敗**
   - 確認 `pdf2image` 正確安裝（需要 poppler）
   - 檢查磁碟空間是否充足

4. **前端連接失敗**
   - 確認後端運行在 `http://localhost:3001`
   - 檢查防火牆設定

## 📝 開發筆記

### 效能優化
- 圖片縮放使用 JPEG (quality=95) 而非 PNG，速度提升 3-5 倍
- 多線程音訊生成，支援並行處理
- 使用 `thumbnail()` 方法進行圖片縮小，速度提升 20-30%

### 安全性
- 檔案上傳大小限制 (10MB)
- 任務 ID 使用 UUID，防止猜測
- CORS 設定限制來源

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

MIT License

## 👨‍💻 作者

poirotw66

---

**注意**: 本專案需要 Google Cloud 憑證和 Gemini API Key 才能運行。請確保在使用前正確設定環境變數。

