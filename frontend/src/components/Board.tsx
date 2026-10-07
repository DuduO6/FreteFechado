import { useMemo, useState, type CSSProperties } from 'react'
import boardImage from './map/Mapa Rural Colorido de Tabuleiro.png'
import type { BoardDefinition, GamePlayer } from '../types/game'
import './Board.css'

const MARKER_COLORS = ['#e63f2e', '#237edb', '#f3b51b', '#7b45bf']
const MARKER_OFFSETS = [
  [-10, -10],
  [10, -10],
  [-10, 10],
  [10, 10],
]

interface BoardProps {
  board: BoardDefinition
  players: GamePlayer[]
  positions: string[]
  currentPlayerIndex: number
}

interface MarkerStyle extends CSSProperties {
  '--marker-color': string
  '--offset-x': string
  '--offset-y': string
}

function Board({ board, players, positions, currentPlayerIndex }: BoardProps) {
  const [imageFailed, setImageFailed] = useState(false)
  const nodesById = useMemo(
    () => new Map(board.nodes.map((node) => [node.id, node])),
    [board.nodes],
  )
  const invalidPosition = positions.find((position) => !nodesById.has(position))

  if (imageFailed) {
    return <p className="board-error" role="alert">Não foi possível carregar a imagem do mapa.</p>
  }

  if (invalidPosition) {
    return <p className="board-error" role="alert">Posição inválida recebida: {invalidPosition}.</p>
  }

  return (
    <div className="board" aria-label="Mapa da partida">
      <img
        className="board-image"
        src={boardImage}
        alt="Mapa rodoviário de Frete Fechado"
        onError={() => setImageFailed(true)}
      />

      {players.map((player, playerIndex) => {
        const position = positions[playerIndex]
        const node = nodesById.get(position)
        if (!node) {
          return null
        }
        const sameNodeSlot = positions
          .slice(0, playerIndex)
          .filter((nodeId) => nodeId === position).length
        const [offsetX, offsetY] = MARKER_OFFSETS[sameNodeSlot] ?? [0, 0]
        const style: MarkerStyle = {
          left: `${node.x}%`,
          top: `${node.y}%`,
          '--marker-color': MARKER_COLORS[playerIndex] ?? '#333',
          '--offset-x': `${offsetX}px`,
          '--offset-y': `${offsetY}px`,
        }

        return (
          <div
            className="player-marker-position"
            style={style}
            key={player.id}
            aria-label={`${player.name} em ${node.name ?? node.id}`}
          >
            <span
              className={`player-marker${
                playerIndex === currentPlayerIndex ? ' player-marker--current' : ''
              }`}
              title={player.name}
            >
              {playerIndex + 1}
            </span>
          </div>
        )
      })}
    </div>
  )
}

export default Board
