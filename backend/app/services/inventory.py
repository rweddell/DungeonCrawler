from __future__ import annotations
import uuid
from app.models.character import Character, Item
from app.models.inventory import ItemCreate, ItemUpdate
from app.services.character import get_character, save_character


async def get_inventory(char_id: str) -> dict | None:
    char = await get_character(char_id)
    if not char:
        return None
    return char.inventory.model_dump()


async def add_item(char_id: str, data: ItemCreate) -> Item | None:
    char = await get_character(char_id)
    if not char:
        return None
    item = Item(id=str(uuid.uuid4()), **data.model_dump())
    char.inventory.items.append(item)
    await save_character(char)
    return item


async def update_item(char_id: str, item_id: str, data: ItemUpdate) -> Item | None:
    char = await get_character(char_id)
    if not char:
        return None
    for i, item in enumerate(char.inventory.items):
        if item.id == item_id:
            update_data = data.model_dump(exclude_unset=True)
            updated_item = item.model_copy(update=update_data)
            char.inventory.items[i] = updated_item
            await save_character(char)
            return updated_item
    return None


async def remove_item(char_id: str, item_id: str) -> bool:
    char = await get_character(char_id)
    if not char:
        return False
    original_len = len(char.inventory.items)
    char.inventory.items = [i for i in char.inventory.items if i.id != item_id]
    if len(char.inventory.items) == original_len:
        return False
    await save_character(char)
    return True
