import React from 'react'
import { Icon } from './Icons.jsx'

const TABS = [
  { id: 'search', label: 'Search', icon: 'search' },
  { id: 'docs', label: 'API & MCP', icon: 'code' },
  { id: 'settings', label: 'Settings', icon: 'settings' },
]

export default function Header({ view, setView, theme, onToggleTheme, online }) {
  return (
    <header className="header">
      <div className="header-inner">
        <button className="brand" onClick={() => setView('search')}>
          <span className="brand-mark"><Icon name="search" size={19} /></span>
          <span className="brand-name">Sear<strong>NXG</strong></span>
        </button>

        <nav className="nav-tabs" aria-label="Main navigation">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`nav-tab ${view === tab.id ? 'active' : ''}`}
              onClick={() => setView(tab.id)}
            >
              <Icon name={tab.icon} size={16} />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>

        <div className="header-right">
          <span className={`status-pill ${online ? '' : 'offline'}`} title="Backend status">
            <span className="status-dot" />
            <span>{online ? 'Online' : 'Offline'}</span>
          </span>
          <button
            className="icon-btn"
            onClick={onToggleTheme}
            title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
            aria-label="Toggle theme"
          >
            <Icon name={theme === 'dark' ? 'sun' : 'moon'} size={18} />
          </button>
        </div>
      </div>
    </header>
  )
}
