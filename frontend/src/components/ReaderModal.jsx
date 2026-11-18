import React, { useEffect, useState } from 'react'
import { motion, useReducedMotion } from 'motion/react'
import { Icon } from './Icons.jsx'
import { api } from '../api.js'

export default function ReaderModal({ url, onClose, onCopy }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const reduce = useReducedMotion()

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    api.extract(url)
      .then((result) => { if (active) setData(result) })
      .catch((err) => { if (active) setError(err.message || 'Could not read this page.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [url])

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <motion.div
      className="modal-overlay"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      transition={{ duration: 0.18 }}
      onMouseDown={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <motion.div
        className="reader-modal"
        role="dialog" aria-modal="true" aria-label="Page reader"
        initial={reduce ? false : { opacity: 0, y: 14, scale: 0.985 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={reduce ? { opacity: 0 } : { opacity: 0, y: 8, scale: 0.99 }}
        transition={{ type: 'spring', stiffness: 280, damping: 28 }}
      >
        <div className="reader-head">
          <div className="reader-head-copy">
            <span className="reader-kicker"><Icon name="bookOpen" size={14} /> Page reader</span>
            <h2>{data?.title || (loading ? 'Loading page…' : 'Unable to read page')}</h2>
            {data && (
              <div className="reader-meta">
                <span>{data.site_name}</span>
                <span>·</span>
                <span>{data.word_count.toLocaleString()} words</span>
                <span>·</span>
                <span>{data.duration_ms} ms</span>
              </div>
            )}
          </div>
          <div className="reader-actions">
            {data && <button className="btn tiny secondary" onClick={() => onCopy(data.text)}><Icon name="copy" size={14} /> Copy</button>}
            <a className="btn tiny secondary" href={url} target="_blank" rel="noreferrer"><Icon name="external" size={14} /> Open</a>
            <button className="icon-btn" onClick={onClose} aria-label="Close"><Icon name="close" size={18} /></button>
          </div>
        </div>

        <div className="reader-body">
          {loading && <div className="loading-state"><span className="spinner big-spinner" /><p>Fetching and extracting readable content…</p></div>}
          {error && <div className="error-box"><Icon name="info" size={18} /><div><strong>Could not read this page</strong><p>{error}</p></div></div>}
          {data && <article className="reader-content">{data.text}</article>}
        </div>
      </motion.div>
    </motion.div>
  )
}
