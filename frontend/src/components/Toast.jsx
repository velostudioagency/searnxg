import React from 'react'
import { motion, useReducedMotion } from 'motion/react'
import { Icon } from './Icons.jsx'

export default function Toast({ toast, onClose }) {
  const reduce = useReducedMotion()
  if (!toast) return null
  return (
    <motion.div
      key={toast.message}
      className={`toast ${toast.type || 'info'}`}
      role="status"
      initial={reduce ? false : { opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={reduce ? { opacity: 0 } : { opacity: 0, y: 8 }}
      transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
    >
      <Icon name={toast.type === 'error' ? 'info' : 'check'} size={16} />
      <span>{toast.message}</span>
      <button className="toast-close" onClick={onClose} aria-label="Dismiss">
        <Icon name="close" size={14} />
      </button>
    </motion.div>
  )
}
