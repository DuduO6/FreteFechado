import blueTruck from './trucks/blue.png'
import greenTruck from './trucks/green.png'
import redTruck from './trucks/red.png'
import yellowTruck from './trucks/yellow.png'
import type { GamePlayer } from '../types/game'

const TRUCK_BY_COLOR: Record<string, string> = {
  '#e63f2e': redTruck,
  '#237edb': blueTruck,
  '#f3b51b': yellowTruck,
  '#7b45bf': greenTruck,
  '#3ba447': greenTruck,
}

const TRUCKS_BY_TURN = [redTruck, blueTruck, yellowTruck, greenTruck]

export function getPlayerTruck(
  player: Partial<Pick<GamePlayer, 'color' | 'turnOrder'>>,
): string {
  const color = player.color?.toLowerCase()
  const turnIndex = typeof player.turnOrder === 'number' ? player.turnOrder - 1 : -1

  return (
    (color ? TRUCK_BY_COLOR[color] : undefined) ??
    TRUCKS_BY_TURN[turnIndex] ??
    redTruck
  )
}
