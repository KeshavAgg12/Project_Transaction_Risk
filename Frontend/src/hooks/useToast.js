import { useState } from 'react'

export function useToast(duration = 2200) {
  const [message, setMessage] = useState('')

  const showToast = (text) => {
    setMessage(text)
    setTimeout(() => setMessage(''), duration)
  }
  return { message, showToast }
}
