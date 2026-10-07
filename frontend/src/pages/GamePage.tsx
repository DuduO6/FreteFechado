import { useEffect, useMemo, useState } from 'react'
import Board from '../components/Board'
import Dice from '../components/Dice'
import GameScreen from '../components/GameScreen'
import { loadBoard } from '../services/gameApi'
import { useLobbyStore } from '../store/lobbyStore'
import type { BoardDefinition, RollMoveResponse } from '../types/game'
import './GamePage.css'

const DICE_FRAME_INTERVALS = [65, 75, 90, 110, 140, 180, 220]
const MOVEMENT_STEP_DURATION = 280

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds))
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : 'Ocorreu um erro inesperado. Tente novamente.'
}

function GamePage() {
  const snapshot = useLobbyStore((state) => state.snapshot)
  const refreshGame = useLobbyStore((state) => state.refreshGame)
  const selectRoute = useLobbyStore((state) => state.selectRoute)
  const rollDice = useLobbyStore((state) => state.rollDice)
  const setSnapshot = useLobbyStore((state) => state.setSnapshot)
  const [board, setBoard] = useState<BoardDefinition | null>(null)
  const [animatedPositions, setAnimatedPositions] = useState<string[] | null>(null)
  const [diceFace, setDiceFace] = useState(1)
  const [isRolling, setIsRolling] = useState(false)
  const [isMoving, setIsMoving] = useState(false)
  const [isSelectingRoute, setIsSelectingRoute] = useState(false)
  const [error, setError] = useState('')

  const isBusy = isRolling || isMoving || isSelectingRoute
  const boardNodeIds = useMemo(
    () => new Set(board?.nodes.map((node) => node.id) ?? []),
    [board],
  )

  useEffect(() => {
    let isActive = true

    async function initialize() {
      try {
        const loadedBoard = await loadBoard()
        if (isActive) {
          setBoard(loadedBoard)
        }
        await refreshGame()
      } catch (loadError) {
        if (isActive) {
          setError(errorMessage(loadError))
        }
      }
    }

    void initialize()
    return () => {
      isActive = false
    }
  }, [refreshGame])

  if (!snapshot) {
    return (
      <GameScreen>
        <p className="game-load-error" role="alert">Nenhuma partida foi preparada.</p>
      </GameScreen>
    )
  }

  const activeSnapshot = snapshot
  const currentPlayer = activeSnapshot.players[activeSnapshot.currentPlayerIndex]
  const displayedPositions =
    animatedPositions ?? activeSnapshot.players.map((player) => player.position)

  async function animateDice(finalFace: number) {
    for (const interval of DICE_FRAME_INTERVALS) {
      let nextFace = Math.floor(Math.random() * 6) + 1
      if (nextFace === diceFace) {
        nextFace = (nextFace % 6) + 1
      }
      setDiceFace(nextFace)
      await delay(interval)
    }
    setDiceFace(finalFace)
  }

  async function animateMovement(response: RollMoveResponse) {
    const { movement } = response
    if (!movement.path.length) {
      throw new Error('O servidor respondeu sem o caminho da movimentação.')
    }
    for (const nodeId of movement.path) {
      if (!boardNodeIds.has(nodeId)) {
        throw new Error(`O servidor retornou uma posição inválida: ${nodeId}.`)
      }
      await delay(MOVEMENT_STEP_DURATION)
      setAnimatedPositions((currentPositions) =>
        (currentPositions ?? activeSnapshot.players.map((player) => player.position)).map(
          (position, index) =>
            index === movement.playerIndex ? nodeId : position,
        ),
      )
    }
  }

  async function handleRouteSelection(routeId: string) {
    if (isBusy) {
      return
    }
    setError('')
    setIsSelectingRoute(true)
    try {
      await selectRoute(routeId)
    } catch (routeError) {
      setError(errorMessage(routeError))
    } finally {
      setIsSelectingRoute(false)
    }
  }

  async function handleRoll() {
    if (isBusy || activeSnapshot.phase !== 'WAITING_FOR_ROLL') {
      return
    }

    setError('')
    setIsRolling(true)
    let response: RollMoveResponse | null = null
    try {
      response = await rollDice()
      await animateDice(response.movement.dice)
      setIsRolling(false)
      setIsMoving(true)
      setAnimatedPositions(activeSnapshot.players.map((player) => player.position))
      await animateMovement(response)
      setSnapshot(response.snapshot)
      setAnimatedPositions(null)
    } catch (rollError) {
      if (response) {
        setSnapshot(response.snapshot)
      }
      setError(errorMessage(rollError))
    } finally {
      setIsRolling(false)
      setIsMoving(false)
      setAnimatedPositions(null)
    }
  }

  return (
    <GameScreen className="game-page">
      <div className="game-layout">
        <header className="game-hud">
          <div>
            <span className="hud-label">Rodada</span>
            <strong>{activeSnapshot.currentRound} / {activeSnapshot.maxRounds}</strong>
          </div>
          <div>
            <span className="hud-label">Jogador atual</span>
            <strong>{currentPlayer.name}</strong>
          </div>
          <div>
            <span className="hud-label">Estado</span>
            <strong>
              {isRolling ? 'Lançando dado' : isMoving ? 'Em movimento' : 'Aguardando jogada'}
            </strong>
          </div>
        </header>

        {board ? (
          <Board
            board={board}
            players={activeSnapshot.players}
            positions={displayedPositions}
            currentPlayerIndex={activeSnapshot.currentPlayerIndex}
          />
        ) : (
          <div className="board-loading" aria-live="polite">Carregando mapa…</div>
        )}

        <section className="game-controls" aria-label="Controles da jogada">
          <Dice
            face={diceFace}
            isRolling={isRolling}
            onAssetError={() => setError('Não foi possível carregar uma face do dado.')}
          />

          <div className="turn-actions">
            {activeSnapshot.status === 'FINISHED' ? (
              <p className="game-finished">Partida encerrada após 15 rodadas.</p>
            ) : activeSnapshot.phase === 'WAITING_FOR_ROUTE' ? (
              <>
                <p>Escolha uma rota para {currentPlayer.name}:</p>
                <div className="route-options">
                  {activeSnapshot.availableRoutes.map((route) => (
                    <button
                      type="button"
                      key={route.id}
                      disabled={isBusy}
                      onClick={() => void handleRouteSelection(route.id)}
                    >
                      Ir para {route.destinationName}
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <button
                className="roll-button"
                type="button"
                disabled={isBusy || !board}
                onClick={() => void handleRoll()}
              >
                {isRolling ? 'Lançando…' : isMoving ? 'Movendo…' : 'Jogar dado'}
              </button>
            )}

            {error && <p className="game-action-error" role="alert">{error}</p>}
          </div>
        </section>
      </div>
    </GameScreen>
  )
}

export default GamePage
