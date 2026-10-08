from django.urls import path

from .views import (
    acknowledge_game_event,
    board_config,
    game_detail,
    receive_player_names,
    refuel_game,
    roll_game,
    select_game_route,
)

app_name = 'inicial'

urlpatterns = [
    path('players/', receive_player_names, name='receive-player-names'),
    path('board/', board_config, name='board-config'),
    path('games/<uuid:game_id>/', game_detail, name='game-detail'),
    path('games/<uuid:game_id>/route/', select_game_route, name='select-game-route'),
    path('games/<uuid:game_id>/roll/', roll_game, name='roll-game'),
    path('games/<uuid:game_id>/refuel/', refuel_game, name='refuel-game'),
    path('games/<uuid:game_id>/event/acknowledge/', acknowledge_game_event, name='acknowledge-game-event'),
]
