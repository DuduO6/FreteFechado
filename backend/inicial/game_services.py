from random import SystemRandom
from typing import Protocol

from django.db import transaction

from .board import get_node, get_route, get_routes_from_city
from .models import GameSession


MAX_ROUNDS = 15
INITIAL_NODE_ID = 'CITY_BH'
D6_SIDES = 6
INITIAL_BALANCE = 1000
MOVEMENT_COST = 10
MOVEMENT_COST_INTERVAL = 2
BH_ARRIVAL_REWARD = 100
CURRENT_SCHEMA_VERSION = 3
PLAYER_COLORS = ('#e63f2e', '#237edb', '#f3b51b', '#7b45bf')

MAX_FUEL = 5
FUEL_CONSUMPTION_INTERVAL = 3
FUEL_UNIT_PRICE = 50
OUT_OF_FUEL_PENALTY = 300
FUEL_STATION_NODE_ID = 'H_SUL_TRI_05'
FUEL_STATION_ROUTE_ID = 'ROUTE_SUL_TRIANGULO'

PROBLEM_CARDS = (
    {
        'id': 'FLAT_TIRE',
        'title': 'Pneu furado',
        'description': 'Sem estepe disponível: pague R$ 300.',
        'effect': {'balanceDelta': -300},
    },
    {
        'id': 'MECHANICAL_REPAIR',
        'title': 'Reparo mecânico na estrada',
        'description': 'Pague R$ 200 pelo reparo.',
        'effect': {'balanceDelta': -200},
    },
    {
        'id': 'MANDATORY_DETOUR',
        'title': 'Desvio obrigatório',
        'description': 'Na próxima jogada, o dado perde 2 pontos (mínimo 1).',
        'effect': {'nextMovePenalty': 2},
    },
    {
        'id': 'INSURANCE_ASSISTANCE',
        'title': 'Assistência da seguradora',
        'description': 'Receba R$ 100 da seguradora.',
        'effect': {'balanceDelta': 100},
    },
    {
        'id': 'FUEL_VOUCHER',
        'title': 'Vale-combustível',
        'description': 'A próxima movimentação não consumirá combustível.',
        'effect': {'fuelVoucher': True},
    },
)


class GameActionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class RandomSource(Protocol):
    def randrange(self, start: int, stop: int, /) -> int: ...


class DiceRoller:
    def __init__(self, random_source: RandomSource | None = None) -> None:
        self.random_source = random_source or SystemRandom()

    def roll(self, sides: int = D6_SIDES) -> int:
        if sides < 2:
            raise ValueError('O dado precisa ter pelo menos duas faces.')
        return self.random_source.randrange(1, sides + 1)


class ProblemCardDrawer:
    def __init__(self, random_source: RandomSource | None = None) -> None:
        self.random_source = random_source or SystemRandom()

    def draw(self) -> dict[str, object]:
        index = self.random_source.randrange(0, len(PROBLEM_CARDS))
        card = PROBLEM_CARDS[index]
        return {**card, 'effect': dict(card['effect'])}


def _normalize_player(player: dict[str, object], index: int) -> dict[str, object]:
    normalized_player = dict(player)
    normalized_player.setdefault('turnOrder', index + 1)
    normalized_player.setdefault('balance', INITIAL_BALANCE)
    normalized_player.setdefault('hasValidContract', False)
    normalized_player.setdefault('color', PLAYER_COLORS[index])
    normalized_player.setdefault('spacesTraveled', 0)
    normalized_player.setdefault('fuel', MAX_FUEL)
    normalized_player.setdefault('fuelDistance', 0)
    normalized_player.setdefault('fuelVoucher', False)
    normalized_player.setdefault('nextMovePenalty', 0)
    normalized_player.setdefault('pendingRefuel', None)
    normalized_player.setdefault('pendingProblemCard', None)
    return normalized_player


def _players_for_snapshot(game: GameSession) -> list[dict[str, object]]:
    player_count = len(game.players)
    players: list[dict[str, object]] = []
    for index, player in enumerate(game.players):
        snapshot_player = _normalize_player(player, index)
        snapshot_player['isCurrentPlayer'] = index == game.current_player_index
        snapshot_player['turnsUntilTurn'] = (
            index - game.current_player_index
        ) % player_count
        players.append(snapshot_player)
    return players


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
            'turnOrder': index + 1,
            'balance': INITIAL_BALANCE,
            'hasValidContract': False,
            'color': PLAYER_COLORS[index],
            'spacesTraveled': 0,
            'fuel': MAX_FUEL,
            'fuelDistance': 0,
            'fuelVoucher': False,
            'nextMovePenalty': 0,
            'pendingRefuel': None,
            'pendingProblemCard': None,
        }
        for index, name in enumerate(player_names)
    ]
    return GameSession.objects.create(
        players=players,
        current_player_index=starting_player_index,
        schema_version=CURRENT_SCHEMA_VERSION,
    )


