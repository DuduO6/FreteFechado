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
    landmarks = board.get('landmarks', [])
    if (
        not isinstance(nodes, list)
        or not isinstance(routes, list)
        or not isinstance(landmarks, list)
    ):
        raise InvalidBoardConfiguration(
            'O tabuleiro precisa conter nodes, routes e landmarks válidos.'
        )

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
    landmark_ids: set[str] = set()
    for landmark in landmarks:
        landmark_id = landmark.get('id')
        if not landmark_id or landmark_id in landmark_ids:
            raise InvalidBoardConfiguration('Os IDs dos landmarks devem ser únicos.')
        landmark_ids.add(landmark_id)
        if landmark.get('type') not in {'GAS_STATION', 'POLICE_STATION'}:
            raise InvalidBoardConfiguration(f'Tipo inválido no landmark {landmark_id}.')
        if not 0 <= landmark.get('x', -1) <= 100 or not 0 <= landmark.get('y', -1) <= 100:
            raise InvalidBoardConfiguration(f'Coordenada inválida no landmark {landmark_id}.')
        if landmark.get('nodeId') not in node_by_id:
            raise InvalidBoardConfiguration(f'Landmark {landmark_id} referencia node inexistente.')
        if (
            landmark.get('type') == 'GAS_STATION'
            and 'FUEL_STATION' not in node_by_id[landmark['nodeId']].get('tags', [])
        ):
            raise InvalidBoardConfiguration(
                f'Posto {landmark_id} precisa referenciar uma casa de combustível.'
            )

    for route in routes:
        route_id = route.get('id')
        route_nodes = route.get('nodes')
        allowed_directions = route.get('allowedDirections')
        if not route_id or route_id in route_ids:
            raise InvalidBoardConfiguration('Os IDs das rotas devem ser únicos.')
        route_ids.add(route_id)
        if not isinstance(route_nodes, list) or len(route_nodes) < 2:
            raise InvalidBoardConfiguration(f'Rota {route_id} sem nodes suficientes.')
        if (
            not isinstance(allowed_directions, list)
            or not allowed_directions
            or any(direction not in (-1, 1) for direction in allowed_directions)
            or len(set(allowed_directions)) != len(allowed_directions)
        ):
            raise InvalidBoardConfiguration(
                f'Rota {route_id} precisa declarar sentidos válidos e únicos.'
            )
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
    routes = []
    for route in load_board()['routes']:
        direction = get_route_direction_from_city(route, city_id)
        if direction in route['allowedDirections']:
            routes.append(route)
    return routes


def get_route_direction_from_city(route: dict[str, Any], city_id: str) -> int | None:
    if city_id == route['nodes'][0]:
        return 1
    if city_id == route['nodes'][-1]:
        return -1
    return None
