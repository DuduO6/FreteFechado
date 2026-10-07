import { useState, type FormEvent } from 'react'
import GameScreen from '../components/GameScreen'
import PlayButton from '../components/PlayButton'
import logo from '../components/logo.png'
import {
  submitPlayerNames,
  type PlayerNamesResponse,
} from '../services/initialApi'
import './InicialPage.css'

const MIN_PLAYERS = 2
const MAX_PLAYERS = 4

type PageStep = 'landing' | 'players'

interface InicialPageProps {
  onPlayersConfirmed: (response: PlayerNamesResponse) => void
}

function InicialPage({ onPlayersConfirmed }: InicialPageProps) {
  const [step, setStep] = useState<PageStep>('landing')
  const [playerNames, setPlayerNames] = useState(['', ''])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  function updatePlayerName(index: number, value: string) {
    setPlayerNames((currentNames) =>
      currentNames.map((name, currentIndex) =>
        currentIndex === index ? value : name,
      ),
    )
  }

  function addPlayer() {
    if (playerNames.length < MAX_PLAYERS) {
      setPlayerNames((currentNames) => [...currentNames, ''])
    }
  }

  function removePlayer(index: number) {
    if (playerNames.length > MIN_PLAYERS) {
      setPlayerNames((currentNames) =>
        currentNames.filter((_, currentIndex) => currentIndex !== index),
      )
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      const response = await submitPlayerNames(playerNames)
      onPlayersConfirmed(response)
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Não foi possível enviar os nomes. Tente novamente.',
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <GameScreen className="initial-page">
      <div className={`initial-content initial-content--${step}`}>
        <div className="game-logo" aria-hidden="true">
          <img src={logo} alt="" />
        </div>
        <h1 className="visually-hidden">Frete Fechado</h1>

        {step === 'landing' && (
          <PlayButton onClick={() => setStep('players')} />
        )}

        {step === 'players' && (
          <section
            className="game-panel player-panel"
            aria-labelledby="player-panel-title"
          >
            <h2 id="player-panel-title">Quem vai jogar?</h2>
            <p>Informe de 2 a 4 nomes para preparar a partida.</p>

            <form onSubmit={handleSubmit}>
              <div className="player-fields">
                {playerNames.map((name, index) => (
                  <div className="player-field" key={index}>
                    <label htmlFor={`player-${index}`}>
                      Jogador {index + 1}
                    </label>
                    <div className="player-input-row">
                      <input
                        id={`player-${index}`}
                        name={`player-${index}`}
                        value={name}
                        onChange={(event) =>
                          updatePlayerName(index, event.target.value)
                        }
                        maxLength={40}
                        autoComplete="off"
                        required
                      />
                      {playerNames.length > MIN_PLAYERS && (
                        <button
                          className="remove-player"
                          type="button"
                          onClick={() => removePlayer(index)}
                          aria-label={`Remover jogador ${index + 1}`}
                        >
                          ×
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {error && (
                <p className="form-message form-message--error" role="alert">
                  {error}
                </p>
              )}

              <div className="player-actions">
                <button
                  className="secondary-action"
                  type="button"
                  onClick={addPlayer}
                  disabled={playerNames.length === MAX_PLAYERS}
                >
                  Adicionar jogador
                </button>
                <button
                  className="primary-action"
                  type="submit"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? 'Enviando…' : 'Confirmar nomes'}
                </button>
              </div>
            </form>
          </section>
        )}
      </div>
    </GameScreen>
  )
}

export default InicialPage
