from django.urls import path

from .views import receive_player_names

app_name = 'inicial'

urlpatterns = [
    path('players/', receive_player_names, name='receive-player-names'),
]
