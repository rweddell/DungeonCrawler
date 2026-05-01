# DungeonCrawler

An AI-powered Dungeon Master (AIDM) companion app for playing D&D 5th Edition solo adventures. The AIDM is driven by a locally hosted LLM via Ollama, with a parchment-themed UI, dynamic artwork from DeviantArt, and full character sheet management.

---

## Project Structure

```
DungeonCrawler/
├── CLAUDE.md
├── frontend/              # React + Vite (TypeScript)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ImagePanel/         # Top banner — DeviantArt scene imagery
│   │   │   ├── NarrativeView/      # Main gameplay area (hybrid narrative + input)
│   │   │   ├── CharacterSheet/     # 5e character sheet viewer/editor
│   │   │   ├── Inventory/          # Equipment and item management
│   │   │   ├── StorySelector/      # Browse/start/upload story prompts
│   │   │   ├── SaveManager/        # Save/load game sessions
│   │   │   ├── CombatPanel/        # Sidebar — initiative, HP, conditions, combat log
│   │   │   ├── AmbientAudio/       # Audio player, scene-based ambient loops
│   │   │   ├── Settings/           # Model selection, context length, auto-save, audio
│   │   │   └── Layout/             # App shell, parchment theming
│   │   ├── hooks/
│   │   ├── services/               # API client wrappers
│   │   ├── types/                  # Shared TypeScript types
│   │   ├── assets/                 # Parchment textures, fonts, icons
│   │   └── App.tsx
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
├── backend/               # Python — FastAPI
│   ├── app/
│   │   ├── main.py                 # FastAPI entrypoint
│   │   ├── routers/
│   │   │   ├── game.py             # Game session CRUD, narrative endpoints
│   │   │   ├── characters.py       # Character sheet CRUD
│   │   │   ├── stories.py          # Story listing, upload, selection
│   │   │   ├── ollama.py           # Ollama proxy — model listing, generation
│   │   │   ├── ollama.py           # Ollama proxy — model listing, generation
│   │   │   ├── images.py           # DeviantArt image search proxy
│   │   │   ├── audio.py            # Ambient audio — scene-to-sound mapping
│   │   │   └── settings.py         # Runtime settings CRUD
│   │   ├── services/
│   │   │   ├── aidm.py             # Core AIDM logic — prompt construction, context management
│   │   │   ├── ollama_client.py    # Ollama HTTP client
│   │   │   ├── deviantart.py       # DeviantArt Client Credentials auth + search client
│   │   │   ├── character.py        # Character sheet logic, 5e validation
│   │   │   ├── inventory.py        # Inventory management logic
│   │   │   ├── story.py            # Story prompt parsing and management
│   │   │   ├── save_manager.py     # Save/load game state
│   │   │   └── audio.py            # Freesound.org client, audio file caching
│   │   ├── models/
│   │   │   ├── character.py        # Pydantic models for 5e character data
│   │   │   ├── game_state.py       # Pydantic models for session/save data
│   │   │   ├── story.py            # Story prompt models
│   │   │   └── inventory.py        # Item and inventory models
│   │   ├── data/
│   │   │   ├── saves/              # Game save files (JSON)
│   │   │   ├── characters/         # Character sheet files (JSON)
│   │   │   ├── stories/            # Built-in + uploaded story prompts (.txt/.json)
│   │   │   ├── srd/                # 5e SRD reference data (classes, races, items, spells)
│   │   │   ├── audio_cache/        # Downloaded ambient audio loops
│   │   │   └── settings.json       # Runtime user settings (persisted)
│   │   └── config.py               # App config, env vars, defaults
│   ├── tests/
│   ├── pyproject.toml              # Managed by uv
│   └── uv.lock
└── README.md
```

---

## Tech Stack

| Layer       | Technology                              |
|-------------|----------------------------------------|
| Frontend    | React 18+, Vite, TypeScript            |
| Backend     | Python 3.11+, FastAPI, Pydantic v2     |
| LLM         | Ollama (local), model configurable     |
| Data Store  | JSON flat files (filesystem-based)     |
| Images      | DeviantArt API (OAuth2)                |
| Pkg Manager | uv (Python), npm (Node)               |

---

## Core Features

### 1. AI Dungeon Master (AIDM)

