from django.db import migrations, models


MAX_FUEL = 5


def add_fuel_and_event_information(apps, schema_editor):
    del schema_editor
    GameSession = apps.get_model('inicial', 'GameSession')
    for game in GameSession.objects.all().iterator():
        players = []
        for player in game.players:
            normalized_player = dict(player)
            normalized_player.setdefault('fuel', MAX_FUEL)
            normalized_player.setdefault('fuelDistance', 0)
            normalized_player.setdefault('fuelVoucher', False)
            normalized_player.setdefault('nextMovePenalty', 0)
            normalized_player.setdefault('pendingRefuel', None)
            normalized_player.setdefault('pendingProblemCard', None)
            players.append(normalized_player)
        game.players = players
        game.schema_version = 3
        game.save(update_fields=['players', 'schema_version'])


class Migration(migrations.Migration):
    dependencies = [('inicial', '0002_player_information')]

    operations = [
        migrations.AlterField(
            model_name='gamesession',
            name='schema_version',
            field=models.PositiveSmallIntegerField(default=3),
        ),
        migrations.RunPython(
            add_fuel_and_event_information,
            migrations.RunPython.noop,
        ),
    ]
