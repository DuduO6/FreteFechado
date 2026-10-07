import axios from 'axios'
import type { GameSnapshot } from '../types/game'

export interface PlayerNamesResponse {
  ok: true
  players: string[]
  startingPlayerIndex: number
  snapshot: GameSnapshot
}

interface ApiErrorResponse {
  ok: false
  message?: string
}

export async function submitPlayerNames(
  playerNames: string[],
): Promise<PlayerNamesResponse> {
  try {
    const response = await axios.post<PlayerNamesResponse>(
      '/api/inicial/players/',
      { players: playerNames },
    )

    return response.data
  } catch (error) {
    if (axios.isAxiosError<ApiErrorResponse>(error)) {
      throw new Error(
        error.response?.data.message ??
          'Não foi possível conectar ao servidor. Tente novamente.',
      )
    }

    throw error
  }
}
