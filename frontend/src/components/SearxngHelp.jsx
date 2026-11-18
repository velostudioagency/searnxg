import React from 'react'
import { Icon } from './Icons.jsx'

export default function SearxngHelp() {
  return (
    <details className="help-details">
      <summary><Icon name="info" size={14} /> What is this, and where do I find the address?</summary>
      <div className="help-body">
        <p>You don't need one. SearNXG already searches several sources out of the box.</p>
        <p>
          A SearXNG instance is a search engine you run yourself, usually on your own computer or
          server. If you already have one, paste its address here, for example{' '}
          <code>http://localhost:8080</code>.
        </p>
        <p>
          If you have Docker installed, the easiest way to get one is to run{' '}
          <code>docker compose up</code> in the SearNXG folder. That starts SearXNG on port 8080
          and connects it automatically. You may need to stop other apps using port 8000 first.
        </p>
        <p>
          You can browse public instances at{' '}
          <a href="https://searx.space/" target="_blank" rel="noreferrer">searx.space</a>,
          but many block automated requests. Your own instance is more reliable.
        </p>
      </div>
    </details>
  )
}
