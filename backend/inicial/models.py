import uuid

from django.db import models


class GameSession(models.Model):
    class Status(models.TextChoices):
        PLAYING = 'PLAYING', 'Em andamento'
        FINISHED = 'FINISHED', 'Finalizada'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    players = models.JSONField()
    current_player_index = models.PositiveSmallIntegerField()
    current_round = models.PositiveSmallIntegerField(default=1)
    turns_played_in_round = models.PositiveSmallIntegerField(default=0)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PLAYING,
    )
    schema_version = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
