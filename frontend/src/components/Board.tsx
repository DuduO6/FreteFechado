import { useMemo, useState, type CSSProperties } from 'react'
import boardImage from './map/Mapa Rural Colorido de Tabuleiro.png'
import problemImage from './map/problema.png'
import fuelTickImage from './spr_space_fuel_tick.png'
import stationImage from './spr_space_station.png'
import { getPlayerTruck } from './truckAssets'
import type { BoardDefinition, GamePlayer } from '../types/game'
import './Board.css'

const MARKER_OFFSETS = [
  [-15, -15],
  [15, -15],
  [-15, 15],
  [15, 15],
]

interface BoardProps {
  board: BoardDefinition
  players: GamePlayer[]
  positions: string[]
  currentPlayerIndex: number
}

interface MarkerStyle extends CSSProperties {
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

      {board.nodes.map((node) => {
        const isStation = node.tags?.includes('FUEL_STATION')
        const isProblem = node.tags?.includes('PROBLEM')
        if (!isStation && !isProblem) {
          return null
        }
        return (
          <div
            className="board-special-space"
            key={`special-${node.id}`}
            style={{ left: `${node.x}%`, top: `${node.y}%` }}
            aria-label={isStation ? 'Posto de combustível' : 'Casa de problema'}
          >
            {isStation && (
              <>
                <img className="board-special-space__station" src={stationImage} alt="" />
                <img className="board-special-space__fuel" src={fuelTickImage} alt="" />
              </>
            )}
            {isProblem && (
              <img className="board-special-space__problem" src={problemImage} alt="" />
            )}
          </div>
        )
      })}

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
            <img
              className={`player-marker${
                playerIndex === currentPlayerIndex ? ' player-marker--current' : ''
              }`}
              src={getPlayerTruck(player)}
              alt=""
              title={player.name}
            />
          </div>
        )
      })}
    </div>
  )
}

export default Board
