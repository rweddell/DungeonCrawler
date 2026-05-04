from __future__ import annotations
import json
import re
from datetime import datetime
from app.models.character import Character
from app.models.game_state import (
    GameSession,
    NarrativeEntry,
    RollRequest,
    PlayerAction,
)
from app.models.story import Story
from app.services.ollama_client import ollama_client

SYSTEM_PROMPT = """You are an expert Dungeon Master running a D&D 5th Edition solo adventure. Narrate in second person ("You see...", "You hear..."). Be vivid and immersive.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DICE ROLLS — READ THIS CAREFULLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NEVER roll dice yourself. NEVER write things like:
  ✗ "Roll: 1d20 + 3 = 14"
  ✗ "Rolling for initiative... you get a 7."
  ✗ "*rolls dice* — 12, success!"

The player rolls their own dice in the UI. Your job is to REQUEST the roll.

When a roll is required, output ROLL_REQUEST on its own line at the TOP of your response, then write the narrative WITHOUT the result (the player hasn't rolled yet):
A roll is required to determine the outcome of the player's action. 
You should request a roll when the outcome of an event is uncertain and depends on the character's stats, or when the player explicitly indicates they want to roll for something.     

ROLL_REQUEST: {"roll_type": "ability_check", "ability": "perception", "dc": 14}
You hold your torch aloft and peer into the darkness of the corridor...

Valid roll_types: ability_check, saving_throw, attack_roll
Valid abilities: strength, dexterity, constitution, intelligence, wisdom, charisma,
  acrobatics, animal_handling, arcana, athletics, deception, history, insight,
  intimidation, investigation, medicine, nature, perception, performance, persuasion,
  religion, sleight_of_hand, stealth, survival

The player will then send you the roll result as [ROLL RESULT: ...] and you narrate the outcome.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SCENE KEYWORDS — required at the END of every response:
SCENE_KEYWORDS: keyword1, keyword2, keyword3
Output EXACTLY 3 keywords — the most visually distinctive nouns of the current setting.
These drive an image search, so prefer concrete visual nouns over abstract descriptions.
Pick the 3 that would best find matching fantasy artwork (e.g. "dungeon, torchlight, iron door").
Do NOT include character names, NPC names, or abstract words like "tension" or "danger".

COMBAT:
  COMBAT_START — add this line when combat begins
  COMBAT_END   — add this line when combat ends

GENERAL RULES:
- Maintain world, NPC, and story continuity at all times.
- Narrate outcomes of [ROLL RESULT] messages the player sends you.
- Apply the character's stats to all mechanical decisions.
- Respond only as the Dungeon Master. Never break character.
- Never make up dialogue for the player, but you can and should write dialogue for NPCs.
"""


def _char_summary(char: Character) -> str:
    a = char.ability_scores
    mods = {
        "STR": (a.strength - 10) // 2,
        "DEX": (a.dexterity - 10) // 2,
        "CON": (a.constitution - 10) // 2,
        "INT": (a.intelligence - 10) // 2,
        "WIS": (a.wisdom - 10) // 2,
        "CHA": (a.charisma - 10) // 2,
    }
    mod_str = ", ".join(f"{k}:{'+' if v >= 0 else ''}{v}" for k, v in mods.items())
    items = [i.name for i in char.inventory.items if i.equipped]
    equipped = ", ".join(items) if items else "nothing equipped"
    conditions = ", ".join(char.conditions) if char.conditions else "none"

    return (
        f"Character: {char.name} | {char.race} {char.char_class} Level {char.level} | "
        f"HP: {char.current_hp}/{char.max_hp} | AC: {char.armor_class} | "
        f"Prof: +{char.proficiency_bonus} | {mod_str} | "
        f"Equipped: {equipped} | Conditions: {conditions}"
    )


