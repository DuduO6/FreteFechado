from django.urls import path

from .views import (
    board_config,
    game_detail,
    receive_player_names,
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
]
