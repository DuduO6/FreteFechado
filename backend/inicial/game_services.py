from random import SystemRandom
from typing import Protocol

from django.db import transaction

from .board import get_node, get_route, get_routes_from_city
from .models import GameSession


MAX_ROUNDS = 15
INITIAL_NODE_ID = 'CITY_BH'
D6_SIDES = 6


class GameActionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class DiceSource(Protocol):
    def randrange(self, start: int, stop: int, /) -> int: ...


class DiceRoller:
    def __init__(self, random_source: DiceSource | None = None) -> None:
        self.random_source = random_source or SystemRandom()

    def roll(self, sides: int = D6_SIDES) -> int:
        if sides < 2:
            raise ValueError('O dado precisa ter pelo menos duas faces.')
        return self.random_source.randrange(1, sides + 1)


def create_game_session(
    player_names: list[str],
    starting_player_index: int,
) -> GameSession:
    players = [
        {
            'id': f'player-{index + 1}',
            'name': name,
            'position': INITIAL_NODE_ID,
            'activeRouteId': None,
            'routeDirection': None,
        }
        for index, name in enumerate(player_names)
    ]
    return GameSession.objects.create(
        players=players,
        current_player_index=starting_player_index,
    )


def serialize_game(game: GameSession) -> dict[str, object]:
    current_player = game.players[game.current_player_index]
    available_routes: list[dict[str, str]] = []
    phase = 'FINISHED'

    if game.status == GameSession.Status.PLAYING:
        if current_player['activeRouteId']:
            phase = 'WAITING_FOR_ROLL'
        else:
            phase = 'WAITING_FOR_ROUTE'
            for route in get_routes_from_city(current_player['position']):
                destination_id = (
                    route['nodes'][-1]
                    if route['nodes'][0] == current_player['position']
                    else route['nodes'][0]
                )
                available_routes.append(
                    {
                        'id': route['id'],
                        'name': route['name'],
                        'destinationId': destination_id,
                        'destinationName': get_node(destination_id)['name'],
                    }
                )

    return {
        'gameId': str(game.id),
        'status': game.status,
        'phase': phase,
        'currentRound': game.current_round,
        'maxRounds': MAX_ROUNDS,
        'currentPlayerIndex': game.current_player_index,
        'turnsPlayedInRound': game.turns_played_in_round,
        'players': game.players,
        'availableRoutes': available_routes,
    }


def _validate_turn(
    game: GameSession,
    expected_player_index: int,
    expected_round: int,
) -> None:
    if game.status != GameSession.Status.PLAYING:
        raise GameActionError('GAME_FINISHED', 'A partida já foi finalizada.')
    if expected_player_index != game.current_player_index:
        raise GameActionError('NOT_CURRENT_PLAYER', 'Este jogador não possui o turno atual.')
    if expected_round != game.current_round:
        raise GameActionError('STALE_TURN', 'A rodada informada não é mais a rodada atual.')


@transaction.atomic
def select_route(
    game_id: str,
    route_id: str,
    expected_player_index: int,
    expected_round: int,
) -> GameSession:
    game = GameSession.objects.select_for_update().get(id=game_id)
    _validate_turn(game, expected_player_index, expected_round)

    players = [dict(player) for player in game.players]
    player = players[game.current_player_index]
    if player['activeRouteId']:
        raise GameActionError('ROUTE_ALREADY_SELECTED', 'O jogador já possui uma rota ativa.')

    try:
        route = get_route(route_id)
    except RuntimeError as error:
        raise GameActionError('INVALID_ROUTE', 'A rota informada não existe.') from error

    position = player['position']
    if position == route['nodes'][0]:
        direction = 1
    elif position == route['nodes'][-1]:
        direction = -1
    else:
        raise GameActionError('INVALID_ROUTE', 'A rota não está conectada à posição atual.')

    player['activeRouteId'] = route_id
    player['routeDirection'] = direction
    game.players = players
    game.save(update_fields=['players', 'updated_at'])
    return game


def _advance_turn(game: GameSession) -> None:
    turns_played = game.turns_played_in_round + 1
    if turns_played == len(game.players):
        if game.current_round == MAX_ROUNDS:
            game.turns_played_in_round = turns_played
            game.status = GameSession.Status.FINISHED
            return
        game.current_round += 1
        game.turns_played_in_round = 0
    else:
        game.turns_played_in_round = turns_played

    game.current_player_index = (game.current_player_index + 1) % len(game.players)


@transaction.atomic
def roll_and_move(
    game_id: str,
    expected_player_index: int,
    expected_round: int,
    dice_roller: DiceRoller | None = None,
) -> tuple[GameSession, dict[str, object]]:
    game = GameSession.objects.select_for_update().get(id=game_id)
    _validate_turn(game, expected_player_index, expected_round)

    players = [dict(player) for player in game.players]
    player = players[game.current_player_index]
    route_id = player['activeRouteId']
    direction = player['routeDirection']
    if not route_id or direction not in (-1, 1):
        raise GameActionError('ROUTE_REQUIRED', 'Escolha uma rota antes de jogar o dado.')

    route = get_route(route_id)
    route_nodes = route['nodes']
    try:
        current_position_index = route_nodes.index(player['position'])
    except ValueError as error:
        raise GameActionError('INVALID_POSITION', 'A posição atual não pertence à rota ativa.') from error

    dice = (dice_roller or DiceRoller()).roll(D6_SIDES)
    start_position = player['position']
    path: list[str] = []
    position_index = current_position_index

    for _ in range(dice):
        next_index = position_index + direction
        if not 0 <= next_index < len(route_nodes):
            break
        next_node_id = route_nodes[next_index]
        path.append(next_node_id)
        position_index = next_index
        if get_node(next_node_id)['type'] == 'CITY':
            player['activeRouteId'] = None
            player['routeDirection'] = None
            break

    if not path:
        raise GameActionError('INVALID_POSITION', 'Não existe próxima casa válida nesta rota.')

    player['position'] = path[-1]
    game.players = players
    movement = {
        'playerIndex': game.current_player_index,
        'dice': dice,
        'from': start_position,
        'path': path,
        'to': path[-1],
    }
    _advance_turn(game)
    game.save(
        update_fields=[
            'players',
            'current_player_index',
            'current_round',
            'turns_played_in_round',
            'status',
            'updated_at',
        ]
    )
    return game, movement
