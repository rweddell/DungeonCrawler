# DungeonCrawler — Project Overview

A high-level description of the architecture, design decisions, and lessons learned. Intended as a seed document for a clean rebuild.

---

## Concept

An AI-powered solo Dungeons & Dragons companion app. The player types freeform actions; a local LLM acts as the Dungeon Master, narrating outcomes, calling for dice rolls, and maintaining story continuity. The entire LLM stack runs locally via [Ollama](https://ollama.com) — no API keys or cloud costs required.

---

## Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + Vite + TypeScript | Fast dev cycle, strong typing |
| Backend | Python + FastAPI | Async, clean REST, Pydantic validation |
| LLM | Ollama (local) | No cost, no latency to external API, model-swappable |
| Storage | JSON flat files | Zero infrastructure, easy to inspect and edit |
| Package mgmt | `uv` (Python), `npm` (Node) | |

---

## Architecture

```
Browser (React)
    │
    │  REST + SSE
    ▼
FastAPI backend
    │
    ├── 3-agent LLM pipeline (via Ollama)
    ├── JSON file store (characters, saves, stories, settings)
    └── Optional integrations (DeviantArt images, Freesound audio)
```

The backend is stateful in memory for active sessions (`dict[session_id, GameSession]`) and persists to disk on save. There is no database.

---

## The 3-Agent LLM Pipeline

This is the core design. Every player action passes through up to three sequential LLM calls, each with its own system prompt and (optionally) its own model and temperature.

```
Player action text
        │
        ▼
  ┌─────────────┐
  │  Assessor   │  "Does this action require a dice roll?"
  │  temp: 0.1  │  Returns: {"needs_roll": true/false}
  └──────┬──────┘
         │ yes
         ▼
  ┌─────────────┐
  │ Dice Agent  │  "What type of roll, which ability, what DC?"
  │  temp: 0.1  │  Returns: {"roll_type", "ability", "dc"}
  └──────┬──────┘
         │ RollRequest sent to frontend
         │ Player clicks to roll
         │ RollResult returned to backend
         ▼
  ┌─────────────┐
  │  Responder  │  Narrates the outcome (or full action if no roll needed)
  │  temp: 0.8  │  Streams output to UI via SSE
  └─────────────┘
```

**Key rules for the pipeline:**
- The assessor and dice agent only need low temperature — they output structured JSON. High temperature here causes hallucinated roll types or false positives.
- The responder needs moderate temperature for vivid, varied prose.
- If the player is submitting a roll result, skip the assessor and dice agent entirely — go straight to the responder.
- The player entry must **not** be appended to `narrative_history` until after the LLM call completes. Appending it first causes the current action to appear twice in the message list (once from the history loop, once added explicitly as the final user message), which causes the model to lose context of the prior scene.

### Prompt Architecture

Each agent has its own `.txt` system prompt file loaded at startup. Keeping prompts in files (not hardcoded strings) makes iteration much faster.

**Responder output format:** The responder must emit structured metadata at the end of its response so the backend can parse state updates without a separate extraction call:

```
(prose narrative)

SCENE_KEYWORDS: keyword1, keyword2, keyword3
MEMORY_PERSON: Name — one-sentence description
MEMORY_PLACE: Name — one-sentence description
MEMORY_EVENT: One-sentence summary of key event this turn
```

The backend strips all of these lines from the narrative before storing it and displaying it to the player.

### Critical Prompt Rules (hard-won)

- **Assessor**: Rolls must only trigger on *explicitly declared player attempts* — not questions, observations, or ambient situational context. Add concrete examples of "never roll" cases (questions, passive looking, movement) directly in the prompt.
- **Responder**: Must be told explicitly never to narrate the player character's choices. The model will sometimes generate a `---` separator and then "play" the player's next action itself. Truncate everything at or after a thematic break (`---`, `***`, `___`) as a post-processing safety net.
- **Metadata leakage**: Never show metadata tag syntax (e.g. `[PENDING ROLL: ...]`) inside system prompts — the model learns to echo the tags into its narrative output. Use markers the model is less likely to reproduce verbatim (e.g. `<<double angle brackets>>`).
- **SCENE_KEYWORDS stripping**: Must be case-insensitive and handle format variations the model produces: `SCENE_KEYWORDS`, `SCENE KEYWORDS`, `SCENE\_KEYWORDS` (markdown-escaped), `**SCENE_KEYWORDS**` (bold). Use `re.sub` with `re.IGNORECASE | re.MULTILINE`, not `str.replace`.

---

## Data Models

### GameSession
The central object. Lives in memory while active; serialized to JSON on save.

```
GameSession
├── id
├── story_id / character_id
├── narrative_history: NarrativeEntry[]
│     each entry: role (aidm | player | system | roll), content, timestamp
│                 optional: roll_request, scene_keywords, combat_signal
├── memory: GameMemory
│     people: ["Mira — elderly caretaker", ...]
│     places: ["East Wing — forbidden area", ...]
│     events: ["Arrived at Blackmoor Manor", ...]
├── combat_state: CombatState (active, round, combatants, log)
├── current_scene_keywords: string[]
└── turn_count
```

### Character
Full D&D 5e character sheet: ability scores, skills, saving throws, HP, AC, conditions, inventory, spells. Stored as individual JSON files. The AIDM reads this to apply modifiers to roll checks.

### Story
Title, synopsis, opening narration, setting description, NPCs, special rules, tags. Stored as JSON files. The player selects one to begin a session. The setting and synopsis are injected into every responder prompt for continuity.

### RuntimeSettings
Persisted to `settings.json`. Includes per-agent model names and temperatures, context window length, auto-save interval, and UI toggles.

---

## Context Management

The responder receives recent `narrative_history` entries formatted as an alternating user/assistant message list (player entries → `user`, aidm entries → `assistant`). A `context_limit` setting caps how many turns back to include.

The `GameMemory` block is injected as a separate context message before the history, giving the model persistent access to named people, places, and past events without requiring every detail to be in the rolling context window. This is important for long sessions where early characters or locations would otherwise be forgotten.

---

## Streaming

The responder streams output to the browser via Server-Sent Events (SSE). The flow:

1. Assessor and dice agent run synchronously (they're fast, return JSON).
2. The responder streams via Ollama's `stream: true` API.
3. Each chunk is forwarded to the browser as `data: {"type": "chunk", "text": "..."}`.
4. When the stream ends, the backend parses the full response (strips metadata, extracts keywords/memory/combat signals, updates session state), then sends a final `data: {"type": "done", "entry": ..., "session": ...}` event.
5. The frontend replaces the streaming placeholder with the cleaned final entry.

This means `SCENE_KEYWORDS` and `MEMORY_*` lines may briefly appear at the end of the streamed text before the `done` event replaces them. This is acceptable for a local app (latency is negligible).

---

## Frontend Architecture

- **React Context + useReducer** for global state (session, character, story, settings, streaming text).
- No external state library.
- API calls centralized in `services/api.ts`.
- Streaming handled directly in `App.tsx` with the Fetch ReadableStream API.
- Each major UI area is its own component folder with colocated CSS.

**Parchment theme:** CSS custom properties for the color palette (`--parchment-light`, `--ink-dark`, `--gold`, `--red-dark`, etc.). Applied consistently across all components. Medieval serif font for narrative, sans-serif for UI controls.

---

## Optional Integrations

These add polish but are not core to gameplay:

| Feature | Service | Notes |
|---|---|---|
| Scene imagery | DeviantArt API | OAuth2 Client Credentials; searches `/browse/tags` with a single keyword; images refresh per DM response (`turn_count` as refresh key) |
| Ambient audio | Freesound.org API | Maps scene keywords to search queries; caches downloaded files locally |

Both require API credentials and degrade gracefully to nothing when not configured.

---

## VRAM / Hardware Constraints

Running three different models requires loading each into VRAM in sequence. On a 6 GB GPU (e.g. RTX 3060), swapping between a 4 GB model and a 4.7 GB model takes 10–30 seconds per swap — unacceptable mid-turn. Practical solution: set all three agents to the same model in settings. The three-model architecture is preserved for future hardware.

`mistral:instruct` at ~4.1 GB is a solid single-model choice: structured enough for the assessor/dice JSON tasks, capable enough for narrative at 0.8 temperature.

---

## What to Simplify in a Rebuild

The current project accumulated complexity over many iterations. For a clean rebuild, consider:

- **Cut ambient audio** from v1. It adds significant backend complexity (Freesound client, file caching, audio serving) for a feature that rarely works reliably.
- **Cut DeviantArt images** from v1 or make them fully optional with a clear fallback. The API is fragile and the keyword filtering required is non-trivial.
- **Flatten settings.** Per-agent model + temperature + context window is the right design, but start with sane defaults and expose a minimal settings UI first.
- **Start with one story.** The story upload system, JSON format enforcement, and custom story parsing add scope. A single hardcoded story is enough to prove the core loop.
- **Keep the 3-agent pipeline.** This design is sound and worth preserving. The prompt files, the structured output parsing, and the post-processing safety nets all carry over cleanly.
- **Keep GameMemory.** Long sessions are unplayable without it. It's low cost (one parsing step per turn) and makes the experience dramatically more coherent.
- **Keep streaming.** The UX difference is significant. The SSE architecture is clean and the implementation is not complex once the agent pipeline is in place.