- Communicates with Ollama's local API (`http://localhost:11434` by default).
- The user can select from any model available in their local Ollama installation. The backend queries `GET /api/tags` to list models and exposes this to the frontend.
- The AIDM maintains a running context of the current game session: character state, inventory, story progress, and recent narrative history.
- Prompt construction lives in `backend/app/services/aidm.py`. The system prompt instructs the model to act as a 5e Dungeon Master, narrate in second person, call for skill checks, manage combat turns, and respect the character's stats.
- The AIDM should extract "scene keywords" from its own narrative responses (e.g., "tavern", "dark forest", "dragon lair") to drive the DeviantArt image search.

### 2. Gameplay Interface (Hybrid Narrative)

- The main panel displays narrative text in a scrollable, book-like format — paragraphs of prose from the AIDM, interspersed with the player's actions.
- AIDM responses are styled differently from player input (e.g., AIDM text in serif font, player actions in a slightly different style or indentation).
- A text input prompt is fixed at the bottom of the narrative panel. The player types freeform actions (e.g., "I search the chest", "I attack the goblin with my longsword").
### 2a. Dice Rolls (v1 — Player Roll)

- When the AIDM calls for a check (skill check, saving throw, attack roll, etc.), it pauses the narrative and signals the roll requirement. The AIDM response should include structured metadata indicating: the roll type, the relevant ability/skill, and the DC (if applicable).
- The frontend intercepts this signal and presents a **click-to-roll UI** inline in the narrative — a button or dice icon styled to the parchment theme (e.g., "Roll Perception (WIS)" with a d20 icon).
- The player clicks to roll. The system generates the random result, applies the character's relevant modifier automatically, and displays the outcome (e.g., "d20: 14 + 3 (WIS) = 17 vs DC 14 — Success").
- The roll result is then sent back to the AIDM so it can narrate the outcome accordingly.
- **v1 scope**: Only d20-based checks (ability checks, saving throws, attack rolls). Damage rolls and other dice types (d4, d6, d8, d10, d12) are handled by the AIDM narratively for now.
- Roll results are displayed as parchment-styled inline cards within the narrative flow.

### 3. Character Sheet (5e)

- Full D&D 5th Edition character sheet: name, race, class, level, ability scores (STR, DEX, CON, INT, WIS, CHA), proficiency bonus, AC, HP, hit dice, speed, saving throws, skills, features, traits, spells.
- Editable via a dedicated character sheet panel/page.
- The AIDM reads from the character data to make contextual decisions (e.g., checking modifiers for skill checks).
- Character creation wizard for new characters (race, class, ability score assignment, background).
- Characters are stored as individual JSON files in `backend/app/data/characters/`.

### 4. Inventory System

- Tracks items, equipment, currency (CP, SP, EP, GP, PP), and encumbrance.
- Items can be marked as equipped, attuned, or stored.
- The AIDM can grant, remove, or modify items during gameplay. These changes are reflected in the inventory in real time.
- Inventory is part of the character JSON but managed through its own UI panel and API endpoints.

### 5. Story System

- A curated set of built-in story prompts ships with the app (stored in `backend/app/data/stories/`). Each story is a structured text/JSON file containing: title, synopsis, opening narration, setting details, key NPCs, and any special rules.
- The player selects a story to begin a new game session.
- **Custom story upload**: Users can upload `.txt` files that serve as story prompts. The backend parses these into the story format. At minimum, the file should contain a title and opening prompt. The system should be flexible — a simple freeform text prompt is valid.
- Stories appear in a selection screen before starting a game.

### 6. Save/Load System

- Game sessions are saved as JSON files in `backend/app/data/saves/`.
- A save file captures: full narrative history, character state snapshot, inventory snapshot, current story ID, AIDM context/memory summary, and a timestamp.
- The player can manually save at any time. Auto-save on a configurable interval (default: every 5 turns) is encouraged.
- The save manager UI lists existing saves with metadata (character name, story title, date, turn count) and allows loading or deleting.

### 7. DeviantArt Image Panel