def serialize_game(game: GameSession) -> dict[str, object]:
    players = _players_for_snapshot(game)
    current_player = players[game.current_player_index]
    available_routes: list[dict[str, str]] = []
    phase = 'FINISHED'
    refuel_offer = None
    pending_problem_card = None

    if game.status == GameSession.Status.PLAYING:
        if current_player['pendingProblemCard']:
            phase = 'WAITING_FOR_EVENT'
            pending_problem_card = {
                **current_player['pendingProblemCard'],
                'playerIndex': game.current_player_index,
            }
        elif current_player['pendingRefuel']:
            phase = 'WAITING_FOR_REFUEL'
            refuel_offer = {
                **current_player['pendingRefuel'],
                'playerIndex': game.current_player_index,
                'fuel': current_player['fuel'],
                'maxFuel': MAX_FUEL,
                'unitPrice': FUEL_UNIT_PRICE,
            }
        elif current_player['activeRouteId']:
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
        'players': players,
        'availableRoutes': available_routes,
        'refuelOffer': refuel_offer,
        'pendingProblemCard': pending_problem_card,
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


def _ensure_no_pending_action(player: dict[str, object]) -> None:
    if player['pendingRefuel']:
        raise GameActionError('REFUEL_DECISION_REQUIRED', 'Decida se deseja abastecer antes de continuar.')
    if player['pendingProblemCard']:
        raise GameActionError('EVENT_ACKNOWLEDGEMENT_REQUIRED', 'Revele e confirme a carta antes de continuar.')


@transaction.atomic
def select_route(
    game_id: str,
    route_id: str,
    expected_player_index: int,
    expected_round: int,
) -> GameSession:
    game = GameSession.objects.select_for_update().get(id=game_id)
    _validate_turn(game, expected_player_index, expected_round)

    players = [_normalize_player(player, index) for index, player in enumerate(game.players)]
    player = players[game.current_player_index]
    _ensure_no_pending_action(player)
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


def _apply_problem_card(player: dict[str, object], card: dict[str, object]) -> None:
    effect = card['effect']
    player['balance'] = int(player['balance']) + int(effect.get('balanceDelta', 0))
    if effect.get('nextMovePenalty'):
        player['nextMovePenalty'] = int(effect['nextMovePenalty'])
    if effect.get('fuelVoucher'):
        player['fuelVoucher'] = True
    player['pendingProblemCard'] = card


