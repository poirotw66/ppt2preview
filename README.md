# PPT2Preview - PDF to Video Presentation Generator

將 PDF 投影片轉換為帶有語音解說的影片工具。

## 功能特色

- 📄 自動將 PDF 轉換為圖片
- 🎙️ 使用 Google Gemini TTS 生成語音（支援繁體中文）
- 🎬 自動合成影片，逐頁同步語音與投影片
- ⚡ 多線程處理，加速音訊生成
- 📊 顯示詳細進度條

## 需求

- Python 3.10+
- Google Cloud Text-to-Speech API 憑證
- 以下 Python 套件：
  - `google-cloud-texttospeech`
  - `pdf2image`
  - `moviepy`
  - `Pillow`

## 安裝

```bash
pip install google-cloud-texttospeech pdf2image moviepy Pillow
```

## 使用方式

1. 準備三個檔案：
   - `three_pig_pdf.pdf` - PDF 投影片檔案
   - `transcription.py` - 對話內容（Python 列表格式）
   - `three_pig_page_abstract.md` - 頁面摘要（可選）

2. 設定 Google Cloud 認證：
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
   ```

3. 執行程式：
   ```bash
   python test.py
   ```

## 輸出

程式會生成：
- `slides/` - PDF 轉換的圖片檔案
- `audio_segments/` - 生成的語音片段
- `three_pig_presentation.mp4` - 最終的影片檔案

## 注意事項

- 首次執行會生成所有檔案
- 後續執行會自動使用已存在的檔案（可跳過重複生成）
- 影片合成是最耗時的步驟，請耐心等待