- A top banner panel (roughly 200–300px tall) displays a scene-appropriate image fetched from DeviantArt.
- The backend extracts scene keywords from the AIDM's latest response and queries the DeviantArt API for fantasy art matching those keywords (e.g., "fantasy tavern interior", "dark cave entrance", "medieval marketplace").
- Images update when the scene changes (not on every single message — only when the setting shifts).
- Authentication uses the **Client Credentials** grant (server-to-server, no user login or redirect URI needed). The backend POSTs `client_id` and `client_secret` to `https://www.deviantart.com/oauth2/token` with `grant_type=client_credentials` to obtain an access token. Tokens are cached and refreshed on expiry.
- DeviantArt credentials are configured via environment variables (`DEVIANTART_CLIENT_ID`, `DEVIANTART_CLIENT_SECRET`).
- The image panel displays attribution (artist name, link to original) below or overlaid on the image.
- Fallback: If DeviantArt returns no results, show a default parchment/atmospheric image.

### 8. Combat Panel (Sidebar)

- When the AIDM initiates combat, a sidebar panel slides in from the right side of the screen.
- The panel displays: **initiative order** (turn list with the current turn highlighted), **HP tracker** (current/max HP for the player character, updated in real time as damage is taken or healing occurs), and **active conditions** (poisoned, stunned, prone, etc. as tagged by the AIDM).
- A scrollable **combat log** at the bottom of the sidebar summarizes each turn's actions, rolls, and results in short-form entries (e.g., "Turn 3 — You attack Goblin: d20+5 = 18 vs AC 15 — Hit — 8 slashing damage").
- The AIDM signals combat start/end via structured metadata in its responses. The frontend toggles the sidebar visibility based on this signal.
- Enemy HP and stats are tracked by the AIDM internally and not shown to the player (fog of war) unless the AIDM narratively reveals them.
- The sidebar collapses automatically when combat ends, and the combat log is preserved in the narrative history.

### 9. Ambient Audio

- Scene-appropriate ambient audio loops play in the background based on the current setting (e.g., tavern chatter, forest ambiance, cave drips, rain, combat drums).
- Audio files are sourced from **Freesound.org** (free, Creative Commons licensed). The backend maps scene keywords (same as the image system) to predefined Freesound search queries and caches downloaded audio files locally in `backend/app/data/audio_cache/`.
- A Freesound API key is required and configured via environment variable (`FREESOUND_API_KEY`).
- Audio crossfades smoothly when the scene changes.
- The frontend provides a volume slider and mute toggle, accessible from the settings page and as a small persistent control in the app header.
- Attribution for audio tracks is stored and accessible from the settings or an info tooltip.

### 10. Settings Page

- An in-app settings page accessible from the main navigation, covering:
  - **Ollama model**: Dropdown populated from the available local models. Changing the model mid-session is allowed (takes effect on the next AIDM response).
  - **Context length**: Slider or input to configure how many turns of history are included in the AIDM prompt (default: 50).
  - **Auto-save**: Toggle on/off, and configure the interval (every N turns).
  - **Audio**: Master volume, mute toggle, ambient audio on/off.
  - **DeviantArt images**: Toggle image panel on/off (for lower-bandwidth or distraction-free play).
  - **Theme**: Future-proofed slot — for now just "Parchment (default)".
- Settings are persisted to `backend/app/data/settings.json` and loaded on app start.
- The backend exposes `GET /settings` and `PUT /settings` endpoints.

---

## Visual Design

- **Parchment theme throughout**: The app background, panels, and containers use a parchment/aged paper texture. Borders should feel hand-drawn or medieval.
- **Typography**: Use a serif font for narrative text (e.g., "Crimson Text", "IM Fell English") and a clean sans-serif for UI controls (e.g., "Inter", "Lato"). Headers and titles can use a decorative fantasy font (e.g., "MedievalSharp", "Uncial Antiqua") — use sparingly.
- **Color palette**: Warm tones — deep browns, aged golds, dark reds, parchment yellows. Avoid bright modern colors. Accent colors for interactive elements (buttons, links) should be muted gold or dark red.
- **Image panel**: Dark border, slightly recessed, like a framed painting hung above the game table.
- **Input prompt**: Styled like a quill/ink input — subtle animation or icon of a quill pen.
- **Scrollbar**: Custom styled to match the parchment theme (thin, brown, ornamental).
- **Dice roll indicators**: Styled as inline badges or parchment cards within the narrative.

