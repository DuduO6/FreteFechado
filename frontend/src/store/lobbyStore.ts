import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import {
  acknowledgeProblemEvent,
  loadGame,
  refuelGame,
  rollAndMove,
  selectGameRoute,
} from '../services/gameApi'
import type { PlayerNamesResponse } from '../services/initialApi'
import type { GameSnapshot, RollMoveResponse } from '../types/game'

type LobbyPhase = 'setup' | 'waiting' | 'playing'

interface LobbyState {
  phase: LobbyPhase
  players: string[]
  startingPlayerIndex: number | null
  snapshot: GameSnapshot | null
  prepareLobby: (response: PlayerNamesResponse) => void
  startGame: () => void
  restartGame: () => void
  setSnapshot: (snapshot: GameSnapshot) => void
  refreshGame: () => Promise<void>
  selectRoute: (routeId: string) => Promise<void>
  rollDice: () => Promise<RollMoveResponse>
  refuel: (units: number) => Promise<void>
  acknowledgeEvent: () => Promise<void>
}

export const useLobbyStore = create<LobbyState>()(
  persist(
    (set, get) => ({
      phase: 'setup',
      players: [],
      startingPlayerIndex: null,
      snapshot: null,
      prepareLobby: (response) =>
        set({
          phase: 'waiting',
          players: response.players,
          startingPlayerIndex: response.startingPlayerIndex,
          snapshot: response.snapshot,
        }),
      startGame: () => set({ phase: 'playing' }),
      restartGame: () =>
        set({
          phase: 'setup',
          players: [],
          startingPlayerIndex: null,
          snapshot: null,
        }),
      setSnapshot: (snapshot) => set({ snapshot }),
      refreshGame: async () => {
        const gameId = get().snapshot?.gameId
        if (!gameId) {
          throw new Error('Nenhuma partida foi preparada.')
        }
        set({ snapshot: await loadGame(gameId) })
      },
      selectRoute: async (routeId) => {
        const snapshot = get().snapshot
        if (!snapshot) {
          throw new Error('Nenhuma partida foi preparada.')
        }
        const nextSnapshot = await selectGameRoute(
          snapshot.gameId,
          routeId,
          snapshot.currentPlayerIndex,
          snapshot.currentRound,
        )
        set({ snapshot: nextSnapshot })
      },
      rollDice: async () => {
        const snapshot = get().snapshot
        if (!snapshot) {
          throw new Error('Nenhuma partida foi preparada.')
        }
        return rollAndMove(
          snapshot.gameId,
          snapshot.currentPlayerIndex,
          snapshot.currentRound,
        )
      },
      refuel: async (units) => {
        const snapshot = get().snapshot
        if (!snapshot) {
          throw new Error('Nenhuma partida foi preparada.')
        }
        const nextSnapshot = await refuelGame(
          snapshot.gameId,
          units,
          snapshot.currentPlayerIndex,
          snapshot.currentRound,
        )
        set({ snapshot: nextSnapshot })
      },
      acknowledgeEvent: async () => {
        const snapshot = get().snapshot
        if (!snapshot) {
          throw new Error('Nenhuma partida foi preparada.')
        }
        const nextSnapshot = await acknowledgeProblemEvent(
          snapshot.gameId,
          snapshot.currentPlayerIndex,
          snapshot.currentRound,
        )
        set({ snapshot: nextSnapshot })
      },
    }),
    {
      name: 'frete-fechado-game',
      partialize: (state) => ({
        phase: state.phase,
        players: state.players,
        startingPlayerIndex: state.startingPlayerIndex,
        snapshot: state.snapshot,
      }),
    },
  ),
)
