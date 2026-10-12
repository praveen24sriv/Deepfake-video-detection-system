import { useEffect, useRef, useState } from 'react'
import { formatBytes, MAX_UPLOAD_MB } from '../api.js'
import { CloseIcon, FilmIcon, UploadIcon } from './Icons.jsx'

export default function UploadZone({ file, onSelect, onRemove, disabled, error }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [previewUrl, setPreviewUrl] = useState(null)
  const [previewFailed, setPreviewFailed] = useState(false)

  // Create the object URL for the preview and always revoke it when the file
  // changes or the component unmounts.
  useEffect(() => {
    if (!file) {
      setPreviewUrl(null)
      return undefined
    }
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    setPreviewFailed(false)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const pick = (files) => {
    if (disabled || !files || files.length === 0) return
    onSelect(files[0])
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    pick(e.dataTransfer.files)
  }

  const openPicker = () => inputRef.current?.click()

  return (
    <div className="upload">
      <input
        ref={inputRef}
        id="video-input"
        className="visually-hidden"
        type="file"
        accept=".mp4,.avi,.mov,video/mp4,video/x-msvideo,video/quicktime"
        aria-label="Choose a video file"
        tabIndex={-1}
        disabled={disabled}
        onChange={(e) => {
          pick(e.target.files)
          e.target.value = '' // allow re-selecting the same file after removing it
        }}
      />

      {!file ? (
        <div
          className={`dropzone${dragging ? ' dragging' : ''}${error ? ' invalid' : ''}`}
          onDragOver={(e) => {
            e.preventDefault()
            if (!disabled) setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <span className="dropzone-icon">
            <UploadIcon width={26} height={26} />
          </span>
          <p className="dropzone-title">Drag and drop a video here</p>
          <p className="muted">MP4, AVI or MOV, up to {MAX_UPLOAD_MB} MB</p>
          <button type="button" className="btn btn-secondary" onClick={openPicker}>
            Browse Files
          </button>
        </div>
      ) : (
        <div className={`file-card${error ? ' invalid' : ''}`}>
          <div className="file-head">
            <span className="file-icon">
              <FilmIcon />
            </span>
            <div className="file-meta">
              <p className="file-name" title={file.name}>
                {file.name}
              </p>
              <p className="muted">{formatBytes(file.size)}</p>
            </div>
            <div className="file-actions">
              <button type="button" className="btn btn-ghost" onClick={openPicker} disabled={disabled}>
                Replace
              </button>
              <button
                type="button"
                className="icon-btn"
                onClick={onRemove}
                disabled={disabled}
                aria-label="Remove selected video"
              >
                <CloseIcon width={18} height={18} />
              </button>
            </div>
          </div>

          {previewUrl && !previewFailed && !error && (
            <video
              className="preview"
              src={previewUrl}
              controls
              preload="metadata"
              onError={() => setPreviewFailed(true)}
            />
          )}
          {previewFailed && !error && (
            <p className="muted preview-note">
              Your browser can’t preview this file, but it can still be analyzed.
            </p>
          )}
        </div>
      )}

      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
