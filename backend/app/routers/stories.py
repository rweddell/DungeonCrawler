from fastapi import APIRouter, HTTPException, UploadFile, File
from app.models.story import Story, StoryCreate
from app.services import story as story_svc

router = APIRouter(prefix="/stories", tags=["stories"])


@router.get("", response_model=list[Story])
async def list_stories():
    return await story_svc.list_stories()


@router.get("/{story_id}", response_model=Story)
async def get_story(story_id: str):
    story = await story_svc.get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.post("/upload", response_model=Story, status_code=201)
async def upload_story(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    content = (await file.read()).decode("utf-8", errors="replace")
    return await story_svc.upload_story_from_text(file.filename, content)


@router.delete("/{story_id}", status_code=204)
async def delete_story(story_id: str):
    ok = await story_svc.delete_story(story_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Story not found or is a built-in story")
