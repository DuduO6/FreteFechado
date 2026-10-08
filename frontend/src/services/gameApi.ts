import axios from 'axios'
import type {
  BoardDefinition,
  GameSnapshot,
  RollMoveResponse,
} from '../types/game'

interface ApiErrorResponse {
  ok: false
  code?: string
  message?: string
}

interface BoardResponse {
  ok: true
  board: BoardDefinition
}

interface SnapshotResponse {
  ok: true
  snapshot: GameSnapshot
}

function requestMessage(error: unknown, fallback: string): Error {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    return new Error(error.response?.data.message ?? fallback)
  }
  return error instanceof Error ? error : new Error(fallback)
}

export async function loadBoard(): Promise<BoardDefinition> {
  try {
    const response = await axios.get<BoardResponse>('/api/inicial/board/')
    return response.data.board
  } catch (error) {
    throw requestMessage(error, 'Não foi possível carregar o mapa.')
  }
}

export async function loadGame(gameId: string): Promise<GameSnapshot> {
  try {
    const response = await axios.get<SnapshotResponse>(
      `/api/inicial/games/${gameId}/`,
    )
    return response.data.snapshot
  } catch (error) {
    throw requestMessage(error, 'Não foi possível carregar a partida.')
  }
}

export async function selectGameRoute(
  gameId: string,
  routeId: string,
  expectedPlayerIndex: number,
  expectedRound: number,
): Promise<GameSnapshot> {
  try {
    const response = await axios.post<SnapshotResponse>(
      `/api/inicial/games/${gameId}/route/`,
      { routeId, expectedPlayerIndex, expectedRound },
    )
    return response.data.snapshot
  } catch (error) {
    throw requestMessage(error, 'Não foi possível selecionar a rota.')
  }
}

export async function rollAndMove(
  gameId: string,
  expectedPlayerIndex: number,
  expectedRound: number,
): Promise<RollMoveResponse> {
  try {
    const response = await axios.post<RollMoveResponse>(
      `/api/inicial/games/${gameId}/roll/`,
      { expectedPlayerIndex, expectedRound },
    )
    return response.data
  } catch (error) {
    throw requestMessage(error, 'Não foi possível jogar o dado.')
  }
}

export async function refuelGame(
  gameId: string,
  units: number,
  expectedPlayerIndex: number,
  expectedRound: number,
): Promise<GameSnapshot> {
  try {
    const response = await axios.post<SnapshotResponse>(
      `/api/inicial/games/${gameId}/refuel/`,
      { units, expectedPlayerIndex, expectedRound },
    )
    return response.data.snapshot
  } catch (error) {
    throw requestMessage(error, 'Não foi possível concluir o abastecimento.')
  }
}

export async function acknowledgeProblemEvent(
  gameId: string,
  expectedPlayerIndex: number,
  expectedRound: number,
): Promise<GameSnapshot> {
  try {
    const response = await axios.post<SnapshotResponse>(
      `/api/inicial/games/${gameId}/event/acknowledge/`,
      { expectedPlayerIndex, expectedRound },
    )
    return response.data.snapshot
  } catch (error) {
    throw requestMessage(error, 'Não foi possível concluir o evento.')
  }
}
