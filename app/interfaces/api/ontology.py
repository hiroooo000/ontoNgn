from fastapi import APIRouter, Body, Depends, HTTPException

from app.core.dependencies import get_text_llm_service
from app.domain.models.graph import ExtractionResult
from app.domain.services.text_llm_service import ITextLLMService
from app.usecases.generate_ontology import GenerateOntologyUseCase

router = APIRouter()


@router.post("/generate", response_model=ExtractionResult)
async def generate_ontology_api(
    text_content: str = Body(..., media_type="text/plain"),
    llm_service: ITextLLMService = Depends(get_text_llm_service),
) -> ExtractionResult:
    try:
        usecase = GenerateOntologyUseCase(llm_service=llm_service)
        result = await usecase.execute(text_content=text_content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
