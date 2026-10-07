MIN_PLAYERS = 2
MAX_PLAYERS = 4
MAX_NAME_LENGTH = 40


class InvalidPlayerNames(ValueError):
    """Raised when the initial player list cannot start a valid game."""


def validate_player_names(players: object) -> list[str]:
    if not isinstance(players, list):
        raise InvalidPlayerNames('Envie os nomes em uma lista de jogadores.')

    if not MIN_PLAYERS <= len(players) <= MAX_PLAYERS:
        raise InvalidPlayerNames('Informe de 2 a 4 jogadores.')

    normalized_names: list[str] = []
    for name in players:
        if not isinstance(name, str) or not name.strip():
            raise InvalidPlayerNames('Todos os jogadores precisam de um nome.')

        normalized_name = name.strip()
        if len(normalized_name) > MAX_NAME_LENGTH:
            raise InvalidPlayerNames(
                f'Cada nome deve ter no máximo {MAX_NAME_LENGTH} caracteres.'
            )

        normalized_names.append(normalized_name)

    return normalized_names
