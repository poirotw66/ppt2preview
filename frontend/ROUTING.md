# 前端路由結構

## 路由配置

前端應用程式使用 React Router 實現多頁面路由，每個步驟都有獨立的頁面。

### 路由列表

| 路徑 | 頁面元件 | 說明 |
|------|---------|------|
| `/` | 重定向到 `/upload` | 首頁自動跳轉 |
| `/upload` | `UploadPage` | 步驟 1: 上傳檔案 |
| `/script` | `ScriptPage` | 步驟 2: 生成與編輯腳本 |
| `/video` | `VideoPage` | 步驟 3: 生成影片 |
| `/download` | `DownloadPage` | 步驟 4: 下載影片 |

## 頁面結構

### UploadPage (`/upload`)
- **功能**: 上傳 Markdown 大綱檔案和 PDF 投影片
- **導航**: 
  - 上傳成功後可前往 `/script`
  - 如果任務已存在且狀態為 `script_ready`，自動跳轉到 `/script`
  - 如果任務已存在且狀態為 `generating_video` 或 `completed`，自動跳轉到 `/video`

### ScriptPage (`/script`)
- **功能**: 生成腳本（選擇長度模式）和編輯腳本內容
- **前置條件**: 必須有 `taskId`
- **導航**:
  - 如果沒有 `taskId`，自動跳轉到 `/upload`
  - 如果狀態為 `generating_video`，自動跳轉到 `/video`
  - 如果狀態為 `completed`，自動跳轉到 `/download`
  - 可以返回 `/upload` 或前往 `/video`

### VideoPage (`/video`)
- **功能**: 設定影片參數並生成影片，顯示即時進度
- **前置條件**: 必須有 `taskId` 且狀態為 `script_ready` 或 `generating_video`
- **導航**:
  - 如果沒有 `taskId`，自動跳轉到 `/upload`
  - 如果狀態為 `completed`，自動跳轉到 `/download`
  - 如果狀態不是 `generating_video` 或 `script_ready`，自動跳轉到 `/script`
  - 可以返回 `/script` 或前往 `/download`

### DownloadPage (`/download`)
- **功能**: 預覽和下載生成的影片
- **前置條件**: 必須有 `taskId` 且狀態為 `completed`
- **導航**:
  - 如果沒有 `taskId`，自動跳轉到 `/upload`
  - 如果狀態不是 `completed`，自動跳轉到 `/video`
  - 可以返回 `/video` 或建立新任務（重置狀態並跳轉到 `/upload`）

## 導航元件

### Navigation Component
頂部導航欄顯示當前進度和可訪問的步驟：
- **視覺指示**: 
  - 已完成步驟顯示 ✓
  - 當前步驟高亮顯示
  - 未完成步驟顯示步驟號碼
  - 不可訪問的步驟顯示為禁用狀態
- **連接線**: 步驟之間的連接線，已完成的步驟顯示為綠色

## 狀態管理

使用 Zustand store (`useTaskStore`) 管理全域狀態：
- `taskId`: 當前任務 ID
- `status`: 任務狀態
- `progress`: 進度百分比
- `scriptContent`: 腳本內容
- 狀態在所有頁面間共享

## 自動重定向邏輯

每個頁面都會根據當前狀態自動重定向到合適的頁面：
- 確保用戶不會訪問無效的頁面
- 根據任務進度自動導航
- 提供流暢的用戶體驗

## 使用範例

```typescript
import { useNavigate } from 'react-router-dom';
import { useTaskStore } from '@/store/useTaskStore';

function MyComponent() {
  const navigate = useNavigate();
  const { taskId, status } = useTaskStore();

  const handleNext = () => {
    navigate('/script');
  };

  return <button onClick={handleNext}>下一步</button>;
}
```

## 注意事項

1. **狀態同步**: 確保 Zustand store 中的狀態與後端 API 同步
2. **路由保護**: 每個頁面都有前置條件檢查，防止無效訪問
3. **導航一致性**: 使用統一的導航按鈕樣式和行為
4. **響應式設計**: 導航元件在移動設備上自動調整佈局

