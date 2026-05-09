import React, { useEffect, useState } from 'react'
import { Layout } from './components/Layout/Layout'
import { ImagePanel } from './components/ImagePanel/ImagePanel'
import { NarrativeView } from './components/NarrativeView/NarrativeView'
import { CharacterSheet } from './components/CharacterSheet/CharacterSheet'
import { Inventory } from './components/Inventory/Inventory'
import { StorySelector } from './components/StorySelector/StorySelector'
import { SaveManager } from './components/SaveManager/SaveManager'
import { CombatPanel } from './components/CombatPanel/CombatPanel'
import { AmbientAudio } from './components/AmbientAudio/AmbientAudio'
import { Settings } from './components/Settings/Settings'
import { useGameState } from './hooks/useGameState'
import { charactersApi, gameApi, settingsApi } from './services/api'
import type { Character, RollResult, RuntimeSettings } from './types'
import './App.css'

type TabId = 'game' | 'character' | 'stories' | 'saves'

function App() {
  const { state, dispatch } = useGameState()
  const [activeTab, setActiveTab] = useState<TabId>('stories')
  const [showSettings, setShowSettings] = useState(false)
  const [toastMsg, setToastMsg] = useState<string | null>(null)
  const [characterList, setCharacterList] = useState<Character[]>([])

  function toast(msg: string, isError = false) {
    void isError
    setToastMsg(msg)
    setTimeout(() => setToastMsg(null), 3000)
  }

  // Load settings and characters on mount
  useEffect(() => {
    settingsApi.get().then((s) => dispatch({ type: 'SET_SETTINGS', payload: s }))
    charactersApi.list().then((chars) => {
      setCharacterList(chars)
      if (chars.length > 0 && !state.character) {
        dispatch({ type: 'SET_CHARACTER', payload: chars[0] })
      }
    })
  }, [])

  async function handleStartGame() {
    if (!state.story || !state.character) {
      toast('Please select both a story and a character first.', true)
      return
    }
    dispatch({ type: 'SET_LOADING', payload: true })
    try {
      const res = await gameApi.start(state.story.id, state.character.id)
      dispatch({ type: 'SET_SESSION', payload: res.session })
      setActiveTab('game')
    } catch (e: unknown) {
      toast((e as Error).message ?? 'Failed to start game', true)
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }

  async function handleAction(text: string, rollResult?: RollResult) {
    if (!state.session) return

    // Show the player's entry immediately so it appears before the DM responds
    if (text.trim() || rollResult) {
      const playerContent = rollResult
        ? `${text}\n**${rollResult.label}: ${rollResult.total}**${rollResult.success !== null ? ` (${rollResult.success ? 'Success' : 'Failure'})` : ''}`
        : text
      dispatch({
        type: 'ADD_ENTRY',
        payload: { role: 'player', content: playerContent, timestamp: new Date().toISOString(), scene_keywords: [] },
      })
    }

    dispatch({ type: 'SET_LOADING', payload: true })
    dispatch({ type: 'SET_STREAMING_TEXT', payload: '' })
    try {
      const response = await fetch(`/api/v1/game/${state.session.id}/action/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, roll_result: rollResult ?? null }),
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let sseBuffer = ''
      const chunkQueue: string[] = []
      let donePayload: typeof state.session | null = null

      // Drain the chunk queue to the UI at a controlled rate (every 80ms)
      const drainInterval = setInterval(() => {
        if (chunkQueue.length > 0) {
          dispatch({ type: 'APPEND_STREAMING_TEXT', payload: chunkQueue.shift()! })
        }
      }, 80)

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        sseBuffer += decoder.decode(value, { stream: true })
        const lines = sseBuffer.split('\n')
        sseBuffer = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const data = JSON.parse(line.slice(6)) as { type: string; text?: string; session?: typeof state.session }
            if (data.type === 'chunk' && data.text) {
              // Split into word+trailing-whitespace tokens so the queue drains one word at a time
              const tokens = data.text.match(/\S+\s*/g) ?? [data.text]
              tokens.forEach((t) => chunkQueue.push(t))
            } else if (data.type === 'done' && data.session) {
              donePayload = data.session
            }
          } catch { /* malformed line */ }
        }
      }

      // Flush remaining chunks before applying the done state
      await new Promise<void>((resolve) => {
        const flush = setInterval(() => {
          if (chunkQueue.length > 0) {
            dispatch({ type: 'APPEND_STREAMING_TEXT', payload: chunkQueue.shift()! })
          } else {
            clearInterval(flush)
            resolve()
          }
        }, 80)
      })
      clearInterval(drainInterval)

      if (donePayload) {
        dispatch({ type: 'UPDATE_SESSION', payload: donePayload })
        dispatch({ type: 'SET_STREAMING_TEXT', payload: null })
      }
    } catch (e: unknown) {
      toast((e as Error).message ?? 'Error sending action', true)
      dispatch({ type: 'SET_STREAMING_TEXT', payload: null })
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }

  async function handleQuickSave() {
    if (!state.session) return
    try {
      await gameApi.save(state.session.id)
      toast('Adventure saved!')
    } catch {
      toast('Failed to save', true)
    }
  }

  function handleStopGame() {
    if (state.session && !window.confirm('Stop the adventure? Unsaved progress will be lost.')) return
    dispatch({ type: 'CLEAR_SESSION' })
    setActiveTab('stories')
  }

  function handleLoadSession(sessionId: string) {
    gameApi.getSession(sessionId).then((session) => {
      dispatch({ type: 'SET_SESSION', payload: session })
      setActiveTab('game')
    }).catch(() => toast('Failed to load session', true))
  }

  function handleSettingsChange(s: RuntimeSettings) {
    dispatch({ type: 'SET_SETTINGS', payload: s })
  }

  const settings = state.settings
  // Join to a primitive string so ImagePanel/AmbientAudio effects only re-fire when content changes
  const sceneKeywords = state.session?.current_scene_keywords?.join(',') ?? ''

  const tabs: { id: TabId; label: string }[] = [
    { id: 'stories', label: 'Stories' },
    { id: 'character', label: 'Character' },
    { id: 'game', label: 'Adventure' },
    { id: 'saves', label: 'Saves' },
  ]

  const sidebar = (
    <div className="sidebar-content">
      {state.session?.combat_state.active && (
        <CombatPanel combat={state.session.combat_state} />
      )}
      {state.character && (
        <div className="sidebar-char-summary parchment medieval-border">
          <div className="sidebar-char-name">{state.character.name}</div>
          <div className="sidebar-char-stats">
            <span className="sstat">HP {state.character.current_hp}/{state.character.max_hp}</span>
            <span className="sstat">AC {state.character.armor_class}</span>
            <span className="sstat">L{state.character.level} {state.character.char_class}</span>
          </div>
          {state.character.conditions.length > 0 && (
            <div className="sidebar-conditions">
              {state.character.conditions.map((c) => (
                <span key={c} className="cond-badge">{c}</span>
              ))}
            </div>
          )}
        </div>
      )}
      {state.session && state.character && (
        <Inventory character={state.character} onUpdate={(c) => dispatch({ type: 'SET_CHARACTER', payload: c })} />
      )}
    </div>
  )

  return (
    <Layout
      showSidebar={activeTab === 'game' && !!state.session}
      sidebarContent={sidebar}
      headerExtra={
        <>
          {settings?.audio_enabled && (
            <AmbientAudio
              keywords={sceneKeywords}
              enabled={settings.audio_enabled}
              volume={settings.audio_volume}
            />
          )}
          <button className="settings-btn" onClick={() => setShowSettings(true)} title="Settings">⚙</button>
        </>
      }
    >
      {/* Tab nav */}
      <nav className="tab-nav parchment">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
        {state.story && state.character && (
          <button
            className="start-adventure-btn"
            onClick={handleStartGame}
            disabled={state.isLoading || !!state.session}
          >
            {state.session ? 'Adventure Active' : '▶ Begin Adventure'}
          </button>
        )}
        {state.session && (
          <>
            <button
              className="quick-save-btn"
              onClick={handleQuickSave}
              disabled={state.isLoading}
              title="Save progress"
            >
              💾 Save
            </button>
            <button
              className="stop-adventure-btn"
              onClick={handleStopGame}
              disabled={state.isLoading}
              title="Stop adventure"
            >
              ⏹ Stop
            </button>
          </>
        )}
      </nav>

      {/* Tab content */}
      <div className="tab-content">
        {activeTab === 'stories' && (
          <div className="tab-pane parchment">
            <StorySelector
              onSelect={(s) => { dispatch({ type: 'SET_STORY', payload: s }) }}
              selectedId={state.story?.id}
            />
          </div>
        )}

        {activeTab === 'character' && (
          <div className="tab-pane parchment">
            <CharacterSheet
              characters={characterList}
              selectedId={state.character?.id}
              onSelect={(c) => {
                dispatch({ type: 'SET_CHARACTER', payload: c })
                if (!characterList.find((ch) => ch.id === c.id)) {
                  setCharacterList((prev) => [...prev, c])
                }
              }}
              onUpdate={(c) => {
                dispatch({ type: 'SET_CHARACTER', payload: c })
                setCharacterList((prev) => prev.map((ch) => ch.id === c.id ? c : ch))
              }}
            />
          </div>
        )}

        {activeTab === 'game' && (
          <div className="tab-pane game-tab">
            {settings?.images_enabled && (
              <ImagePanel
                keywords={sceneKeywords}
                enabled={settings.images_enabled}
                refreshKey={state.session?.turn_count ?? 0}
              />
            )}
            {state.session ? (
              <NarrativeView
                entries={state.session.narrative_history}
                character={state.character}
                isLoading={state.isLoading}
                streamingText={state.streamingText}
                onAction={handleAction}
              />
            ) : (
              <div className="no-session-message parchment">
                <h2>No Active Adventure</h2>
                <p>Select a story and character, then click <strong>Begin Adventure</strong>.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'saves' && (
          <div className="tab-pane parchment">
            <SaveManager
              sessionId={state.session?.id ?? null}
              onLoad={handleLoadSession}
            />
          </div>
        )}
      </div>

      {/* Modals */}
      {showSettings && (
        <Settings onClose={() => setShowSettings(false)} onSettingsChange={handleSettingsChange} />
      )}

      {/* Toast */}
      {toastMsg && (
        <div className="toast-container">
          <div className="toast">{toastMsg}</div>
        </div>
      )}
    </Layout>
  )
}

export default App
