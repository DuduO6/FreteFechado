import type { ReactNode } from 'react'
import './GameScreen.css'

interface GameScreenProps {
  children: ReactNode
  className?: string
}

function GameScreen({ children, className = '' }: GameScreenProps) {
  const classes = ['game-screen', className].filter(Boolean).join(' ')

  return <main className={classes}>{children}</main>
}

export default GameScreen
