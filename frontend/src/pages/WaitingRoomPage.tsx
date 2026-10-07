import GameScreen from '../components/GameScreen'
import PlayButton from '../components/PlayButton'
import './WaitingRoomPage.css'

interface WaitingRoomPageProps {
  players: string[]
  startingPlayerIndex: number
  onStartGame: () => void
}

function WaitingRoomPage({
  players,
  startingPlayerIndex,
  onStartGame,
}: WaitingRoomPageProps) {
  const startingPlayer = players[startingPlayerIndex]

  return (
    <GameScreen className="waiting-room-page">
      <section className="game-panel waiting-room-panel" aria-labelledby="room-title">
        <p className="waiting-room-kicker">Tudo pronto para partir</p>
        <h1 id="room-title">Sala de espera</h1>
        <p className="waiting-room-description">
          Confira os participantes e quem fará a primeira jogada.
        </p>

        <ol className="player-list" aria-label="Jogadores participantes">
          {players.map((player, index) => {
            const isStartingPlayer = index === startingPlayerIndex

            return (
              <li
                className={`player-list-item${
                  isStartingPlayer ? ' player-list-item--starting' : ''
                }`}
                key={`${player}-${index}`}
              >
                <span className="player-position" aria-hidden="true">
                  {index + 1}
                </span>
                <span className="player-name">{player}</span>
                {isStartingPlayer && (
                  <span className="starting-badge">Começa</span>
                )}
              </li>
            )
          })}
        </ol>

        <p className="starting-player-summary" aria-live="polite">
          <strong>{startingPlayer}</strong> inicia a partida.
        </p>

        <PlayButton onClick={onStartGame} />
      </section>
    </GameScreen>
  )
}

export default WaitingRoomPage
