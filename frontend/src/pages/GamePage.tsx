import { useEffect, useMemo, useState } from 'react'
import Board from '../components/Board'
import Dice from '../components/Dice'
import DiceRollButton from '../components/DiceRollButton'
import GameScreen from '../components/GameScreen'
import PlayerInfoCard from '../components/PlayerInfoCard'
import ProblemCardModal from '../components/ProblemCardModal'
import { loadBoard } from '../services/gameApi'
import { useLobbyStore } from '../store/lobbyStore'
import type { BoardDefinition, RollMoveResponse } from '../types/game'
import './GamePage.css'

const DICE_FRAME_INTERVALS = [65, 75, 90, 110, 140, 180, 220]
const MOVEMENT_STEP_DURATION = 280
const DICE_REVEAL_DURATION = 480

type DiceOverlayPhase = 'hidden' | 'rolling' | 'revealing'

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
  const restartGame = useLobbyStore((state) => state.restartGame)
  const refuel = useLobbyStore((state) => state.refuel)
  const acknowledgeEvent = useLobbyStore((state) => state.acknowledgeEvent)
  const setSnapshot = useLobbyStore((state) => state.setSnapshot)
  const [board, setBoard] = useState<BoardDefinition | null>(null)
  const [animatedPositions, setAnimatedPositions] = useState<string[] | null>(null)
  const [diceFace, setDiceFace] = useState(1)
  const [isRolling, setIsRolling] = useState(false)
  const [diceOverlayPhase, setDiceOverlayPhase] =
    useState<DiceOverlayPhase>('hidden')
  const [isMoving, setIsMoving] = useState(false)
  const [isSelectingRoute, setIsSelectingRoute] = useState(false)
  const [isResolvingAction, setIsResolvingAction] = useState(false)
  const [error, setError] = useState('')

  const isBusy =
    diceOverlayPhase !== 'hidden' || isMoving || isSelectingRoute || isResolvingAction
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
    setDiceOverlayPhase('rolling')
    let response: RollMoveResponse | null = null
    try {
      response = await rollDice()
      await animateDice(response.movement.dice)
      setIsRolling(false)
      setDiceOverlayPhase('revealing')
      await delay(DICE_REVEAL_DURATION)
      setDiceOverlayPhase('hidden')
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
      setIsRolling(false)
      setDiceOverlayPhase('revealing')
      await delay(DICE_REVEAL_DURATION)
    } finally {
      setIsRolling(false)
      setDiceOverlayPhase('hidden')
      setIsMoving(false)
      setAnimatedPositions(null)
    }
  }

  async function handleRefuel(units: number) {
    if (isBusy) {
      return
    }
    setError('')
    setIsResolvingAction(true)
    try {
      await refuel(units)
    } catch (refuelError) {
      setError(errorMessage(refuelError))
    } finally {
      setIsResolvingAction(false)
    }
  }

  async function handleEventConfirmation() {
    if (isBusy) {
      return
    }
    setError('')
    setIsResolvingAction(true)
    try {
      await acknowledgeEvent()
    } catch (eventError) {
      setError(errorMessage(eventError))
    } finally {
      setIsResolvingAction(false)
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
          <button
            className="restart-button"
            type="button"
            disabled={isBusy}
            onClick={restartGame}
          >
            <span aria-hidden="true">↺</span>
            Recomeçar
          </button>
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

        <aside className="player-info-cards" aria-label="Informações dos jogadores">
          {Array.from({ length: 4 }, (_, slot) => (
            <PlayerInfoCard
              key={activeSnapshot.players[slot]?.id ?? `empty-${slot}`}
              player={activeSnapshot.players[slot]}
              slot={slot}
            />
          ))}
        </aside>

        <section
          className={`game-controls${
            activeSnapshot.phase === 'WAITING_FOR_ROUTE' ||
            activeSnapshot.phase === 'WAITING_FOR_REFUEL' ||
            activeSnapshot.status === 'FINISHED'
              ? ' game-controls--routes'
              : ' game-controls--dice'
          }`}
          aria-label="Controles da jogada"
        >
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
            ) : activeSnapshot.phase === 'WAITING_FOR_REFUEL' && activeSnapshot.refuelOffer ? (
              <>
                <p>
                  {activeSnapshot.refuelOffer.reason === 'OUT_OF_FUEL'
                    ? 'O combustível acabou. Abasteça ao menos 1 nível para continuar.'
                    : `Abastecer ${currentPlayer.name}? Cada nível custa R$ ${activeSnapshot.refuelOffer.unitPrice}.`}
                </p>
                <div className="route-options refuel-options">
                  {!activeSnapshot.refuelOffer.required && (
                    <button type="button" disabled={isBusy} onClick={() => void handleRefuel(0)}>
                      Não abastecer
                    </button>
                  )}
                  {Array.from(
                    { length: activeSnapshot.refuelOffer.maxFuel - activeSnapshot.refuelOffer.fuel },
                    (_, index) => index + 1,
                  ).map((units) => (
                    <button type="button" key={units} disabled={isBusy} onClick={() => void handleRefuel(units)}>
                      +{units} {units === 1 ? 'nível' : 'níveis'} — R$ {units * activeSnapshot.refuelOffer!.unitPrice}
                    </button>
                  ))}
                </div>
              </>
            ) : activeSnapshot.phase === 'WAITING_FOR_EVENT' ? (
              <p>Revele a carta de problema para concluir a jogada.</p>
            ) : (
              <DiceRollButton
                face={diceFace}
                disabled={isBusy || !board}
                onClick={() => void handleRoll()}
                onAssetError={() =>
                  setError('Não foi possível carregar uma face do dado.')
                }
              />
            )}

            {error && <p className="game-action-error" role="alert">{error}</p>}
          </div>
        </section>

        {diceOverlayPhase !== 'hidden' && (
          <div
            className={`dice-roll-overlay dice-roll-overlay--${diceOverlayPhase}`}
            role="status"
            aria-live="polite"
            aria-label={isRolling ? 'Lançando o dado' : `Resultado: ${diceFace}`}
          >
            <div className="dice-roll-overlay__stage">
              <Dice
                face={diceFace}
                isRolling={isRolling}
                variant="overlay"
                onAssetError={() =>
                  setError('Não foi possível carregar uma face do dado.')
                }
              />
            </div>
          </div>
        )}

        {activeSnapshot.pendingProblemCard && !isMoving && diceOverlayPhase === 'hidden' && (
          <ProblemCardModal
            key={`${activeSnapshot.pendingProblemCard.playerIndex}-${activeSnapshot.pendingProblemCard.id}`}
            card={activeSnapshot.pendingProblemCard}
            playerName={activeSnapshot.players[activeSnapshot.pendingProblemCard.playerIndex].name}
            isConfirming={isResolvingAction}
            onConfirm={() => void handleEventConfirmation()}
          />
        )}
      </div>
    </GameScreen>
  )
}

export default GamePage
