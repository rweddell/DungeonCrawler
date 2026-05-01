import type {
  Character,
  CharacterCreate,
  Story,
  GameSession,
  SaveFileMeta,
  NarrativeEntry,
  PlayerAction,
  RuntimeSettings,
  DeviantArtImage,
  Item,
  Inventory,
} from '../types'

const BASE = '/api/v1'

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

// ─── Ollama ───────────────────────────────────────────────────────────────────

export const ollamaApi = {
  listModels: () => request<{ models: { name: string }[] }>('/ollama/models'),
}

// ─── Characters ───────────────────────────────────────────────────────────────

export const charactersApi = {
  list: () => request<Character[]>('/characters'),
  get: (id: string) => request<Character>(`/characters/${id}`),
  create: (data: CharacterCreate) =>
    request<Character>('/characters', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: Partial<Character>) =>
    request<Character>(`/characters/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (id: string) =>
    request<void>(`/characters/${id}`, { method: 'DELETE' }),

  getInventory: (id: string) => request<Inventory>(`/characters/${id}/inventory`),
  addItem: (id: string, item: Partial<Item>) =>
    request<Item>(`/characters/${id}/inventory/items`, {
      method: 'POST',
      body: JSON.stringify(item),
    }),
  updateItem: (charId: string, itemId: string, data: Partial<Item>) =>
    request<Item>(`/characters/${charId}/inventory/items/${itemId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  removeItem: (charId: string, itemId: string) =>
    request<void>(`/characters/${charId}/inventory/items/${itemId}`, { method: 'DELETE' }),
}

// ─── Stories ──────────────────────────────────────────────────────────────────

export const storiesApi = {
  list: () => request<Story[]>('/stories'),
  get: (id: string) => request<Story>(`/stories/${id}`),
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return fetch(`${BASE}/stories/upload`, { method: 'POST', body: form }).then(
      (r) => r.json() as Promise<Story>
    )
  },
  delete: (id: string) => request<void>(`/stories/${id}`, { method: 'DELETE' }),
}

// ─── Game ─────────────────────────────────────────────────────────────────────

export const gameApi = {
  start: (storyId: string, characterId: string) =>
    request<{ session_id: string; opening: NarrativeEntry; session: GameSession }>('/game/start', {
      method: 'POST',
      body: JSON.stringify({ story_id: storyId, character_id: characterId }),
    }),
  getSession: (sessionId: string) => request<GameSession>(`/game/${sessionId}`),
  action: (sessionId: string, action: PlayerAction) =>
    request<{ entry: NarrativeEntry; session: GameSession }>(`/game/${sessionId}/action`, {
      method: 'POST',
      body: JSON.stringify(action),
    }),
  save: (sessionId: string) =>
    request<{ save_id: string; saved_at: string }>(`/game/${sessionId}/save`, { method: 'POST' }),
  listSaves: () => request<SaveFileMeta[]>('/game/saves'),
  load: (saveId: string) =>
    request<{ session_id: string; session: GameSession }>(`/game/load/${saveId}`, {
      method: 'POST',
    }),
  deleteSave: (saveId: string) =>
    request<void>(`/game/saves/${saveId}`, { method: 'DELETE' }),
}

// ─── Images ───────────────────────────────────────────────────────────────────

export const imagesApi = {
  search: (keywords: string) =>
    request<{ images: DeviantArtImage[] }>(`/images/search?keywords=${encodeURIComponent(keywords)}`),
}

// ─── Audio ────────────────────────────────────────────────────────────────────

export const audioApi = {
  getScene: (keywords: string) =>
    request<{ audio: { filename: string; url: string; name: string; username: string; license: string } | null }>(
      `/audio/scene?keywords=${encodeURIComponent(keywords)}`
    ),
}

// ─── Settings ─────────────────────────────────────────────────────────────────

export const settingsApi = {
  get: () => request<RuntimeSettings>('/settings'),
  update: (data: RuntimeSettings) =>
    request<RuntimeSettings>('/settings', { method: 'PUT', body: JSON.stringify(data) }),
}
