import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import {
  loadGame,
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
  setSnapshot: (snapshot: GameSnapshot) => void
  refreshGame: () => Promise<void>
  selectRoute: (routeId: string) => Promise<void>
  rollDice: () => Promise<RollMoveResponse>
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