@transaction.atomic
def roll_and_move(
    game_id: str,
    expected_player_index: int,
    expected_round: int,
    dice_roller: DiceRoller | None = None,
    card_drawer: ProblemCardDrawer | None = None,
) -> tuple[GameSession, dict[str, object]]:
    game = GameSession.objects.select_for_update().get(id=game_id)
    _validate_turn(game, expected_player_index, expected_round)

    players = [_normalize_player(player, index) for index, player in enumerate(game.players)]
    player = players[game.current_player_index]
    _ensure_no_pending_action(player)
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
    applied_penalty = int(player['nextMovePenalty'])
    movement_steps = max(1, dice - applied_penalty)
    player['nextMovePenalty'] = 0
    uses_fuel_voucher = bool(player['fuelVoucher'])
    player['fuelVoucher'] = False
    start_position = player['position']
    path: list[str] = []
    position_index = current_position_index
    traveled_steps = 0
    ran_out_of_fuel = False
    reached_station = False

    for _ in range(movement_steps):
        next_index = position_index + direction
        if not 0 <= next_index < len(route_nodes):
            break
        next_node_id = route_nodes[next_index]
        path.append(next_node_id)
        traveled_steps += 1
        position_index = next_index

        if not uses_fuel_voucher:
            player['fuelDistance'] = int(player['fuelDistance']) + 1
            if int(player['fuelDistance']) % FUEL_CONSUMPTION_INTERVAL == 0:
                player['fuel'] = max(0, int(player['fuel']) - 1)
                if player['fuel'] == 0:
                    ran_out_of_fuel = True
                    break

        node = get_node(next_node_id)
        if 'FUEL_STATION' in node.get('tags', []):
            reached_station = True
            break
        if node['type'] == 'CITY':
            player['activeRouteId'] = None
            player['routeDirection'] = None
            break

    if not path:
        raise GameActionError('INVALID_POSITION', 'Não existe próxima casa válida nesta rota.')

    previous_spaces = int(player['spacesTraveled'])
    current_spaces = previous_spaces + traveled_steps
    charged_intervals = current_spaces // MOVEMENT_COST_INTERVAL - previous_spaces // MOVEMENT_COST_INTERVAL
    movement_cost = charged_intervals * MOVEMENT_COST
    player['spacesTraveled'] = current_spaces
    balance_delta = -movement_cost

    if ran_out_of_fuel:
        if path[-1] != FUEL_STATION_NODE_ID:
            path.append(FUEL_STATION_NODE_ID)
        player['position'] = FUEL_STATION_NODE_ID
        player['activeRouteId'] = FUEL_STATION_ROUTE_ID
        player['routeDirection'] = 1
        player['pendingRefuel'] = {'reason': 'OUT_OF_FUEL', 'required': True}
        balance_delta -= OUT_OF_FUEL_PENALTY
    else:
        player['position'] = path[-1]
        if reached_station:
            player['pendingRefuel'] = {'reason': 'STATION', 'required': False}

    arrival_reward = (
        BH_ARRIVAL_REWARD
        if player['position'] == INITIAL_NODE_ID and start_position != INITIAL_NODE_ID
        else 0
    )
    balance_delta += arrival_reward
    player['balance'] = int(player['balance']) + balance_delta

    problem_card = None
    final_node = get_node(player['position'])
    if not ran_out_of_fuel and not reached_station and 'PROBLEM' in final_node.get('tags', []):
        problem_card = (card_drawer or ProblemCardDrawer()).draw()
        _apply_problem_card(player, problem_card)

    game.players = players
    card_balance_delta = int((problem_card or {}).get('effect', {}).get('balanceDelta', 0))
    movement = {
        'playerIndex': game.current_player_index,
        'dice': dice,
        'movementSteps': movement_steps,
        'appliedPenalty': applied_penalty,
        'from': start_position,
        'path': path,
        'to': player['position'],
        'balanceDelta': balance_delta + card_balance_delta,
        'ranOutOfFuel': ran_out_of_fuel,
    }
    if not player['pendingRefuel'] and not player['pendingProblemCard']:
        _advance_turn(game)
    game.save(
        update_fields=[
            'players', 'current_player_index', 'current_round',
            'turns_played_in_round', 'status', 'updated_at',
        ]
    )
    return game, movement


@transaction.atomic
def refuel_player(
    game_id: str,
    units: int,
    expected_player_index: int,
    expected_round: int,
) -> GameSession:
    game = GameSession.objects.select_for_update().get(id=game_id)
    _validate_turn(game, expected_player_index, expected_round)
    players = [_normalize_player(player, index) for index, player in enumerate(game.players)]
    player = players[game.current_player_index]
    offer = player['pendingRefuel']
    if not offer:
        raise GameActionError('NO_REFUEL_OFFER', 'Não há abastecimento pendente.')
    if isinstance(units, bool) or not isinstance(units, int):
        raise GameActionError('INVALID_FUEL_AMOUNT', 'Informe uma quantidade inteira de combustível.')
    missing_units = MAX_FUEL - int(player['fuel'])
    minimum_units = 1 if offer.get('required') else 0
    if not minimum_units <= units <= missing_units:
        raise GameActionError('INVALID_FUEL_AMOUNT', 'Quantidade de combustível inválida para este abastecimento.')

    player['fuel'] = int(player['fuel']) + units
    player['balance'] = int(player['balance']) - units * FUEL_UNIT_PRICE
    player['pendingRefuel'] = None
    game.players = players
    _advance_turn(game)
    game.save(
        update_fields=[
            'players', 'current_player_index', 'current_round',
            'turns_played_in_round', 'status', 'updated_at',
        ]
    )
    return game


@transaction.atomic
def acknowledge_problem_card(
    game_id: str,
    expected_player_index: int,
    expected_round: int,
) -> GameSession:
    game = GameSession.objects.select_for_update().get(id=game_id)
    _validate_turn(game, expected_player_index, expected_round)
    players = [_normalize_player(player, index) for index, player in enumerate(game.players)]
    player = players[game.current_player_index]
    if not player['pendingProblemCard']:
        raise GameActionError('NO_PENDING_EVENT', 'Não há carta de problema pendente.')

    player['pendingProblemCard'] = None
    game.players = players
    _advance_turn(game)
    game.save(
        update_fields=[
            'players', 'current_player_index', 'current_round',
            'turns_played_in_round', 'status', 'updated_at',
        ]
    )
    return game
