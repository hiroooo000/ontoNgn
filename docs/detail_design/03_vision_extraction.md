# 03. Vision Extraction API 詳細設計

## 1. 抽象サービス定義 (`app/domain/services/vision_service.py`)

```python
from abc import ABC, abstractmethod
from typing import List

class IVisionService(ABC):
    @abstractmethod
    async def extract_text(self, image_buffers: List[bytes]) -> str:
        """画像群からレイアウト情報を維持した構造化テキストを抽出"""
        pass
```

## 2. LMStudio 連携ゲートウェイ (Vision抽出実装)

`app/interfaces/gateways/lmstudio_gateway.py` のVision関連の実装を抜粋します。

```python
import base64
from openai import AsyncOpenAI
from typing import List
from fastapi import Depends
from app.core.config import get_settings, Settings
from app.domain.services.vision_service import IVisionService

class LMStudioGateway(IVisionService):
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.client = AsyncOpenAI(
            base_url=settings.llm_api_base_url,
            api_key=settings.llm_api_key or "lm-studio",
        )
        self.vision_model_name = settings.vision_model_name

    async def extract_text(self, image_buffers: List[bytes]) -> str:
        content_parts = [
            {
                "type": "text",
                "text": "提供された画像に含まれる文書の構造（見出し、表、段落など）を維持し、詳細なMarkdown形式のテキストとして抽出してください。"
            }
        ]
        
        for buf in image_buffers:
            base64_image = base64.b64encode(buf).decode('utf-8')
            content_parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}"
                }
            })

        response = await self.client.chat.completions.create(
            model=self.vision_model_name,
            temperature=0.0,
            messages=[{"role": "user", "content": content_parts}]
        )
        return response.choices[0].message.content or ""
```
