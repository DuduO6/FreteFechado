import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import InvalidPlayerNames, validate_player_names


@csrf_exempt
@require_POST
def receive_player_names(request: HttpRequest) -> JsonResponse:
    try:
        payload = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return JsonResponse(
            {'ok': False, 'message': 'O corpo da requisição deve ser um JSON válido.'},
            status=400,
        )

    if not isinstance(payload, dict):
        return JsonResponse(
            {'ok': False, 'message': 'O corpo da requisição deve ser um objeto JSON.'},
            status=400,
        )

    try:
        players = validate_player_names(payload.get('players'))
    except InvalidPlayerNames as error:
        return JsonResponse({'ok': False, 'message': str(error)}, status=400)

    return JsonResponse({'ok': True, 'players': players})
