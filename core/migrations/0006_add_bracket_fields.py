# Generated migration for bracket fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_availableteam'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='tournament_round',
            field=models.PositiveIntegerField(blank=True, null=True, help_text='Auto-calculated round based on scheduling (1 = initial, 2 = next, etc.)'),
        ),
        migrations.AddField(
            model_name='match',
            name='bracket_position',
            field=models.PositiveIntegerField(blank=True, null=True, help_text='Position within round (0-indexed)'),
        ),
        migrations.AddField(
            model_name='match',
            name='next_match',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='previous_matches', to='core.match', help_text='Match that the winner advances to'),
        ),
    ]