def _build_messages(
    session: GameSession,
    character: Character,
    story: Story,
    action: PlayerAction,
    context_limit: int,
) -> list[dict]:
    messages = []

    # Inject character state as a system-adjacent user message
    char_ctx = _char_summary(character)
    story_ctx = f"Story: {story.title}\nSetting: {story.setting}\nSynopsis: {story.synopsis}"
    messages.append({"role": "user", "content": f"[CONTEXT]\n{story_ctx}\n{char_ctx}"})
    messages.append({"role": "assistant", "content": "Understood. I'll keep these details in mind throughout our session."})

    # Add recent narrative history
    history = session.narrative_history[-context_limit:]
    for entry in history:
        if entry.role == "aidm":
            messages.append({"role": "assistant", "content": entry.content})
        elif entry.role == "player":
            messages.append({"role": "user", "content": entry.content})
        elif entry.role == "roll":
            messages.append({"role": "user", "content": entry.content})

    # Current player action
    action_text = action.text
    if action.roll_result:
        r = action.roll_result
        success_text = ""
        if r.success is not None:
            success_text = f" — {'Success' if r.success else 'Failure'}"
        action_text += (
            f"\n[ROLL RESULT: {r.label} | d20: {r.d20} + {r.modifier} = {r.total}"
            + (f" vs DC {r.dc}" if r.dc else "")
            + success_text
            + "]"
        )
    messages.append({"role": "user", "content": action_text})

    return messages


# Maps natural-language ability/skill names the LLM might write to canonical ability keys
_ABILITY_ALIASES: dict[str, str] = {
    "strength": "strength", "str": "strength",
    "dexterity": "dexterity", "dex": "dexterity", "initiative": "dexterity",
    "constitution": "constitution", "con": "constitution",
    "intelligence": "intelligence", "int": "intelligence",
    "wisdom": "wisdom", "wis": "wisdom",
    "charisma": "charisma", "cha": "charisma",
    "acrobatics": "acrobatics", "animal handling": "animal_handling",
    "arcana": "arcana", "athletics": "athletics", "deception": "deception",
    "history": "history", "insight": "insight", "intimidation": "intimidation",
    "investigation": "investigation", "medicine": "medicine", "nature": "nature",
    "perception": "perception", "performance": "performance",
    "persuasion": "persuasion", "religion": "religion",
    "sleight of hand": "sleight_of_hand", "sleight_of_hand": "sleight_of_hand",
    "stealth": "stealth", "survival": "survival",
    "attack": "strength", "attack roll": "strength",
}


def _infer_roll_type(raw_ability: str) -> str:
    lower = raw_ability.lower()
    if "saving throw" in lower or "save" in lower:
        return "saving_throw"
    if "attack" in lower:
        return "attack_roll"
    return "ability_check"


def _extract_implicit_roll(text: str) -> RollRequest | None:
    """Last-resort heuristic: detect when the LLM wrote inline roll text instead of ROLL_REQUEST."""
    lower = text.lower()

    # Pattern: "make a/an <ability> check" or "roll a/an <ability> check/save/saving throw"
    check_pattern = re.search(
        r"(?:make|roll)\s+(?:a\s+)?(?:an\s+)?"
        r"([\w\s]+?)\s+(?:check|saving throw|save|attack roll)",
        lower,
    )
    if check_pattern:
        raw_ability = check_pattern.group(1).strip()
        ability = _ABILITY_ALIASES.get(raw_ability)
        if ability:
            roll_type = _infer_roll_type(check_pattern.group(0))
            # Try to find a DC nearby
            dc_match = re.search(r"\bdc\s*(\d+)\b", lower)
            dc = int(dc_match.group(1)) if dc_match else None
            return RollRequest(roll_type=roll_type, ability=ability, dc=dc)

    # Pattern: LLM rolled for the player — "rolling for <ability>", "roll: 1d20"
    rolled_pattern = re.search(r"rolling\s+for\s+([\w\s]+?)[\.,!]", lower)
    if rolled_pattern:
        raw_ability = rolled_pattern.group(1).strip()
        ability = _ABILITY_ALIASES.get(raw_ability)
        if ability:
            dc_match = re.search(r"\bdc\s*(\d+)\b", lower)
            dc = int(dc_match.group(1)) if dc_match else None
            return RollRequest(roll_type="ability_check", ability=ability, dc=dc)

    return None


