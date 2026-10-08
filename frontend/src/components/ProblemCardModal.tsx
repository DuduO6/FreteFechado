import { useState } from 'react'
import insuranceCard from './cartas/assistência da seguradora.png'
import cardBack from './cartas/cartasDePrenda.png'
import detourCard from './cartas/desvio obrigatório.png'
import flatTireCard from './cartas/pneu furado.png'
import repairCard from './cartas/reparo mecânico na estrada.png'
import fuelVoucherCard from './cartas/vale-combustível.png'
import type { ProblemCard, ProblemCardId } from '../types/game'
import './ProblemCardModal.css'

const CARD_IMAGES: Record<ProblemCardId, string> = {
  FLAT_TIRE: flatTireCard,
  MECHANICAL_REPAIR: repairCard,
  MANDATORY_DETOUR: detourCard,
  INSURANCE_ASSISTANCE: insuranceCard,
  FUEL_VOUCHER: fuelVoucherCard,
}

interface ProblemCardModalProps {
  card: ProblemCard
  playerName: string
  isConfirming: boolean
  onConfirm: () => void
}

function ProblemCardModal({
  card,
  playerName,
  isConfirming,
  onConfirm,
}: ProblemCardModalProps) {
  const [isRevealed, setIsRevealed] = useState(false)

  return (
    <div className="problem-card-overlay" role="dialog" aria-modal="true" aria-labelledby="problem-card-title">
      <div className="problem-card-modal">
        <p id="problem-card-title">
          {isRevealed ? card.title : `${playerName} encontrou um problema!`}
        </p>
        <button
          className={`problem-card-flip${isRevealed ? ' is-revealed' : ''}`}
          type="button"
          disabled={isRevealed}
          onClick={() => setIsRevealed(true)}
          aria-label={isRevealed ? card.title : 'Revelar carta de problema'}
        >
          <span className="problem-card-flip__inner">
            <span className="problem-card-flip__face problem-card-flip__back">
              <img src={cardBack} alt="Monte de cartas de problema" />
            </span>
            <span className="problem-card-flip__face problem-card-flip__front">
              <img src={CARD_IMAGES[card.id]} alt={card.title} />
            </span>
          </span>
        </button>
        {isRevealed ? (
          <div className="problem-card-result">
            <span>{card.description}</span>
            <button type="button" disabled={isConfirming} onClick={onConfirm}>
              {isConfirming ? 'Confirmando…' : 'Continuar'}
            </button>
          </div>
        ) : (
          <span className="problem-card-hint">Clique no monte para revelar a carta</span>
        )}
      </div>
    </div>
  )
}

export default ProblemCardModal
