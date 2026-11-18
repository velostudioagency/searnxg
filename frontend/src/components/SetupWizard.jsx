import React, { useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { api } from '../api.js'
import { Icon } from './Icons.jsx'
import SearxngHelp from './SearxngHelp.jsx'

export default function SetupWizard({ setup, onClose, onComplete }) {
  const reduce = useReducedMotion()
  const [step, setStep] = useState('choose')
  const [url, setUrl] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  async function finish(promise) {
    setBusy(true)
    setError('')
    try {
      const result = await promise
      setMessage(result.message || 'You are all set.')
      onComplete?.(result.public)
      setStep('done')
    } catch (err) {
      setError(err.message || 'Something went wrong. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  async function testSearch() {
    setBusy(true)
    setError('')
    try {
      const result = await api.search({ query: 'how does web search work', category: 'general', limit: 5 })
      const working = result.providers.filter((p) => p.ok).length
      setMessage(
        result.number_of_results > 0
          ? `All good. ${result.number_of_results} results came back from ${working} source${working === 1 ? '' : 's'}.`
          : 'Sources are slow right now. A built-in library will keep search working.',
      )
      setStep('done')
    } catch (err) {
      setError(err.message || 'The test could not complete.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <motion.div
      className="modal-overlay"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      onMouseDown={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <motion.div
        className="setup-modal"
        role="dialog" aria-modal="true" aria-label="Set up SearNXG"
        initial={reduce ? false : { opacity: 0, y: 14, scale: 0.985 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 8 }}
        transition={{ type: 'spring', stiffness: 280, damping: 28 }}
      >
        <div className="setup-head">
          <span className="feature-icon"><Icon name="sparkles" size={19} /></span>
          <div>
            <h2>Let's get you set up</h2>
            <p>Takes about a minute. You can change everything later in Settings.</p>
          </div>
          <button className="icon-btn setup-close" onClick={onClose} aria-label="Close">
            <Icon name="close" size={16} />
          </button>
        </div>

        <AnimatePresence mode="wait">
          {step === 'choose' && (
            <motion.div
              key="choose" className="setup-body"
              initial={reduce ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <button className="setup-option recommended" onClick={() => finish(api.quickSetup())} disabled={busy}>
                <span className="setup-option-icon"><Icon name="bolt" size={20} /></span>
                <span className="setup-option-copy">
                  <strong>Just make it work <em>Recommended</em></strong>
                  <span>Turns on the reliable search sources. No choices, no jargon.</span>
                </span>
                <Icon name="arrow" size={17} />
              </button>

              <button className="setup-option" onClick={() => setStep('searxng')} disabled={busy}>
                <span className="setup-option-icon"><Icon name="database" size={20} /></span>
                <span className="setup-option-copy">
                  <strong>I have my own search engine</strong>
                  <span>Connect a SearXNG address you already run. Optional.</span>
                </span>
                <Icon name="arrow" size={17} />
              </button>

              <button className="setup-option" onClick={() => setStep('check')} disabled={busy}>
                <span className="setup-option-icon"><Icon name="pulse" size={20} /></span>
                <span className="setup-option-copy">
                  <strong>Show me what's working</strong>
                  <span>See a plain-language check of each search source.</span>
                </span>
                <Icon name="arrow" size={17} />
              </button>
              {busy && <p className="setup-working"><span className="spinner" /> Working on it…</p>}
            </motion.div>
          )}

          {step === 'searxng' && (
            <motion.div key="searxng" className="setup-body"
              initial={reduce ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <h3>Connect your search engine</h3>
              <p className="setup-explain">Paste the web address of your SearXNG instance. It usually looks like <code>http://localhost:8080</code>. Skip this if you don't have one.</p>
              <input
                className="setup-input"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="http://localhost:8080"
                aria-label="SearXNG address"
              />
              <SearxngHelp />
              {error && <p className="setup-error"><Icon name="info" size={14} /> {error}</p>}
              <div className="setup-actions">
                <button className="btn secondary" onClick={() => { setStep('choose'); setError('') }}>Back</button>
                <button className="btn primary" onClick={() => finish(api.setupSearxng(url))} disabled={busy || !url.trim()}>
                  {busy ? <span className="spinner" /> : <Icon name="check" size={15} />} Connect
                </button>
              </div>
            </motion.div>
          )}

          {step === 'check' && (
            <motion.div key="check" className="setup-body"
              initial={reduce ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <h3>Here's what we found</h3>
              <div className="setup-checks">
                {(setup?.checks || []).map((check) => (
                  <div className="setup-check" key={check.id}>
                    <span className={`setup-check-dot ${check.ok ? 'ok' : ''}`}>
                      <Icon name={check.ok ? 'check' : 'info'} size={12} />
                    </span>
                    <span><strong>{check.title}</strong><small>{check.detail}</small></span>
                  </div>
                ))}
              </div>
              {error && <p className="setup-error"><Icon name="info" size={14} /> {error}</p>}
              <div className="setup-actions">
                <button className="btn secondary" onClick={() => { setStep('choose'); setError('') }}>Back</button>
                <button className="btn primary" onClick={testSearch} disabled={busy}>
                  {busy ? <span className="spinner" /> : <Icon name="search" size={15} />} Run a test search
                </button>
              </div>
            </motion.div>
          )}

          {step === 'done' && (
            <motion.div key="done" className="setup-body setup-done"
              initial={reduce ? false : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <span className="setup-done-icon"><Icon name="check" size={26} /></span>
              <h3>{message}</h3>
              <p>Everything else is optional. Open Settings whenever you want to fine-tune things.</p>
              <button className="btn primary" onClick={onClose}>Start searching <Icon name="arrow" size={15} /></button>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  )
}
