import Dice from './Dice'
import './DiceRollButton.css'

interface DiceRollButtonProps {
  face: number
  disabled: boolean
  onClick: () => void
  onAssetError: () => void
}

function DiceRollButton({
  face,
  disabled,
  onClick,
  onAssetError,
}: DiceRollButtonProps) {
  return (
    <button
      className="dice-roll-button"
      type="button"
      disabled={disabled}
      onClick={onClick}
      aria-label="Jogar dado"
    >
      <Dice
        face={face}
        isRolling={false}
        onAssetError={onAssetError}
      />
    </button>
  )
}

export default DiceRollButton
