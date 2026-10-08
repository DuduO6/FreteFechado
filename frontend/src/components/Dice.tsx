import die1 from './dado/1.png'
import die2 from './dado/2.png'
import die3 from './dado/3.png'
import die4 from './dado/4.png'
import die5 from './dado/5.png'
import die6 from './dado/6.png'
import './Dice.css'

const DICE_FACES = [die1, die2, die3, die4, die5, die6] as const

interface DiceProps {
  face: number
  isRolling: boolean
  onAssetError: () => void
  variant?: 'control' | 'overlay'
}

function Dice({
  face,
  isRolling,
  onAssetError,
  variant = 'control',
}: DiceProps) {
  const source = DICE_FACES[face - 1]

  return (
    <div
      className={`dice dice--${variant}${isRolling ? ' dice--rolling' : ''}`}
    >
      <img
        src={source}
        alt={`Dado mostrando ${face}`}
        onError={onAssetError}
      />
    </div>
  )
}

export default Dice
