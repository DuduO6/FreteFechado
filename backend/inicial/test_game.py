import json

from django.test import TestCase
from django.urls import reverse

from .board import get_routes_from_city, load_board
from .contracts import load_contracts
from .game_services import (
    DiceRoller,
    GameActionError,
    INITIAL_BALANCE,
    MAX_ROUNDS,
    MOVEMENT_COST,
    OUT_OF_FUEL_PENALTY,
    PROBLEM_CARDS,
    FUEL_STATION_NODE_ID,
    FUEL_UNIT_PRICE,
    ProblemCardDrawer,
    acknowledge_problem_card,
    create_game_session,
    refuel_player,
    roll_and_move,
    select_route,
)


class FixedDiceSource:
    def __init__(self, value: int) -> None:
        self.value = value
        self.received_range: tuple[int, int] | None = None

    def randrange(self, start: int, stop: int, /) -> int:
        self.received_range = (start, stop)
        return self.value


class DiceRollerTests(TestCase):
    def test_d6_only_returns_values_between_one_and_six(self) -> None:
        roller = DiceRoller()

        results = [roller.roll() for _ in range(200)]

        self.assertTrue(all(1 <= result <= 6 for result in results))

    def test_random_source_can_be_injected(self) -> None:
        source = FixedDiceSource(6)

        result = DiceRoller(source).roll()

        self.assertEqual(result, 6)
        self.assertEqual(source.received_range, (1, 7))

    def test_only_contracts_can_increase_player_balance(self) -> None:
        positive_event_rewards = [
            card
            for card in PROBLEM_CARDS
            if int(card['effect'].get('balanceDelta', 0)) > 0
        ]

        self.assertEqual(positive_event_rewards, [])


class BoardConfigurationTests(TestCase):
    def test_normalized_board_has_bh_and_only_relative_coordinates(self) -> None:
        board = load_board()
        nodes = {node['id']: node for node in board['nodes']}

        self.assertEqual(nodes['CITY_BH']['type'], 'CITY')
        self.assertEqual(len(nodes), 59)
        self.assertEqual(len(board['landmarks']), 2)
        self.assertEqual(len(board['routes']), 8)
        self.assertEqual(board['source'], 'project-6-at-2026-10-22-11-45-c7358ab8.json')
        self.assertEqual(
            {landmark['type'] for landmark in board['landmarks']},
            {'GAS_STATION', 'POLICE_STATION'},
        )
        routed_nodes = {
            node_id
            for route in board['routes']
            for node_id in route['nodes']
        }
        self.assertEqual(routed_nodes, set(nodes))
        self.assertTrue(
            all(0 <= node['x'] <= 100 and 0 <= node['y'] <= 100 for node in nodes.values())
        )

    def test_routes_declare_directed_traversals(self) -> None:
        board = load_board()

        self.assertTrue(all(route['allowedDirections'] for route in board['routes']))
        self.assertNotIn(
            'ROUTE_BH_NORTE_HIGHWAY',
            {route['id'] for route in get_routes_from_city('CITY_NORTE')},
        )
        self.assertIn(
            'ROUTE_NORTE_ZONA',
            {route['id'] for route in get_routes_from_city('CITY_NORTE')},
        )

    def test_contract_catalog_matches_available_card_assets(self) -> None:
        contracts = load_contracts()

        self.assertEqual(len(contracts), 9)
        self.assertEqual(len({contract['imageKey'] for contract in contracts}), 9)


