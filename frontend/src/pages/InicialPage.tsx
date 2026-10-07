import { useState, type FormEvent } from 'react'
import logo from '../components/logo.png'
import playButton from '../components/playButtom.png'
import { submitPlayerNames } from '../services/initialApi'
import './InicialPage.css'

const MIN_PLAYERS = 2
const MAX_PLAYERS = 4

type PageStep = 'landing' | 'players' | 'ready'

function InicialPage() {
  const [step, setStep] = useState<PageStep>('landing')
  const [playerNames, setPlayerNames] = useState(['', ''])
  const [confirmedNames, setConfirmedNames] = useState<string[]>([])
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
      setConfirmedNames(response.players)
      setStep('ready')
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
    <main className="initial-page">
      <div className={`initial-content initial-content--${step}`}>
        <div className="game-logo" aria-hidden="true">
          <img src={logo} alt="" />
        </div>
        <h1 className="visually-hidden">Frete Fechado</h1>

        {step === 'landing' && (
          <button
            className="play-button"
            type="button"
            onClick={() => setStep('players')}
            aria-label="Jogar"
          >
            <img src={playButton} alt="" />
          </button>
        )}

        {step === 'players' && (
          <section className="player-panel" aria-labelledby="player-panel-title">
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

        {step === 'ready' && (
          <section className="player-panel player-panel--ready" aria-live="polite">
            <h2>Jogadores prontos!</h2>
            <p>{confirmedNames.join(', ')}</p>
            <button
              className="secondary-action"
              type="button"
              onClick={() => setStep('players')}
            >
              Editar nomes
            </button>
          </section>
        )}
      </div>
    </main>
  )
}

export default InicialPage
