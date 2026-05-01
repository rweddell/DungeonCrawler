import React, { useEffect, useState, useRef } from 'react'
import { imagesApi } from '../../services/api'
import type { DeviantArtImage } from '../../types'
import './ImagePanel.css'

interface ImagePanelProps {
  // Comma-separated string so React's dependency check is value-based, not reference-based
  keywords: string
  enabled: boolean
}

export function ImagePanel({ keywords, enabled }: ImagePanelProps) {
  const [image, setImage] = useState<DeviantArtImage | null>(null)
  const [loading, setLoading] = useState(false)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  useEffect(() => {
    if (!enabled || !keywords) return
    setLoading(true)
    imagesApi
      .search(keywords)
      .then((res) => {
        if (!mountedRef.current) return
        if (res.images.length > 0) setImage(res.images[0])
      })
      .catch(() => {})
      .finally(() => {
        if (mountedRef.current) setLoading(false)
      })
  }, [keywords, enabled])

  if (!enabled) return null

  return (
    <div className="image-panel medieval-border">
      {loading && !image && (
        <div className="image-panel-placeholder">
          <div className="spinner" />
        </div>
      )}
      {image ? (
        <div className="image-panel-content">
          <img
            src={image.url}
            alt={image.title}
            className="image-panel-img"
            loading="lazy"
          />
          <div className="image-panel-attribution">
            <a href={image.page_url} target="_blank" rel="noopener noreferrer">
              {image.title} by {image.author}
            </a>
          </div>
        </div>
      ) : !loading ? (
        <div className="image-panel-placeholder">
          <span className="image-panel-placeholder-text">No scene image available</span>
        </div>
      ) : null}
    </div>
  )
}
