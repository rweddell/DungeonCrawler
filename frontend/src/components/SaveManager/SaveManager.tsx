import React, { useEffect, useState } from 'react'
import type { SaveFileMeta } from '../../types'
import { gameApi } from '../../services/api'
import './SaveManager.css'

interface SaveManagerProps {
  sessionId: string | null
  onLoad: (sessionId: string) => void
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export function SaveManager({ sessionId, onLoad }: SaveManagerProps) {
  const [saves, setSaves] = useState<SaveFileMeta[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  function flash(msg: string) {
    setMessage(msg)
    setTimeout(() => setMessage(null), 2000)
  }

  useEffect(() => {
    gameApi.listSaves().then(setSaves).finally(() => setLoading(false))
  }, [])

  async function handleSave() {
    if (!sessionId) return
    setSaving(true)
    try {
      await gameApi.save(sessionId)
      const updated = await gameApi.listSaves()
      setSaves(updated)
      flash('Game saved!')
    } catch {
      flash('Save failed')
    } finally {
      setSaving(false)
    }
  }

  async function handleLoad(saveId: string) {
    try {
      const res = await gameApi.load(saveId)
      onLoad(res.session_id)
      flash('Session loaded')
    } catch {
      flash('Load failed')
    }
  }

  async function handleDelete(saveId: string, e: React.MouseEvent) {
    e.stopPropagation()
    if (!confirm('Delete this save?')) return
    try {
      await gameApi.deleteSave(saveId)
      setSaves((prev) => prev.filter((s) => s.id !== saveId))
    } catch {
      flash('Delete failed')
    }
  }

  return (
    <div className="save-manager parchment medieval-border">
      <div className="save-manager-header">
        <h3 className="save-manager-title">Saves</h3>
        {sessionId && (
          <button className="save-now-btn" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : '💾 Save'}
          </button>
        )}
      </div>
      {message && <div className="save-message">{message}</div>}
      {loading ? (
        <div className="save-loading"><div className="spinner" /></div>
      ) : saves.length === 0 ? (
        <p className="saves-empty">No saves yet</p>
      ) : (
        <div className="saves-list">
          {saves.map((s) => (
            <div key={s.id} className="save-item" onClick={() => handleLoad(s.id)}>
              <div className="save-item-main">
                <span className="save-char-name">{s.character_name}</span>
                <span className="save-story-title">{s.story_title}</span>
              </div>
              <div className="save-item-meta">
                <span>{formatDate(s.saved_at)}</span>
                <span>Turn {s.turn_count}</span>
                <button className="delete-save-btn" onClick={(e) => handleDelete(s.id, e)}>✕</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
