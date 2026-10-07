export type BoardNodeType = 'CITY' | 'HIGHWAY' | 'DIRT_ROAD'

export interface BoardNode {
  id: string
  x: number
  y: number
  type: BoardNodeType
  name?: string
}

export interface BoardRoute {
  id: string
  name: string
  nodes: string[]
}

export interface BoardDefinition {
  source: string
  nodes: BoardNode[]
  routes: BoardRoute[]
}

export interface GamePlayer {
  id: string
  name: string
  position: string
  activeRouteId: string | null
  routeDirection: number | null
}

export interface AvailableRoute {
  id: string
  name: string
  destinationId: string
  destinationName: string
}

export type GameStatus = 'PLAYING' | 'FINISHED'
export type TurnPhase = 'WAITING_FOR_ROUTE' | 'WAITING_FOR_ROLL' | 'FINISHED'

export interface GameSnapshot {
  gameId: string
  status: GameStatus
  phase: TurnPhase
  currentRound: number
  maxRounds: number
  currentPlayerIndex: number
  turnsPlayedInRound: number
  players: GamePlayer[]
  availableRoutes: AvailableRoute[]
}

export interface MovementResult {
  playerIndex: number
  dice: number
  from: string
  path: string[]
  to: string
}

export interface RollMoveResponse {
  ok: true
  snapshot: GameSnapshot
  movement: MovementResult
}
