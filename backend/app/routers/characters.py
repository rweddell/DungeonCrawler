from fastapi import APIRouter, HTTPException
from app.models.character import Character, CharacterCreate, CharacterUpdate
from app.models.inventory import ItemCreate, ItemUpdate
from app.services import character as char_svc
from app.services import inventory as inv_svc

router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("", response_model=list[Character])
async def list_characters():
    return await char_svc.list_characters()


@router.get("/{char_id}", response_model=Character)
async def get_character(char_id: str):
    char = await char_svc.get_character(char_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    return char


@router.post("", response_model=Character, status_code=201)
async def create_character(data: CharacterCreate):
    return await char_svc.create_character(data)


@router.put("/{char_id}", response_model=Character)
async def update_character(char_id: str, data: CharacterUpdate):
    char = await char_svc.update_character(char_id, data)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")
    return char


@router.delete("/{char_id}", status_code=204)
async def delete_character(char_id: str):
    ok = await char_svc.delete_character(char_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Character not found")


# Inventory sub-routes
@router.get("/{char_id}/inventory")
async def get_inventory(char_id: str):
    inv = await inv_svc.get_inventory(char_id)
    if inv is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return inv


@router.post("/{char_id}/inventory/items", status_code=201)
async def add_item(char_id: str, data: ItemCreate):
    item = await inv_svc.add_item(char_id, data)
    if item is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return item


@router.put("/{char_id}/inventory/items/{item_id}")
async def update_item(char_id: str, item_id: str, data: ItemUpdate):
    item = await inv_svc.update_item(char_id, item_id, data)
    if item is None:
        raise HTTPException(status_code=404, detail="Item or character not found")
    return item


@router.delete("/{char_id}/inventory/items/{item_id}", status_code=204)
async def remove_item(char_id: str, item_id: str):
    ok = await inv_svc.remove_item(char_id, item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Item not found")
