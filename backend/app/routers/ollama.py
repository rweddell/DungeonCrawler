from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ollama_client import ollama_client

router = APIRouter(prefix="/ollama", tags=["ollama"])


class GenerateRequest(BaseModel):
    model: str
    prompt: str
    system: str = ""


@router.get("/models")
async def list_models():
    try:
        models = await ollama_client.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Cannot reach Ollama: {e}")


@router.post("/generate")
async def generate(req: GenerateRequest):
    try:
        response = await ollama_client.generate(
            model=req.model,
            prompt=req.prompt,
            system=req.system,
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
