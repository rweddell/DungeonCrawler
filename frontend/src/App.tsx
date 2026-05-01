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
    dispatch({ type: 'SET_LOADING', payload: true })
    try {
      const res = await gameApi.action(state.session.id, {
        text,
        roll_result: rollResult ?? null,
      })
      dispatch({ type: 'UPDATE_SESSION', payload: res.session })
    } catch (e: unknown) {
      toast((e as Error).message ?? 'Error sending action', true)
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
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
              />
            )}
            {state.session ? (
              <NarrativeView
                entries={state.session.narrative_history}
                character={state.character}
                isLoading={state.isLoading}
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
