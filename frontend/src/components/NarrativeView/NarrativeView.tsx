import React, { useEffect, useRef, useState, FormEvent } from 'react'
import type { NarrativeEntry, RollRequest, RollResult, Character } from '../../types'
import { rollForRequest } from '../../hooks/useDiceRoll'
import './NarrativeView.css'

interface NarrativeViewProps {
  entries: NarrativeEntry[]
  character: Character | null
  isLoading: boolean
  onAction: (text: string, rollResult?: RollResult) => void
}

function RollCard({ request, character, onRoll }: {
  request: RollRequest
  character: Character
  onRoll: (result: RollResult) => void
}) {
  const [rolled, setRolled] = useState<RollResult | null>(null)

  function handleRoll() {
    const result = rollForRequest(request, character)
    setRolled(result)
    onRoll(result)
  }

  const abilityLabel = request.ability.replace(/_/g, ' ')
  const dcText = request.dc ? ` (DC ${request.dc})` : ''

  return (
    <div className="roll-card medieval-border parchment">
      <div className="roll-card-type">
        {request.roll_type.replace(/_/g, ' ')}
      </div>
      <div className="roll-card-ability">Roll {abilityLabel}{dcText}</div>
      {!rolled ? (
        <button className="roll-btn" onClick={handleRoll}>
          🎲 Roll d20
        </button>
      ) : (
        <div className={`roll-result ${rolled.success === true ? 'success' : rolled.success === false ? 'failure' : ''}`}>
          <span className="roll-d20">{rolled.d20}</span>
          <span className="roll-mod">
            {rolled.modifier >= 0 ? '+' : ''}{rolled.modifier}
          </span>
          <span className="roll-equals"> = </span>
          <span className="roll-total">{rolled.total}</span>
          {rolled.dc && (
            <span className="roll-dc"> vs DC {rolled.dc}</span>
          )}
          {rolled.success !== null && (
            <span className="roll-outcome">
              {rolled.success ? '✓ Success' : '✗ Failure'}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

function EntryBlock({ entry, character, onRollResult }: {
  entry: NarrativeEntry
  character: Character | null
  onRollResult: (result: RollResult, entryContent: string) => void
}) {
  const paragraphs = entry.content.split('\n').filter(Boolean)

  if (entry.role === 'aidm') {
    return (
      <div className="entry entry-aidm">
        {paragraphs.map((p, i) => (
          <p key={i} className="entry-paragraph">{p}</p>
        ))}
        {entry.roll_request && character && (
          <RollCard
            request={entry.roll_request}
            character={character}
            onRoll={(result) => onRollResult(result, entry.content)}
          />
        )}
      </div>
    )
  }

  if (entry.role === 'player') {
    return (
      <div className="entry entry-player">
        <span className="entry-player-label">You:</span>
        {paragraphs.map((p, i) => (
          <span key={i}> {p}</span>
        ))}
      </div>
    )
  }

  if (entry.role === 'system') {
    return (
      <div className="entry entry-system">
        {entry.content}
      </div>
    )
  }

  return null
}

export function NarrativeView({ entries, character, isLoading, onAction }: NarrativeViewProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const [inputText, setInputText] = useState('')

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [entries, isLoading])

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const text = inputText.trim()
    if (!text || isLoading) return
    setInputText('')
    onAction(text)
  }

  function handleRollResult(result: RollResult) {
    if (isLoading) return
    onAction('', result)
  }

  return (
    <div className="narrative-view">
      <div className="narrative-scroll parchment" ref={scrollRef}>
        {entries.length === 0 && (
          <div className="narrative-empty">
            <p>Select a story and character to begin your adventure...</p>
          </div>
        )}
        {entries.map((entry, i) => (
          <EntryBlock
            key={i}
            entry={entry}
            character={character}
            onRollResult={handleRollResult}
          />
        ))}
        {isLoading && (
          <div className="entry entry-aidm entry-loading">
            <span className="loading-dots">
              <span>.</span><span>.</span><span>.</span>
            </span>
          </div>
        )}
      </div>

      <form className="narrative-input-area parchment medieval-border" onSubmit={handleSubmit}>
        <div className="narrative-input-row">
          <span className="quill-icon">✒</span>
          <textarea
            className="narrative-input"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="What do you do?"
            rows={2}
            disabled={isLoading}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(e as unknown as FormEvent)
              }
            }}
          />
          <button type="submit" className="send-btn" disabled={isLoading || !inputText.trim()}>
            {isLoading ? <span className="spinner" style={{ width: 16, height: 16 }} /> : 'Send'}
          </button>
        </div>
      </form>
    </div>
  )
}
