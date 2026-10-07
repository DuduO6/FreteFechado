import json

from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .board import load_board
from .game_services import (
    GameActionError,
    create_game_session,
    roll_and_move,
    select_route,
    serialize_game,
)
from .models import GameSession
from .services import (
    InvalidPlayerNames,
    select_starting_player_index,
    validate_player_names,
)


def _read_json_object(request: HttpRequest) -> dict[str, object] | JsonResponse:
    try:
        payload = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return JsonResponse(
            {'ok': False, 'code': 'INVALID_JSON', 'message': 'O corpo da requisição deve ser um JSON válido.'},
            status=400,
        )
    if not isinstance(payload, dict):
        return JsonResponse(
            {'ok': False, 'code': 'INVALID_JSON', 'message': 'O corpo da requisição deve ser um objeto JSON.'},
            status=400,
        )
    return payload


def _action_error(error: GameActionError) -> JsonResponse:
    return JsonResponse(
        {'ok': False, 'code': error.code, 'message': str(error)},
        status=409,
    )


@csrf_exempt
@require_POST
def receive_player_names(request: HttpRequest) -> JsonResponse:
    payload = _read_json_object(request)
    if isinstance(payload, JsonResponse):
        return payload

    try:
        players = validate_player_names(payload.get('players'))
    except InvalidPlayerNames as error:
        return JsonResponse({'ok': False, 'message': str(error)}, status=400)

    starting_player_index = select_starting_player_index(players)
    game = create_game_session(players, starting_player_index)
    return JsonResponse(
        {
            'ok': True,
            'players': players,
            'startingPlayerIndex': starting_player_index,
            'snapshot': serialize_game(game),
        }
    )


@require_GET
def board_config(request: HttpRequest) -> JsonResponse:
    del request
    return JsonResponse({'ok': True, 'board': load_board()})


@require_GET
def game_detail(request: HttpRequest, game_id: str) -> JsonResponse:
    del request
    game = get_object_or_404(GameSession, id=game_id)
    return JsonResponse({'ok': True, 'snapshot': serialize_game(game)})


@csrf_exempt
@require_POST
def select_game_route(request: HttpRequest, game_id: str) -> JsonResponse:
    payload = _read_json_object(request)
    if isinstance(payload, JsonResponse):
        return payload
    try:
        game = select_route(
            game_id,
            str(payload.get('routeId', '')),
            int(payload.get('expectedPlayerIndex', -1)),
            int(payload.get('expectedRound', -1)),
        )
    except GameSession.DoesNotExist:
        return JsonResponse({'ok': False, 'code': 'GAME_NOT_FOUND', 'message': 'Partida não encontrada.'}, status=404)
    except (TypeError, ValueError) as error:
        if isinstance(error, GameActionError):
            return _action_error(error)
        return JsonResponse({'ok': False, 'code': 'INVALID_INPUT', 'message': 'Dados da ação inválidos.'}, status=400)
    return JsonResponse({'ok': True, 'snapshot': serialize_game(game)})


@csrf_exempt
@require_POST
def roll_game(request: HttpRequest, game_id: str) -> JsonResponse:
    payload = _read_json_object(request)
    if isinstance(payload, JsonResponse):
        return payload
    try:
        game, movement = roll_and_move(
            game_id,
            int(payload.get('expectedPlayerIndex', -1)),
            int(payload.get('expectedRound', -1)),
        )
    except GameSession.DoesNotExist:
        return JsonResponse({'ok': False, 'code': 'GAME_NOT_FOUND', 'message': 'Partida não encontrada.'}, status=404)
    except (TypeError, ValueError) as error:
        if isinstance(error, GameActionError):
            return _action_error(error)
        return JsonResponse({'ok': False, 'code': 'INVALID_INPUT', 'message': 'Dados da ação inválidos.'}, status=400)
    return JsonResponse(
        {'ok': True, 'snapshot': serialize_game(game), 'movement': movement}
    )
