import React, { useEffect, useState, useRef } from 'react'
import type { Story } from '../../types'
import { storiesApi } from '../../services/api'
import './StorySelector.css'

interface StorySelectorProps {
  onSelect: (story: Story) => void
  selectedId?: string
}

export function StorySelector({ onSelect, selectedId }: StorySelectorProps) {
  const [stories, setStories] = useState<Story[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    storiesApi
      .list()
      .then(setStories)
      .catch(() => setError('Failed to load stories'))
      .finally(() => setLoading(false))
  }, [])

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const story = await storiesApi.upload(file)
      setStories((prev) => [...prev, story])
    } catch {
      setError('Upload failed')
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation()
    if (!confirm('Delete this story?')) return
    try {
      await storiesApi.delete(id)
      setStories((prev) => prev.filter((s) => s.id !== id))
    } catch {
      setError('Could not delete story')
    }
  }

  if (loading) return <div className="story-selector-loading"><div className="spinner" /></div>

  return (
    <div className="story-selector">
      <h2 className="story-selector-title">Choose Your Adventure</h2>
      {error && <div className="story-error">{error}</div>}
      <div className="story-list">
        {stories.map((story) => (
          <div
            key={story.id}
            className={`story-card medieval-border parchment ${selectedId === story.id ? 'selected' : ''}`}
            onClick={() => onSelect(story)}
          >
            <div className="story-card-header">
              <h3 className="story-card-title">{story.title}</h3>
              {story.is_custom && (
                <button
                  className="story-delete-btn"
                  onClick={(e) => handleDelete(story.id, e)}
                  title="Delete story"
                >
                  ✕
                </button>
              )}
            </div>
            <p className="story-card-synopsis">{story.synopsis}</p>
            <div className="story-card-tags">
              {story.tags.map((tag) => (
                <span key={tag} className="story-tag">{tag}</span>
              ))}
              {story.is_custom && <span className="story-tag custom-tag">custom</span>}
            </div>
          </div>
        ))}
      </div>
      <div className="story-upload">
        <input
          ref={fileRef}
          type="file"
          accept=".txt"
          id="story-upload-input"
          onChange={handleUpload}
          hidden
        />
        <label htmlFor="story-upload-input" className="upload-btn">
          {uploading ? 'Uploading...' : '+ Upload Custom Story (.txt)'}
        </label>
      </div>
    </div>
  )
}
