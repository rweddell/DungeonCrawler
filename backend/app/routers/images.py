from fastapi import APIRouter
from app.services.deviantart import deviantart_client

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/search")
async def search_images(keywords: str = "fantasy adventure"):
    results = await deviantart_client.search(keywords)
    return {"images": results, "keywords": keywords}
