from django.db import migrations, models


ROUTE_ID_MAP = {
    'ROUTE_SUL_TRIANGULO': 'ROUTE_TRIANGULO_NORTE',
    'ROUTE_TRIANGULO_NORTE': 'ROUTE_NORTE_ZONA',
    'ROUTE_NORTE_ZONA': 'ROUTE_ZONA_SUL',
    'ROUTE_ZONA_SUL': 'ROUTE_SUL_TRIANGULO',
    'ROUTE_BH_SUL': 'ROUTE_BH_TRIANGULO',
    'ROUTE_BH_TRIANGULO': 'ROUTE_BH_NORTE_DIRT',
    'ROUTE_BH_ZONA': 'ROUTE_BH_SUL',
}

NODE_ID_MAP = {
    'CITY_SUL': 'CITY_TRIANGULO',
    'CITY_TRIANGULO': 'CITY_NORTE',
    'CITY_NORTE': 'CITY_ZONA_MATA',
    'CITY_ZONA_MATA': 'CITY_SUL',
    'H_SUL_TRI_01': 'H_TRI_NORTE_01',
    'H_SUL_TRI_02': 'H_TRI_NORTE_02',
    'H_SUL_TRI_03': 'H_TRI_NORTE_02',
    'H_SUL_TRI_04': 'H_TRI_NORTE_03',
    'H_SUL_TRI_05': 'H_TRI_NORTE_04',
    'H_SUL_TRI_06': 'H_TRI_NORTE_05',
    'H_SUL_TRI_07': 'H_TRI_NORTE_06',
    'H_SUL_TRI_08': 'H_TRI_NORTE_07',
    'H_TRI_NORTE_01': 'H_NORTE_ZONA_01',
    'H_TRI_NORTE_02': 'H_NORTE_ZONA_02',
    'H_TRI_NORTE_03': 'H_NORTE_ZONA_03',
    'H_TRI_NORTE_04': 'H_NORTE_ZONA_04',
    'H_TRI_NORTE_05': 'H_NORTE_ZONA_05',
    'H_NORTE_ZONA_01': 'H_ZONA_SUL_02',
    'H_NORTE_ZONA_02': 'H_ZONA_SUL_03',
    'H_NORTE_ZONA_03': 'H_ZONA_SUL_04',
    'H_NORTE_ZONA_04': 'H_ZONA_SUL_05',
    'H_NORTE_ZONA_05': 'H_ZONA_SUL_06',
    'H_NORTE_ZONA_06': 'H_ZONA_SUL_09',
    'H_NORTE_ZONA_07': 'H_ZONA_SUL_10',
    'H_NORTE_ZONA_08': 'H_ZONA_SUL_11',
    'H_NORTE_ZONA_09': 'H_ZONA_SUL_12',
    'H_ZONA_SUL_01': 'H_SUL_TRI_02',
    'H_ZONA_SUL_02': 'H_SUL_TRI_03',
    'H_ZONA_SUL_03': 'H_SUL_TRI_04',
    'H_ZONA_SUL_04': 'H_SUL_TRI_05',
    'H_ZONA_SUL_05': 'H_SUL_TRI_06',
    'H_ZONA_SUL_06': 'H_SUL_TRI_07',
    'H_ZONA_SUL_07': 'H_SUL_TRI_08',
    'H_ZONA_SUL_08': 'H_SUL_TRI_09',
    'D_WEST_TRI_01': 'D_WEST_NORTE_01',
    'D_WEST_TRI_02': 'D_WEST_NORTE_02',
    'D_WEST_TRI_03': 'D_WEST_NORTE_03',
    'D_WEST_TRI_04': 'D_WEST_NORTE_04',
    'D_BH_ZONA_01': 'D_BH_SUL_01',
    'D_BH_ZONA_02': 'D_BH_SUL_02',
    'D_BH_ZONA_03': 'D_BH_SUL_03',
    'D_BH_ZONA_04': 'D_BH_SUL_04',
    'D_BH_ZONA_05': 'D_BH_SUL_05',
}


def migrate_board_positions(apps, schema_editor):
    del schema_editor
    GameSession = apps.get_model('inicial', 'GameSession')
    for game in GameSession.objects.all().iterator():
        players = []
        for player in game.players:
            migrated_player = dict(player)
            migrated_player['position'] = NODE_ID_MAP.get(
                migrated_player.get('position'),
                migrated_player.get('position'),
            )
            active_route_id = migrated_player.get('activeRouteId')
            migrated_player['activeRouteId'] = ROUTE_ID_MAP.get(
                active_route_id,
                active_route_id,
            )
            if migrated_player.get('pendingRefuel'):
                migrated_player['position'] = 'H_TRI_NORTE_02'
                migrated_player['activeRouteId'] = 'ROUTE_TRIANGULO_NORTE'
                migrated_player['routeDirection'] = 1
            players.append(migrated_player)
        game.players = players
        game.schema_version = 4
        game.save(update_fields=['players', 'schema_version'])


class Migration(migrations.Migration):
    dependencies = [('inicial', '0003_fuel_and_events')]

    operations = [
        migrations.AlterField(
            model_name='gamesession',
            name='schema_version',
            field=models.PositiveSmallIntegerField(default=4),
        ),
        migrations.RunPython(migrate_board_positions, migrations.RunPython.noop),
    ]