class MovementAndTurnTests(TestCase):
    def setUp(self) -> None:
        self.game = create_game_session(['Ana', 'Beto'], starting_player_index=0)

    def select_bh_to_triangulo(self, player_index: int = 0, round_number: int = 1) -> None:
        select_route(
            str(self.game.id),
            'ROUTE_BH_TRIANGULO',
            player_index,
            round_number,
        )

    def test_only_current_player_can_select_or_roll(self) -> None:
        with self.assertRaisesMessage(GameActionError, 'não possui o turno atual'):
            select_route(str(self.game.id), 'ROUTE_BH_TRIANGULO', 1, 1)

    def test_movement_uses_dice_result_and_returns_each_node(self) -> None:
        self.select_bh_to_triangulo()

        game, movement = roll_and_move(
            str(self.game.id),
            0,
            1,
            DiceRoller(FixedDiceSource(4)),
        )

        self.assertEqual(movement['dice'], 4)
        self.assertEqual(
            movement['path'],
            ['D_BH_WEST_01', 'D_BH_WEST_02', 'D_BH_WEST_03', 'D_BH_WEST_04'],
        )
        self.assertEqual(game.players[0]['position'], 'D_BH_WEST_04')
        self.assertEqual(game.players[0]['balance'], INITIAL_BALANCE - 2 * MOVEMENT_COST)
        self.assertEqual(movement['balanceDelta'], -2 * MOVEMENT_COST)

    def test_movement_cost_accumulates_houses_between_turns(self) -> None:
        self.select_bh_to_triangulo()
        first_game, _ = roll_and_move(
            str(self.game.id), 0, 1, DiceRoller(FixedDiceSource(1))
        )
        select_route(str(self.game.id), 'ROUTE_BH_SUL', 1, 1)
        roll_and_move(str(self.game.id), 1, 1, DiceRoller(FixedDiceSource(1)))

        game, movement = roll_and_move(
            str(self.game.id), 0, 2, DiceRoller(FixedDiceSource(1))
        )

        self.assertEqual(first_game.players[0]['balance'], INITIAL_BALANCE)
        self.assertEqual(game.players[0]['spacesTraveled'], 2)
        self.assertEqual(game.players[0]['balance'], INITIAL_BALANCE - MOVEMENT_COST)
        self.assertEqual(movement['balanceDelta'], -MOVEMENT_COST)

    def test_arriving_in_bh_without_contract_does_not_pay_reward(self) -> None:
        players = [dict(player) for player in self.game.players]
        players[0].update(
            {
                'position': 'D_BH_WEST_01',
                'activeRouteId': 'ROUTE_BH_TRIANGULO',
                'routeDirection': -1,
            }
        )
        self.game.players = players
        self.game.save(update_fields=['players'])

        game, movement = roll_and_move(
            str(self.game.id), 0, 1, DiceRoller(FixedDiceSource(1))
        )

        self.assertEqual(movement['to'], 'CITY_BH')
        self.assertEqual(movement['balanceDelta'], 0)
        self.assertEqual(game.players[0]['balance'], INITIAL_BALANCE)

    def test_contract_is_paid_once_when_destination_is_reached(self) -> None:
        players = [dict(player) for player in self.game.players]
        players[0].update(
            {
                'position': 'H_NORTE_BH_01',
                'activeRouteId': 'ROUTE_BH_NORTE_HIGHWAY',
                'routeDirection': 1,
                'activeContractId': 'BH_NORTE_RODOVIA',
                'hasValidContract': True,
            }
        )
        self.game.players = players
        self.game.save(update_fields=['players'])

        game, movement = roll_and_move(
            str(self.game.id), 0, 1, DiceRoller(FixedDiceSource(1))
        )

        self.assertEqual(movement['completedContract']['id'], 'BH_NORTE_RODOVIA')
        self.assertEqual(movement['balanceDelta'], 400)
        self.assertEqual(game.players[0]['balance'], INITIAL_BALANCE + 400)
        self.assertIsNone(game.players[0]['activeContractId'])
        self.assertEqual(game.players[0]['deliveries'], 1)

    def test_contract_automatically_selects_the_only_next_segment(self) -> None:
        players = [dict(player) for player in self.game.players]
        players[0].update(
            {
                'position': 'H_NORTE_BH_01',
                'activeRouteId': 'ROUTE_BH_NORTE_HIGHWAY',
                'routeDirection': 1,
                'activeContractId': 'BH_ZONA_MATA_ALFACE',
                'hasValidContract': True,
            }
        )
        self.game.players = players
        self.game.save(update_fields=['players'])

        game, movement = roll_and_move(
            str(self.game.id), 0, 1, DiceRoller(FixedDiceSource(1))
        )

        self.assertEqual(movement['to'], 'CITY_NORTE')
        self.assertEqual(game.players[0]['activeRouteId'], 'ROUTE_NORTE_ZONA')
        self.assertEqual(game.players[0]['routeDirection'], 1)

    def test_city_stops_movement_and_discards_remaining_steps(self) -> None:
        self.select_bh_to_triangulo()

        game, movement = roll_and_move(
            str(self.game.id),
            0,
            1,
            DiceRoller(FixedDiceSource(6)),
        )

        self.assertEqual(len(movement['path']), 5)
        self.assertEqual(movement['to'], 'CITY_TRIANGULO')
        self.assertIsNone(game.players[0]['activeRouteId'])

    def test_turn_advances_after_movement(self) -> None:
        self.select_bh_to_triangulo()

        game, _ = roll_and_move(
            str(self.game.id), 0, 1, DiceRoller(FixedDiceSource(1))
        )

        self.assertEqual(game.current_player_index, 1)
        self.assertEqual(game.current_round, 1)
        self.assertEqual(game.turns_played_in_round, 1)

    def test_last_player_advances_round_and_returns_to_first(self) -> None:
        self.select_bh_to_triangulo()
        roll_and_move(str(self.game.id), 0, 1, DiceRoller(FixedDiceSource(1)))
        select_route(str(self.game.id), 'ROUTE_BH_SUL', 1, 1)

        game, _ = roll_and_move(
            str(self.game.id), 1, 1, DiceRoller(FixedDiceSource(1))
        )

        self.assertEqual(game.current_player_index, 0)
        self.assertEqual(game.current_round, 2)
        self.assertEqual(game.turns_played_in_round, 0)

    def test_same_turn_cannot_roll_twice(self) -> None:
        self.select_bh_to_triangulo()
        roll_and_move(str(self.game.id), 0, 1, DiceRoller(FixedDiceSource(1)))

        with self.assertRaises(GameActionError) as raised:
            roll_and_move(str(self.game.id), 0, 1, DiceRoller(FixedDiceSource(1)))

        self.assertEqual(raised.exception.code, 'NOT_CURRENT_PLAYER')

    def test_game_finishes_after_every_player_completes_round_fifteen(self) -> None:
        self.game.current_round = MAX_ROUNDS
        self.game.turns_played_in_round = 1
        self.game.current_player_index = 1
        self.game.save()
        select_route(str(self.game.id), 'ROUTE_BH_SUL', 1, MAX_ROUNDS)

        game, _ = roll_and_move(
            str(self.game.id),
            1,
            MAX_ROUNDS,
            DiceRoller(FixedDiceSource(1)),
        )

        self.assertEqual(game.status, 'FINISHED')
        self.assertEqual(game.current_round, MAX_ROUNDS)


