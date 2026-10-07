import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .services import select_starting_player_index


class FixedRandomSource:
    def __init__(self, result: int) -> None:
        self.result = result
        self.received_stop: int | None = None

    def randrange(self, stop: int, /) -> int:
        self.received_stop = stop
        return self.result


class SelectStartingPlayerTests(TestCase):
    def test_selects_player_with_injected_random_source(self) -> None:
        random_source = FixedRandomSource(result=2)

        result = select_starting_player_index(
            ['Ana', 'Beto', 'Caio', 'Duda'],
            random_source,
        )

        self.assertEqual(result, 2)
        self.assertEqual(random_source.received_stop, 4)

    def test_rejects_empty_player_list(self) -> None:
        with self.assertRaisesMessage(
            ValueError,
            'Não há jogadores disponíveis para o sorteio.',
        ):
            select_starting_player_index([])


class ReceivePlayerNamesTests(TestCase):
    def setUp(self) -> None:
        self.url = reverse('inicial:receive-player-names')

    def post_players(self, players: object):
        return self.client.post(
            self.url,
            data=json.dumps({'players': players}),
            content_type='application/json',
        )

    @patch('inicial.views.select_starting_player_index', return_value=2)
    def test_receives_names_and_selects_starting_player(self, select_mock) -> None:
        response = self.post_players(['  Ana  ', 'Beto', 'Caio', 'Duda'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['players'],
            ['Ana', 'Beto', 'Caio', 'Duda'],
        )
        self.assertEqual(response.json()['startingPlayerIndex'], 2)
        self.assertEqual(response.json()['snapshot']['currentPlayerIndex'], 2)
        self.assertEqual(response.json()['snapshot']['currentRound'], 1)
        self.assertTrue(response.json()['snapshot']['gameId'])
        select_mock.assert_called_once_with(['Ana', 'Beto', 'Caio', 'Duda'])

    def test_rejects_player_count_outside_allowed_range(self) -> None:
        for players in (['Ana'], ['A', 'B', 'C', 'D', 'E']):
            with self.subTest(players=players):
                response = self.post_players(players)

                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()['message'], 'Informe de 2 a 4 jogadores.')

    def test_rejects_blank_or_non_string_names(self) -> None:
        for players in (['Ana', '  '], ['Ana', 42]):
            with self.subTest(players=players):
                response = self.post_players(players)

                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()['message'],
                    'Todos os jogadores precisam de um nome.',
                )

    def test_rejects_names_longer_than_forty_characters(self) -> None:
        response = self.post_players(['Ana', 'A' * 41])

        self.assertEqual(response.status_code, 400)
        self.assertIn('no máximo 40 caracteres', response.json()['message'])

    def test_rejects_malformed_json(self) -> None:
        response = self.client.post(
            self.url,
            data='{not-json',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['ok'], False)

    def test_rejects_get_requests(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
