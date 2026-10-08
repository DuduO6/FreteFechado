from django.db import migrations, models


INITIAL_BALANCE = 1000
PLAYER_COLORS = ('#e63f2e', '#237edb', '#f3b51b', '#7b45bf')


def add_player_information(apps, schema_editor):
    del schema_editor
    GameSession = apps.get_model('inicial', 'GameSession')
    for game in GameSession.objects.all().iterator():
        players = []
        for index, player in enumerate(game.players):
            normalized_player = dict(player)
            normalized_player.setdefault('turnOrder', index + 1)
            normalized_player.setdefault('balance', INITIAL_BALANCE)
            normalized_player.setdefault('hasValidContract', False)
            normalized_player.setdefault('color', PLAYER_COLORS[index])
            normalized_player.setdefault('spacesTraveled', 0)
            players.append(normalized_player)
        game.players = players
        game.schema_version = 2
        game.save(update_fields=['players', 'schema_version'])


class Migration(migrations.Migration):
    dependencies = [('inicial', '0001_gamesession')]

    operations = [
        migrations.AlterField(
            model_name='gamesession',
            name='schema_version',
            field=models.PositiveSmallIntegerField(default=2),
        ),
        migrations.RunPython(add_player_information, migrations.RunPython.noop),
    ]