class GameApiTests(TestCase):
    def setUp(self) -> None:
        self.game = create_game_session(['Ana', 'Beto'], starting_player_index=0)

    def post_json(self, url: str, payload: dict[str, object]):
        return self.client.post(
            url,
            data=json.dumps(payload),
            content_type='application/json',
        )

    def test_board_endpoint_exposes_normalized_graph(self) -> None:
        response = self.client.get(reverse('inicial:board-config'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['board']['nodes']), 59)
        self.assertEqual(len(response.json()['board']['landmarks']), 2)

    def test_snapshot_exposes_authoritative_player_information(self) -> None:
        response = self.client.get(
            reverse('inicial:game-detail', args=[self.game.id])
        )

        players = response.json()['snapshot']['players']
        self.assertEqual(
            players[0],
            {
                'id': 'player-1',
                'name': 'Ana',
                'position': 'CITY_BH',
                'activeRouteId': None,
                'routeDirection': None,
                'turnOrder': 1,
                'balance': INITIAL_BALANCE,
                'hasValidContract': False,
                'activeContractId': None,
                'deliveries': 0,
                'color': '#e63f2e',
                'spacesTraveled': 0,
                'fuel': 5,
                'fuelDistance': 0,
                'fuelVoucher': False,
                'nextMovePenalty': 0,
                'pendingRefuel': None,
                'pendingProblemCard': None,
                'activeContract': None,
                'isCurrentPlayer': True,
                'turnsUntilTurn': 0,
            },
        )
        self.assertFalse(players[1]['isCurrentPlayer'])
        self.assertEqual(players[1]['turnsUntilTurn'], 1)

    def test_player_without_contract_can_choose_any_directed_route(self) -> None:
        response = self.client.get(
            reverse('inicial:game-detail', args=[self.game.id])
        )

        self.assertEqual(
            {route['id'] for route in response.json()['snapshot']['availableRoutes']},
            {
                'ROUTE_BH_TRIANGULO',
                'ROUTE_BH_NORTE_DIRT',
                'ROUTE_BH_NORTE_HIGHWAY',
                'ROUTE_BH_SUL',
            },
        )

    def test_contract_endpoint_accepts_only_an_offer_from_current_city(self) -> None:
        contract_url = reverse('inicial:accept-game-contract', args=[self.game.id])
        context = {'expectedPlayerIndex': 0, 'expectedRound': 1}

        rejected = self.post_json(
            contract_url,
            {**context, 'contractId': 'SUL_BH'},
        )
        accepted = self.post_json(
            contract_url,
            {**context, 'contractId': 'BH_NORTE_ATALHO'},
        )

        self.assertEqual(rejected.status_code, 409)
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(
            accepted.json()['snapshot']['players'][0]['activeContract']['id'],
            'BH_NORTE_ATALHO',
        )
        self.assertEqual(
            {route['id'] for route in accepted.json()['snapshot']['availableRoutes']},
            {'ROUTE_BH_NORTE_DIRT', 'ROUTE_BH_NORTE_HIGHWAY'},
        )

    def test_contract_filters_routes_to_the_best_path_and_keeps_road_alternatives(self) -> None:
        contract_url = reverse('inicial:accept-game-contract', args=[self.game.id])
        response = self.post_json(
            contract_url,
            {
                'contractId': 'BH_ZONA_MATA_ALFACE',
                'expectedPlayerIndex': 0,
                'expectedRound': 1,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {route['id'] for route in response.json()['snapshot']['availableRoutes']},
            {'ROUTE_BH_NORTE_DIRT', 'ROUTE_BH_NORTE_HIGHWAY'},
        )

    def test_contract_with_one_path_selects_route_automatically(self) -> None:
        players = [dict(player) for player in self.game.players]
        players[0]['position'] = 'CITY_SUL'
        self.game.players = players
        self.game.save(update_fields=['players'])

        response = self.post_json(
            reverse('inicial:accept-game-contract', args=[self.game.id]),
            {
                'contractId': 'SUL_BH',
                'expectedPlayerIndex': 0,
                'expectedRound': 1,
            },
        )

        snapshot = response.json()['snapshot']
        self.assertEqual(response.status_code, 200)
        self.assertEqual(snapshot['phase'], 'WAITING_FOR_ROLL')
        self.assertEqual(snapshot['players'][0]['activeRouteId'], 'ROUTE_BH_SUL')
        self.assertEqual(snapshot['players'][0]['routeDirection'], -1)

    def test_active_contract_rejects_a_route_outside_its_destination(self) -> None:
        players = [dict(player) for player in self.game.players]
        players[0].update(
            {
                'activeContractId': 'BH_NORTE_ATALHO',
                'hasValidContract': True,
            }
        )
        self.game.players = players
        self.game.save(update_fields=['players'])

        with self.assertRaises(GameActionError) as raised:
            select_route(str(self.game.id), 'ROUTE_BH_SUL', 0, 1)

        self.assertEqual(raised.exception.code, 'ROUTE_OUTSIDE_CONTRACT')

    def test_route_selection_rejects_forbidden_direction(self) -> None:
        players = [dict(player) for player in self.game.players]
        players[0]['position'] = 'CITY_NORTE'
        self.game.players = players
        self.game.save(update_fields=['players'])

        with self.assertRaises(GameActionError) as raised:
            select_route(str(self.game.id), 'ROUTE_BH_NORTE_HIGHWAY', 0, 1)

        self.assertEqual(raised.exception.code, 'INVALID_ROUTE_DIRECTION')

    def test_roll_endpoint_returns_snapshot_and_movement_path(self) -> None:
        route_url = reverse('inicial:select-game-route', args=[self.game.id])
        roll_url = reverse('inicial:roll-game', args=[self.game.id])
        action_context = {'expectedPlayerIndex': 0, 'expectedRound': 1}
        route_response = self.post_json(
            route_url,
            {**action_context, 'routeId': 'ROUTE_BH_TRIANGULO'},
        )

        response = self.post_json(roll_url, action_context)

        self.assertEqual(route_response.status_code, 200)
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()['movement']['dice'], range(1, 7))
        self.assertTrue(response.json()['movement']['path'])
        self.assertIn(
            response.json()['snapshot']['phase'],
            {'WAITING_FOR_ROUTE', 'WAITING_FOR_EVENT'},
        )

    def test_stale_turn_is_rejected_without_changing_session(self) -> None:
        roll_url = reverse('inicial:roll-game', args=[self.game.id])

        response = self.post_json(
            roll_url,
            {'expectedPlayerIndex': 1, 'expectedRound': 1},
        )

        self.assertEqual(response.status_code, 409)
        self.game.refresh_from_db()
        self.assertEqual(self.game.current_player_index, 0)
        self.assertEqual(self.game.players[0]['position'], 'CITY_BH')


