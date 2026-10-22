import { useState } from 'react'
import type { Contract, ContractImageKey } from '../types/game'
import contractBack from './cartas/cartaDeContrato.png'
import bhNorteAtalho from './contratos/bh_norte_atalho.png'
import bhNorteRodovia from './contratos/bh_norte_rodovia.png'
import bhZonaMata from './contratos/bh_zona_da_mata.png'
import bhZonaMata2 from './contratos/bh_zona_da_mata_2.png'
import sulBh from './contratos/sul_bh.png'
import sulZonaMata from './contratos/sul_zona_da_mata.png'
import trianguloBh from './contratos/triangulo_bh.png'
import trianguloSul from './contratos/triangulo_sul.png'
import zonaMataBh from './contratos/zona_da_mata_bh.png'
import './ContractCardModal.css'

const CONTRACT_IMAGES: Record<ContractImageKey, string> = {
  bh_norte_atalho: bhNorteAtalho,
  bh_norte_rodovia: bhNorteRodovia,
  bh_zona_da_mata: bhZonaMata,
  bh_zona_da_mata_2: bhZonaMata2,
  sul_bh: sulBh,
  sul_zona_da_mata: sulZonaMata,
  triangulo_bh: trianguloBh,
  triangulo_sul: trianguloSul,
  zona_da_mata_bh: zonaMataBh,
}

interface ContractCardModalProps {
  contracts: Contract[]
  playerName: string
  canAccept: boolean
  isAccepting: boolean
  onAccept: (contractId: string) => void
  onClose: () => void
}

function ContractCardModal({
  contracts,
  playerName,
  canAccept,
  isAccepting,
  onAccept,
  onClose,
}: ContractCardModalProps) {
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [isRevealed, setIsRevealed] = useState(false)
  const contract = contracts[selectedIndex]

  if (!contract) {
    return null
  }

  function selectRelative(offset: number) {
    setSelectedIndex((current) =>
      (current + offset + contracts.length) % contracts.length,
    )
    setIsRevealed(false)
  }

  return (
    <div className="contract-card-overlay" role="dialog" aria-modal="true" aria-labelledby="contract-card-title">
      <div className="contract-card-modal">
        <p id="contract-card-title">
          {isRevealed
            ? contract.title
            : canAccept
              ? `${playerName}, escolha seu próximo frete`
              : `Contrato ativo de ${playerName}`}
        </p>

        <button
          className={`contract-card-flip${isRevealed ? ' is-revealed' : ''}`}
          type="button"
          disabled={isRevealed}
          onClick={() => setIsRevealed(true)}
          aria-label={isRevealed ? contract.title : 'Revelar carta de contrato'}
        >
          <span className="contract-card-flip__inner">
            <span className="contract-card-flip__face contract-card-flip__back">
              <img src={contractBack} alt="Monte de cartas de contrato" />
            </span>
            <span className="contract-card-flip__face contract-card-flip__front">
              <img src={CONTRACT_IMAGES[contract.imageKey]} alt={contract.title} />
            </span>
          </span>
        </button>

        {isRevealed ? (
          <div className="contract-card-result">
            <span>{contract.cargo} · pagamento de R$ {contract.reward}</span>
            {contracts.length > 1 && canAccept && (
              <div className="contract-card-navigation" aria-label="Navegar pelos contratos">
                <button type="button" disabled={isAccepting} onClick={() => selectRelative(-1)}>
                  ← Anterior
                </button>
                <span>{selectedIndex + 1} / {contracts.length}</span>
                <button type="button" disabled={isAccepting} onClick={() => selectRelative(1)}>
                  Próximo →
                </button>
              </div>
            )}
            <div className="contract-card-actions">
              <button className="contract-card-actions__secondary" type="button" disabled={isAccepting} onClick={onClose}>
                Fechar
              </button>
              {canAccept && (
                <button type="button" disabled={isAccepting} onClick={() => onAccept(contract.id)}>
                  {isAccepting ? 'Aceitando…' : 'Aceitar contrato'}
                </button>
              )}
            </div>
          </div>
        ) : (
          <span className="contract-card-hint">Clique no monte para revelar a carta</span>
        )}
      </div>
    </div>
  )
}

export default ContractCardModal
