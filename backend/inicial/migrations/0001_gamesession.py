import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='GameSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('players', models.JSONField()),
                ('current_player_index', models.PositiveSmallIntegerField()),
                ('current_round', models.PositiveSmallIntegerField(default=1)),
                ('turns_played_in_round', models.PositiveSmallIntegerField(default=0)),
                ('status', models.CharField(choices=[('PLAYING', 'Em andamento'), ('FINISHED', 'Finalizada')], default='PLAYING', max_length=16)),
                ('schema_version', models.PositiveSmallIntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