class FuelAndProblemTests(TestCase):
    def setUp(self) -> None:
        self.game = create_game_session(['Ana', 'Beto'], starting_player_index=0)

    def update_first_player(self, **changes: object) -> None:
        players = [dict(player) for player in self.game.players]
        players[0].update(changes)
        self.game.players = players
        self.game.save(update_fields=['players'])

    def test_players_start_with_five_fuel_levels(self) -> None:
        self.assertEqual([player['fuel'] for player in self.game.players], [5, 5])

    def test_one_fuel_level_is_consumed_after_three_accumulated_spaces(self) -> None:
        self.update_first_player(
            activeRouteId='ROUTE_BH_TRIANGULO',
            routeDirection=1,
            fuelDistance=2,
        )

        game, _ = roll_and_move(
            str(self.game.id), 0, 1, DiceRoller(FixedDiceSource(1))
        )

        self.assertEqual(game.players[0]['fuelDistance'], 3)
        self.assertEqual(game.players[0]['fuel'], 4)

    def test_fuel_voucher_skips_consumption_for_one_movement(self) -> None:
        self.update_first_player(
            activeRouteId='ROUTE_BH_TRIANGULO',
            routeDirection=1,
            fuelVoucher=True,
        )

        game, _ = roll_and_move(
            str(self.game.id), 0, 1, DiceRoller(FixedDiceSource(2))
        )

        self.assertEqual(game.players[0]['fuel'], 5)
        self.assertEqual(game.players[0]['fuelDistance'], 0)
        self.assertFalse(game.players[0]['fuelVoucher'])

    def test_empty_tank_charges_penalty_and_tows_player_to_station(self) -> None:
        self.update_first_player(
            activeRouteId='ROUTE_BH_TRIANGULO',
            routeDirection=1,
            fuel=1,
            fuelDistance=2,
        )

        game, movement = roll_and_move(
            str(self.game.id), 0, 1, DiceRoller(FixedDiceSource(1))
        )

        self.assertTrue(movement['ranOutOfFuel'])
        self.assertEqual(game.players[0]['position'], FUEL_STATION_NODE_ID)
        self.assertEqual(game.players[0]['balance'], INITIAL_BALANCE - OUT_OF_FUEL_PENALTY)
        self.assertEqual(game.players[0]['pendingRefuel']['reason'], 'OUT_OF_FUEL')
        self.assertEqual(game.current_player_index, 0)

    def test_station_stops_movement_and_offers_optional_refuel(self) -> None:
        self.update_first_player(
            position='CITY_TRIANGULO',
            activeRouteId='ROUTE_TRIANGULO_NORTE',
            routeDirection=1,
            fuel=3,
        )

        game, movement = roll_and_move(
            str(self.game.id), 0, 1, DiceRoller(FixedDiceSource(6))
        )

        self.assertEqual(movement['to'], FUEL_STATION_NODE_ID)
        self.assertEqual(len(movement['path']), 2)
        self.assertFalse(game.players[0]['pendingRefuel']['required'])
        self.assertEqual(game.current_player_index, 0)

    def test_refuel_costs_fifty_reais_per_level_and_ends_turn(self) -> None:
        self.update_first_player(
            position=FUEL_STATION_NODE_ID,
            activeRouteId='ROUTE_TRIANGULO_NORTE',
            routeDirection=1,
            fuel=2,
            pendingRefuel={'reason': 'STATION', 'required': False},
        )

        game = refuel_player(str(self.game.id), 2, 0, 1)

        self.assertEqual(game.players[0]['fuel'], 4)
        self.assertEqual(game.players[0]['balance'], INITIAL_BALANCE - 2 * FUEL_UNIT_PRICE)
        self.assertIsNone(game.players[0]['pendingRefuel'])
        self.assertEqual(game.current_player_index, 1)

    def test_out_of_fuel_offer_cannot_be_declined(self) -> None:
        self.update_first_player(
            fuel=0,
            pendingRefuel={'reason': 'OUT_OF_FUEL', 'required': True},
        )

        with self.assertRaises(GameActionError) as raised:
            refuel_player(str(self.game.id), 0, 0, 1)

        self.assertEqual(raised.exception.code, 'INVALID_FUEL_AMOUNT')

    def test_problem_card_is_drawn_only_when_movement_stops_on_problem(self) -> None:
        self.update_first_player(activeRouteId='ROUTE_BH_TRIANGULO', routeDirection=1)

        game, movement = roll_and_move(
            str(self.game.id),
            0,
            1,
            DiceRoller(FixedDiceSource(3)),
            ProblemCardDrawer(FixedDiceSource(0)),
        )

        self.assertEqual(movement['to'], 'D_BH_WEST_03')
        self.assertEqual(game.players[0]['pendingProblemCard']['id'], 'FLAT_TIRE')
        self.assertEqual(game.players[0]['balance'], INITIAL_BALANCE - MOVEMENT_COST - 300)
        self.assertEqual(game.current_player_index, 0)

    def test_passing_problem_space_does_not_draw_card(self) -> None:
        self.update_first_player(activeRouteId='ROUTE_BH_TRIANGULO', routeDirection=1)

        game, _ = roll_and_move(
            str(self.game.id), 0, 1, DiceRoller(FixedDiceSource(4))
        )

        self.assertIsNone(game.players[0]['pendingProblemCard'])
        self.assertEqual(game.current_player_index, 1)

    def test_acknowledging_problem_card_advances_turn(self) -> None:
        self.update_first_player(
            pendingProblemCard={
                'id': 'FLAT_TIRE',
                'title': 'Pneu furado',
                'description': 'Pague R$ 300.',
                'effect': {'balanceDelta': -300},
            }
        )

        game = acknowledge_problem_card(str(self.game.id), 0, 1)

        self.assertIsNone(game.players[0]['pendingProblemCard'])
        self.assertEqual(game.current_player_index, 1)
