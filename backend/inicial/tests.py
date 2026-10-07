import json

from django.test import TestCase
from django.urls import reverse


class ReceivePlayerNamesTests(TestCase):
    def setUp(self) -> None:
        self.url = reverse('inicial:receive-player-names')

    def post_players(self, players: object):
        return self.client.post(
            self.url,
            data=json.dumps({'players': players}),
            content_type='application/json',
        )

    def test_receives_and_normalizes_two_to_four_player_names(self) -> None:
        response = self.post_players(['  Ana  ', 'Beto', 'Caio', 'Duda'])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {'ok': True, 'players': ['Ana', 'Beto', 'Caio', 'Duda']},
        )

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