---

## API Design (REST)

All endpoints are prefixed with `/api/v1`.

### Ollama
- `GET  /ollama/models` — List available local models
- `POST /ollama/generate` — Proxy a prompt to Ollama and stream/return the response

### Game
- `POST /game/start` — Start a new game session (requires story ID and character ID)
- `POST /game/{session_id}/action` — Send a player action, get AIDM response
- `GET  /game/{session_id}` — Get current game state
- `POST /game/{session_id}/save` — Save the session
- `GET  /game/saves` — List all save files
- `POST /game/load/{save_id}` — Load a saved session
- `DELETE /game/saves/{save_id}` — Delete a save

### Characters
- `GET    /characters` — List all characters
- `GET    /characters/{id}` — Get a character
- `POST   /characters` — Create a new character
- `PUT    /characters/{id}` — Update a character
- `DELETE /characters/{id}` — Delete a character

### Inventory
- `GET  /characters/{id}/inventory` — Get inventory
- `POST /characters/{id}/inventory/items` — Add item
- `PUT  /characters/{id}/inventory/items/{item_id}` — Update item (equip, attune, etc.)
- `DELETE /characters/{id}/inventory/items/{item_id}` — Remove item

### Stories
- `GET  /stories` — List all available stories (built-in + uploaded)
- `GET  /stories/{id}` — Get a story's details
- `POST /stories/upload` — Upload a custom story prompt (.txt)
- `DELETE /stories/{id}` — Delete a custom story

### Images
- `GET /images/search?keywords=fantasy+tavern` — Search DeviantArt and return image URLs + attribution

### Audio
- `GET /audio/scene?keywords=tavern,fireplace` — Get ambient audio URL for the current scene
- `GET /audio/file/{filename}` — Serve a cached audio file

### Settings
- `GET /settings` — Get current runtime settings
- `PUT /settings` — Update runtime settings

---

## Configuration

All configuration is managed through environment variables or a `.env` file at the project root.

```
# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3

# DeviantArt
DEVIANTART_CLIENT_ID=<your_client_id>
DEVIANTART_CLIENT_SECRET=<your_client_secret>

# Freesound
FREESOUND_API_KEY=<your_freesound_api_key>

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DATA_DIR=./backend/app/data

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api/v1

# Game
AUTO_SAVE_INTERVAL=5        # Save every N turns (0 to disable)
MAX_CONTEXT_TURNS=50        # Max turns to include in AIDM context window
```

---

## Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- uv (`pip install uv`)
- Ollama installed and running locally with at least one model pulled

### Setup
```bash
# Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

### Code Standards
- **Python**: Follow PEP 8. Use type hints everywhere. Pydantic v2 for all data models. Async endpoints where I/O bound.
- **TypeScript**: Strict mode enabled. No `any` types. Use interfaces for API response shapes.
- **Components**: Functional React components with hooks. No class components.
- **State Management**: React Context + useReducer for global state (active character, game session). Local state with useState for component-level UI.
- **Error Handling**: Backend returns consistent error responses (`{ "detail": "..." }` with appropriate HTTP status codes). Frontend displays errors as parchment-styled toast notifications.
- **File Naming**: Python — snake_case. TypeScript/React — PascalCase for components, camelCase for utilities.

### Testing
- **Backend**: pytest with httpx for API tests. Test files in `backend/tests/`.
- **Frontend**: Vitest + React Testing Library. Test files colocated as `*.test.tsx`.

---

## Future Considerations (Out of Scope for v1)

- **Expanded dice system**: v1 only supports player-rolled d20 checks. Future versions should add: full damage rolls with all dice types (d4–d12), animated 3D dice visuals, advantage/disadvantage toggle, multi-dice rolls (e.g., 2d6+4), and a dice history log.
- **Multiplayer**: Support for multiple players in a party session over a network. The data model should be designed with this in mind (e.g., sessions reference multiple character IDs) even if the UI only supports single player initially.
- **Combat tracker**: A dedicated tactical combat view with initiative order, HP tracking, and condition management.
- **Map integration**: Procedural or uploaded dungeon maps with token placement.
- **Voice input/output**: Speak actions and hear the AIDM narrate via TTS.
- **Mobile layout**: Responsive design for tablet/phone play.
