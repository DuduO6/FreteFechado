import type { CSSProperties } from 'react'
import infoCardImage from './map/InfoCard.png'
import fuelTickImage from './spr_space_fuel_tick.png'
import { getPlayerTruck } from './truckAssets'
import currentPlayerImage from './trucks/playerAtual.png'
import type { GamePlayer } from '../types/game'
import './PlayerInfoCard.css'

const currencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
  maximumFractionDigits: 0,
})

interface PlayerInfoCardProps {
  player?: GamePlayer
  slot: number
}

function PlayerInfoCard({ player, slot }: PlayerInfoCardProps) {
  const balance =
    typeof player?.balance === 'number'
      ? currencyFormatter.format(player.balance)
      : '—'

  return (
    <article
      className={`player-info-card${
        player ? '' : ' player-info-card--empty'
      }${player?.isCurrentPlayer ? ' player-info-card--current' : ''}`}
      style={{ '--player-color': player?.color ?? '#292929' } as CSSProperties}
      aria-label={player ? `Informações de ${player.name}` : `Espaço vazio ${slot + 1}`}
    >
      <img className="player-info-card__image" src={infoCardImage} alt="" />

      {player?.isCurrentPlayer && (
        <img
          className="player-info-card__current-indicator"
          src={currentPlayerImage}
          title="Jogador atual"
          aria-label="Jogador atual"
        />
      )}

      <header className="player-info-card__header">
        <strong>{player?.name ?? 'Sem jogador'}</strong>
      </header>

      <dl className="player-info-card__details">
        <div className="player-info-card__field player-info-card__field--turn">
          <dt>Turno</dt>
          <dd>
            {player && (
              <img
                className="player-info-card__truck"
                src={getPlayerTruck(player)}
                alt=""
                title={player.color}
              />
            )}
            <span>{player?.turnOrder ?? '—'}</span>
          </dd>
        </div>
        <div className="player-info-card__field player-info-card__field--contract">
          <dt>Contrato</dt>
          <dd>{player ? (player.hasValidContract ? 'Sim' : 'Não') : '—'}</dd>
        </div>
        <div className="player-info-card__field player-info-card__field--waiting">
          <dt>Combustível</dt>
          <dd className="player-info-card__fuel" aria-label={`${player?.fuel ?? 0} de 5 níveis de combustível`}>
            {Array.from({ length: 5 }, (_, index) => (
              <img
                key={index}
                className={index < (player?.fuel ?? 0) ? '' : 'is-empty'}
                src={fuelTickImage}
                alt=""
              />
            ))}
          </dd>
        </div>
        <div className="player-info-card__field player-info-card__field--balance">
          <dt>Saldo</dt>
          <dd>{balance}</dd>
        </div>
      </dl>
    </article>
  )
}

export default PlayerInfoCard
