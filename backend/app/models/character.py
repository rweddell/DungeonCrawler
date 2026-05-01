from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class AbilityScores(BaseModel):
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10


class SavingThrows(BaseModel):
    strength: bool = False
    dexterity: bool = False
    constitution: bool = False
    intelligence: bool = False
    wisdom: bool = False
    charisma: bool = False


class Skills(BaseModel):
    acrobatics: bool = False
    animal_handling: bool = False
    arcana: bool = False
    athletics: bool = False
    deception: bool = False
    history: bool = False
    insight: bool = False
    intimidation: bool = False
    investigation: bool = False
    medicine: bool = False
    nature: bool = False
    perception: bool = False
    performance: bool = False
    persuasion: bool = False
    religion: bool = False
    sleight_of_hand: bool = False
    stealth: bool = False
    survival: bool = False


class SpellSlots(BaseModel):
    level_1: int = 0
    level_2: int = 0
    level_3: int = 0
    level_4: int = 0
    level_5: int = 0
    level_6: int = 0
    level_7: int = 0
    level_8: int = 0
    level_9: int = 0


class Spell(BaseModel):
    name: str
    level: int
    school: str = ""
    casting_time: str = ""
    range: str = ""
    components: str = ""
    duration: str = ""
    description: str = ""
    prepared: bool = False


class Currency(BaseModel):
    cp: int = 0
    sp: int = 0
    ep: int = 0
    gp: int = 0
    pp: int = 0


class Item(BaseModel):
    id: str
    name: str
    quantity: int = 1
    weight: float = 0.0
    description: str = ""
    equipped: bool = False
    attuned: bool = False
    item_type: str = "misc"  # weapon, armor, potion, misc, etc.
    properties: dict = Field(default_factory=dict)


class Inventory(BaseModel):
    items: list[Item] = Field(default_factory=list)
    currency: Currency = Field(default_factory=Currency)


class Character(BaseModel):
    id: str
    name: str
    race: str = ""
    char_class: str = ""
    subclass: str = ""
    level: int = 1
    experience: int = 0
    background: str = ""
    alignment: str = ""
    age: str = ""
    appearance: str = ""
    personality_traits: str = ""
    ideals: str = ""
    bonds: str = ""
    flaws: str = ""

    ability_scores: AbilityScores = Field(default_factory=AbilityScores)
    saving_throws: SavingThrows = Field(default_factory=SavingThrows)
    skills: Skills = Field(default_factory=Skills)

    max_hp: int = 10
    current_hp: int = 10
    temp_hp: int = 0
    hit_dice: str = "1d8"
    hit_dice_remaining: int = 1

    armor_class: int = 10
    initiative_bonus: int = 0
    speed: int = 30
    proficiency_bonus: int = 2

    features: list[str] = Field(default_factory=list)
    traits: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    proficiencies: list[str] = Field(default_factory=list)

    spell_slots: SpellSlots = Field(default_factory=SpellSlots)
    spell_slots_used: SpellSlots = Field(default_factory=SpellSlots)
    spells_known: list[Spell] = Field(default_factory=list)
    spell_save_dc: int = 8
    spell_attack_bonus: int = 0
    spellcasting_ability: str = ""

    inventory: Inventory = Field(default_factory=Inventory)

    death_saves_successes: int = 0
    death_saves_failures: int = 0
    conditions: list[str] = Field(default_factory=list)

    notes: str = ""


class CharacterCreate(BaseModel):
    name: str
    race: str = ""
    char_class: str = ""
    level: int = 1
    background: str = ""
    alignment: str = ""
    ability_scores: AbilityScores = Field(default_factory=AbilityScores)


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    race: Optional[str] = None
    char_class: Optional[str] = None
    level: Optional[int] = None
    experience: Optional[int] = None
    background: Optional[str] = None
    alignment: Optional[str] = None
    ability_scores: Optional[AbilityScores] = None
    saving_throws: Optional[SavingThrows] = None
    skills: Optional[Skills] = None
    max_hp: Optional[int] = None
    current_hp: Optional[int] = None
    temp_hp: Optional[int] = None
    armor_class: Optional[int] = None
    speed: Optional[int] = None
    features: Optional[list[str]] = None
    traits: Optional[list[str]] = None
    languages: Optional[list[str]] = None
    proficiencies: Optional[list[str]] = None
    spells_known: Optional[list[Spell]] = None
    conditions: Optional[list[str]] = None
    notes: Optional[str] = None
