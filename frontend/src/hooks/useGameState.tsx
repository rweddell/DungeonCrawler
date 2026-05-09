import React, { createContext, useContext, useReducer, ReactNode } from 'react'
import type {
  Character,
  GameSession,
  RuntimeSettings,
  Story,
  NarrativeEntry,
} from '../types'

interface GameState {
  session: GameSession | null
  character: Character | null
  story: Story | null
  settings: RuntimeSettings | null
  isLoading: boolean
  error: string | null
  currentImage: string | null
  currentAudioUrl: string | null
  streamingText: string | null
}

type Action =
  | { type: 'SET_SESSION'; payload: GameSession }
  | { type: 'SET_CHARACTER'; payload: Character }
  | { type: 'SET_STORY'; payload: Story }
  | { type: 'SET_SETTINGS'; payload: RuntimeSettings }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_IMAGE'; payload: string | null }
  | { type: 'SET_AUDIO'; payload: string | null }
  | { type: 'ADD_ENTRY'; payload: NarrativeEntry }
  | { type: 'UPDATE_SESSION'; payload: GameSession }
  | { type: 'CLEAR_SESSION' }
  | { type: 'SET_STREAMING_TEXT'; payload: string | null }
  | { type: 'APPEND_STREAMING_TEXT'; payload: string }

function reducer(state: GameState, action: Action): GameState {
  switch (action.type) {
    case 'SET_SESSION':
      return { ...state, session: action.payload }
    case 'SET_CHARACTER':
      return { ...state, character: action.payload }
    case 'SET_STORY':
      return { ...state, story: action.payload }
    case 'SET_SETTINGS':
      return { ...state, settings: action.payload }
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }
    case 'SET_ERROR':
      return { ...state, error: action.payload }
    case 'SET_IMAGE':
      return { ...state, currentImage: action.payload }
    case 'SET_AUDIO':
      return { ...state, currentAudioUrl: action.payload }
    case 'ADD_ENTRY':
      if (!state.session) return state
      return {
        ...state,
        session: {
          ...state.session,
          narrative_history: [...state.session.narrative_history, action.payload],
        },
      }
    case 'UPDATE_SESSION':
      return { ...state, session: action.payload }
    case 'CLEAR_SESSION':
      return { ...state, session: null, currentImage: null, currentAudioUrl: null, streamingText: null }
    case 'SET_STREAMING_TEXT':
      return { ...state, streamingText: action.payload }
    case 'APPEND_STREAMING_TEXT':
      return { ...state, streamingText: (state.streamingText ?? '') + action.payload }
    default:
      return state
  }
}

const initialState: GameState = {
  session: null,
  character: null,
  story: null,
  settings: null,
  isLoading: false,
  error: null,
  currentImage: null,
  currentAudioUrl: null,
  streamingText: null,
}

interface GameContextValue {
  state: GameState
  dispatch: React.Dispatch<Action>
}

const GameContext = createContext<GameContextValue | null>(null)

export function GameProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  return <GameContext.Provider value={{ state, dispatch }}>{children}</GameContext.Provider>
}

export function useGameState() {
  const ctx = useContext(GameContext)
  if (!ctx) throw new Error('useGameState must be used within GameProvider')
  return ctx
}
