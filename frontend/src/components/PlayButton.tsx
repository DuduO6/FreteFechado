import playButton from './playButtom.png'
import './PlayButton.css'

interface PlayButtonProps {
  onClick: () => void
  disabled?: boolean
}

function PlayButton({ onClick, disabled = false }: PlayButtonProps) {
  return (
    <button
      className="play-button"
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label="Jogar"
    >
      <img src={playButton} alt="" />
    </button>
  )
}

export default PlayButton
