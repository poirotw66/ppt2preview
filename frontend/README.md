# PPT2Preview Frontend

React + TypeScript + Vite 前端應用程式，用於生成簡報解說影片。

## 功能特色

- 📤 檔案上傳（Markdown 大綱 + PDF 投影片）
- ✍️ 腳本生成與編輯（使用 Gemini AI）
- 🎬 影片生成進度追蹤（WebSocket 即時更新）
- 📥 影片下載與預覽
- 🎨 現代化 UI 設計

## 技術棧

- **React 18** - UI 框架
- **TypeScript** - 類型安全
- **Vite** - 構建工具
- **React Router** - 路由管理
- **Zustand** - 狀態管理
- **Axios** - HTTP 客戶端
- **WebSocket** - 即時通訊

## 安裝與運行

### 前置需求

- Node.js 18+ 
- npm 或 yarn

### 安裝依賴

```bash
cd frontend
npm install
```

### 開發模式

```bash
npm run dev
```

應用程式將在 http://localhost:3000 啟動。

### 構建生產版本

```bash
npm run build
```

構建產物將在 `dist/` 目錄中。

### 預覽生產版本

```bash
npm run preview
```

## 環境變數

創建 `.env` 檔案（可選）：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

## 專案結構

```
frontend/
├── src/
│   ├── components/          # React 元件
│   │   ├── FileUpload.tsx   # 檔案上傳元件
│   │   ├── ScriptEditor.tsx # 腳本編輯器
│   │   ├── ProgressTracker.tsx # 進度追蹤
│   │   └── VideoDownload.tsx   # 影片下載
│   ├── pages/              # 頁面元件
│   │   └── HomePage.tsx     # 主頁面
│   ├── services/           # API 服務
│   │   ├── api.ts          # REST API 客戶端
│   │   └── websocket.ts    # WebSocket 客戶端
│   ├── store/              # 狀態管理
│   │   └── useTaskStore.ts # 任務狀態 store
│   ├── types/              # TypeScript 類型定義
│   │   └── index.ts
│   ├── App.tsx             # 主應用元件
│   └── main.tsx            # 應用入口
├── public/                 # 靜態資源
├── index.html              # HTML 模板
├── vite.config.ts          # Vite 配置
├── tsconfig.json           # TypeScript 配置
└── package.json            # 專案配置
```

## 使用流程

1. **上傳檔案**：選擇 Markdown 大綱檔案和 PDF 投影片
2. **生成腳本**：選擇腳本長度模式，生成並編輯腳本
3. **生成影片**：設定影片參數，開始生成並追蹤進度
4. **下載影片**：影片生成完成後下載

## API 整合

前端通過以下方式與後端 API 整合：

- **REST API**：使用 Axios 進行 HTTP 請求
- **WebSocket**：即時接收任務進度更新
- **代理配置**：Vite 開發服務器自動代理 API 請求

## 開發指南

### 添加新元件

1. 在 `src/components/` 創建新元件檔案
2. 導入並使用在頁面中
3. 添加對應的 CSS 樣式檔案

### 添加新的 API 端點

1. 在 `src/services/api.ts` 中添加新方法
2. 在 `src/types/index.ts` 中添加類型定義
3. 在元件中使用新的 API 方法

### 狀態管理

使用 Zustand store (`useTaskStore`) 管理全域任務狀態：

```typescript
import { useTaskStore } from '@/store/useTaskStore';

const { taskId, status, progress } = useTaskStore();
```

## 故障排除

### API 請求失敗

1. 確認後端服務器正在運行（http://localhost:8000）
2. 檢查 `vite.config.ts` 中的代理配置
3. 確認 CORS 設置正確

### WebSocket 連接失敗

1. 確認後端 WebSocket 端點正常
2. 檢查 WebSocket URL 配置
3. 查看瀏覽器控制台錯誤訊息

## 授權

MIT License

