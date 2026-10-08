import json
from functools import lru_cache
from pathlib import Path
from typing import Any


BOARD_PATH = Path(__file__).resolve().parent / 'data' / 'board.json'


class InvalidBoardConfiguration(RuntimeError):
    """Raised when the normalized board graph is inconsistent."""


@lru_cache(maxsize=1)
def load_board() -> dict[str, Any]:
    with BOARD_PATH.open(encoding='utf-8') as board_file:
        board = json.load(board_file)

    nodes = board.get('nodes')
    routes = board.get('routes')
    if not isinstance(nodes, list) or not isinstance(routes, list):
        raise InvalidBoardConfiguration('O tabuleiro precisa conter nodes e routes.')

    node_ids = {node.get('id') for node in nodes if isinstance(node, dict)}
    if len(node_ids) != len(nodes) or None in node_ids:
        raise InvalidBoardConfiguration('Os IDs dos nodes devem ser únicos.')

    for node in nodes:
        if node.get('type') not in {'CITY', 'HIGHWAY', 'DIRT_ROAD'}:
            raise InvalidBoardConfiguration(f"Tipo inválido no node {node.get('id')}.")
        if not 0 <= node.get('x', -1) <= 100 or not 0 <= node.get('y', -1) <= 100:
            raise InvalidBoardConfiguration(f"Coordenada inválida no node {node.get('id')}.")
        tags = node.get('tags', [])
        if not isinstance(tags, list) or any(
            tag not in {'FUEL_STATION', 'PROBLEM'} for tag in tags
        ):
            raise InvalidBoardConfiguration(f"Tags inválidas no node {node.get('id')}.")

    route_ids: set[str] = set()
    node_by_id = {node['id']: node for node in nodes}
    for route in routes:
        route_id = route.get('id')
        route_nodes = route.get('nodes')
        if not route_id or route_id in route_ids:
            raise InvalidBoardConfiguration('Os IDs das rotas devem ser únicos.')
        route_ids.add(route_id)
        if not isinstance(route_nodes, list) or len(route_nodes) < 2:
            raise InvalidBoardConfiguration(f'Rota {route_id} sem nodes suficientes.')
        if any(node_id not in node_by_id for node_id in route_nodes):
            raise InvalidBoardConfiguration(f'Rota {route_id} referencia node inexistente.')
        if node_by_id[route_nodes[0]]['type'] != 'CITY' or node_by_id[route_nodes[-1]]['type'] != 'CITY':
            raise InvalidBoardConfiguration(f'Rota {route_id} deve começar e terminar em cidade.')

    return board


def get_node(node_id: str) -> dict[str, Any]:
    for node in load_board()['nodes']:
        if node['id'] == node_id:
            return node
    raise InvalidBoardConfiguration(f'Node desconhecido: {node_id}.')


def get_route(route_id: str) -> dict[str, Any]:
    for route in load_board()['routes']:
        if route['id'] == route_id:
            return route
    raise InvalidBoardConfiguration(f'Rota desconhecida: {route_id}.')


def get_routes_from_city(city_id: str) -> list[dict[str, Any]]:
    return [
        route
        for route in load_board()['routes']
        if city_id in (route['nodes'][0], route['nodes'][-1])
    ]
