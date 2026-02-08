from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_add_bracket_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='match_stage',
            field=models.CharField(blank=True, choices=[('quarter_final', 'Quarter Final'), ('semi_final', 'Semi Final'), ('final', 'Final')], max_length=20, null=True),
        ),
    ]
