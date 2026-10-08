export type BoardNodeType = 'CITY' | 'HIGHWAY' | 'DIRT_ROAD'
export type BoardNodeTag = 'FUEL_STATION' | 'PROBLEM'

export interface BoardNode {
  id: string
  x: number
  y: number
  type: BoardNodeType
  name?: string
  tags?: BoardNodeTag[]
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
  turnOrder: number
  balance: number
  hasValidContract: boolean
  color: string
  spacesTraveled: number
  fuel: number
  fuelDistance: number
  fuelVoucher: boolean
  nextMovePenalty: number
  isCurrentPlayer: boolean
  turnsUntilTurn: number
}

export interface AvailableRoute {
  id: string
  name: string
  destinationId: string
  destinationName: string
}

export type GameStatus = 'PLAYING' | 'FINISHED'
export type TurnPhase =
  | 'WAITING_FOR_ROUTE'
  | 'WAITING_FOR_ROLL'
  | 'WAITING_FOR_REFUEL'
  | 'WAITING_FOR_EVENT'
  | 'FINISHED'

export interface RefuelOffer {
  playerIndex: number
  reason: 'STATION' | 'OUT_OF_FUEL'
  required: boolean
  fuel: number
  maxFuel: number
  unitPrice: number
}

export type ProblemCardId =
  | 'FLAT_TIRE'
  | 'MECHANICAL_REPAIR'
  | 'MANDATORY_DETOUR'
  | 'INSURANCE_ASSISTANCE'
  | 'FUEL_VOUCHER'

export interface ProblemCard {
  id: ProblemCardId
  title: string
  description: string
  effect: {
    balanceDelta?: number
    nextMovePenalty?: number
    fuelVoucher?: boolean
  }
  playerIndex: number
}

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
  refuelOffer: RefuelOffer | null
  pendingProblemCard: ProblemCard | null
}

export interface MovementResult {
  playerIndex: number
  dice: number
  movementSteps: number
  appliedPenalty: number
  from: string
  path: string[]
  to: string
  balanceDelta: number
  ranOutOfFuel: boolean
}

export interface RollMoveResponse {
  ok: true
  snapshot: GameSnapshot
  movement: MovementResult
}