def _parse_response(raw: str) -> tuple[str, RollRequest | None, list[str], str | None]:
    """Parse AIDM raw output into (narrative, roll_request, scene_keywords, combat_signal)."""
    roll_request: RollRequest | None = None
    scene_keywords: list[str] = []
    combat_signal: str | None = None
    narrative = raw

    # Extract structured ROLL_REQUEST tag
    roll_match = re.search(r"ROLL_REQUEST:\s*(\{.*?\})", raw, re.DOTALL)
    if roll_match:
        try:
            roll_data = json.loads(roll_match.group(1))
            roll_request = RollRequest(**roll_data)
        except Exception:
            pass
        narrative = narrative.replace(roll_match.group(0), "").strip()

    # Extract scene keywords — hard cap at 3 regardless of what the LLM outputs
    kw_match = re.search(r"SCENE_KEYWORDS:\s*(.+)$", raw, re.MULTILINE)
    if kw_match:
        scene_keywords = [k.strip() for k in kw_match.group(1).split(",") if k.strip()][:4]
        narrative = narrative.replace(kw_match.group(0), "").strip()

    # Extract combat signals
    if "COMBAT_START" in narrative:
        combat_signal = "start"
        narrative = narrative.replace("COMBAT_START", "").strip()
    elif "COMBAT_END" in narrative:
        combat_signal = "end"
        narrative = narrative.replace("COMBAT_END", "").strip()

    # Fallback: if the LLM ignored ROLL_REQUEST format, try to detect inline roll text
    if roll_request is None:
        roll_request = _extract_implicit_roll(narrative)

    return narrative, roll_request, scene_keywords, combat_signal


async def process_action(
    session: GameSession,
    character: Character,
    story: Story,
    action: PlayerAction,
    model: str,
    context_limit: int = 50,
) -> tuple[GameSession, NarrativeEntry]:
    """Process a player action and return the updated session + AIDM narrative entry."""

    # Record player action in history
    player_entry_content = action.text
    if action.roll_result:
        r = action.roll_result
        success_str = f" ({'Success' if r.success else 'Failure'})" if r.success is not None else ""
        player_entry_content = (
            f"{action.text}\n**{r.label}: {r.total}**{success_str}"
        )

    player_entry = NarrativeEntry(
        role="player",
        content=player_entry_content,
        timestamp=datetime.utcnow(),
    )
    session.narrative_history.append(player_entry)

    # Build messages and call Ollama
    messages = _build_messages(session, character, story, action, context_limit)
    raw_response = await ollama_client.chat(model=model, messages=messages)

    # Parse structured metadata from response
    narrative, roll_request, scene_keywords, combat_signal = _parse_response(raw_response)

    # Update session
    if scene_keywords:
        session.current_scene_keywords = scene_keywords

    if combat_signal == "start" and not session.combat_state.active:
        session.combat_state.active = True
        session.combat_state.round = 1
    elif combat_signal == "end" and session.combat_state.active:
        session.combat_state.active = False

    session.turn_count += 1
    session.updated_at = datetime.utcnow()

    aidm_entry = NarrativeEntry(
        role="aidm",
        content=narrative,
        timestamp=datetime.utcnow(),
        roll_request=roll_request,
        scene_keywords=scene_keywords,
        combat_signal=combat_signal,
    )
    session.narrative_history.append(aidm_entry)

    return session, aidm_entry


async def start_session(
    session: GameSession,
    character: Character,
    story: Story,
    model: str,
) -> NarrativeEntry:
    """Generate the opening narration for a new game session."""
    opening = story.opening_narration or f"You are about to embark on an adventure: {story.title}."

    prompt = (
        f"Begin the adventure '{story.title}'. "
        f"The character is {character.name}, a level {character.level} {character.race} {character.char_class}. "
        f"Opening narration to use as inspiration:\n\n{opening}\n\n"
        f"Set the scene vividly. End with SCENE_KEYWORDS as instructed."
    )

    messages = [
        {
            "role": "user",
            "content": (
                f"[CONTEXT]\nStory: {story.title}\nSetting: {story.setting}\n"
                f"Character: {character.name} | {character.race} {character.char_class} Level {character.level} | "
                f"HP: {character.max_hp}/{character.max_hp} | AC: {character.armor_class}"
            ),
        },
        {"role": "assistant", "content": "Understood. Ready to begin."},
        {"role": "user", "content": prompt},
    ]

    raw_response = await ollama_client.chat(model=model, messages=messages)
    narrative, roll_request, scene_keywords, combat_signal = _parse_response(raw_response)

    if scene_keywords:
        session.current_scene_keywords = scene_keywords

    entry = NarrativeEntry(
        role="aidm",
        content=narrative,
        timestamp=datetime.utcnow(),
        scene_keywords=scene_keywords,
    )
    session.narrative_history.append(entry)
    session.updated_at = datetime.utcnow()

    return entry
