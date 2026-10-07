import InicialPage from './pages/InicialPage'
import GamePage from './pages/GamePage'
import WaitingRoomPage from './pages/WaitingRoomPage'
import { useLobbyStore } from './store/lobbyStore'

function App() {
  const phase = useLobbyStore((state) => state.phase)
  const players = useLobbyStore((state) => state.players)
  const startingPlayerIndex = useLobbyStore(
    (state) => state.startingPlayerIndex,
  )
  const snapshot = useLobbyStore((state) => state.snapshot)
  const prepareLobby = useLobbyStore((state) => state.prepareLobby)
  const startGame = useLobbyStore((state) => state.startGame)

  if (phase === 'waiting' && startingPlayerIndex !== null) {
    return (
      <WaitingRoomPage
        players={players}
        startingPlayerIndex={startingPlayerIndex}
        onStartGame={startGame}
      />
    )
  }

  if (phase === 'playing' && snapshot) {
    return <GamePage />
  }

  return (
    <InicialPage
      onPlayersConfirmed={prepareLobby}
    />
  )
}

export default App
