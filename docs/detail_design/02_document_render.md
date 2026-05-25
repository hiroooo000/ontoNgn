# ドキュメントレンダラー詳細設計

アップロードされたPDF、Word、Excelデータを、非同期で画像バッファ（PNG）へレンダリングするモジュールです。Word/Excel などの Office ファイルは、LibreOffice をヘッドレスモードで起動し、一時的に PDF へ変換した上で画像化します。

## 1. 実装詳細 (`app/interfaces/renderers/document_renderer.py`)

```python
import asyncio
from pdf2image import convert_from_bytes
import tempfile
import os
from typing import List

class DocumentRenderer:
    """PDF / DOCX / XLSX バッファを画像バッファ（PNG）にレンダリングする"""
    
    async def render_to_images(self, file_buffer: bytes, file_extension: str) -> List[bytes]:
        pdf_buffer = file_buffer

        # Word/Excel の場合は LibreOffice を介して PDF に事前変換
        if file_extension.lower() in ['.docx', '.xlsx']:
            pdf_buffer = await self._convert_to_pdf_via_libreoffice(file_buffer, file_extension)

        # PDF を各ページ PNG のバイナリデータに展開
        return await self._render_pdf_to_pngs(pdf_buffer)

    async def _convert_to_pdf_via_libreoffice(self, buffer: bytes, ext: str) -> bytes:
        temp_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(dir=temp_dir, suffix=ext, delete=False) as temp_input:
            temp_input.write(buffer)
            temp_input_path = temp_input.name

        try:
            # LibreOffice ヘッドレスモードで PDF 変換を実行
            process = await asyncio.create_subprocess_shell(
                f'soffice --headless --convert-to pdf --outdir "{temp_dir}" "{temp_input_path}"',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            base_name = os.path.splitext(os.path.basename(temp_input_path))[0]
            temp_pdf_path = os.path.join(temp_dir, f"{base_name}.pdf")
            
            with open(temp_pdf_path, 'rb') as f:
                pdf_buffer = f.read()

            return pdf_buffer
        finally:
            # 一時ファイルの削除
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)
            if 'temp_pdf_path' in locals() and os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

    async def _render_pdf_to_pngs(self, pdf_buffer: bytes) -> List[bytes]:
        # pdf2image を用いて PNG リストへレンダリング (並列処理のために executor を使うことを推奨)
        images = convert_from_bytes(pdf_buffer, dpi=200)
        
        buffers = []
        for img in images:
            import io
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            buffers.append(img_byte_arr.getvalue())
            
        return buffers
```
