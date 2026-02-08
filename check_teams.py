import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from core.models import Team, Game

print('Teams by Game:')
print()

for game in Game.objects.all():
    teams = Team.objects.filter(game=game)
    print(f'{game.name} (ID: {game.id}):')
    for team in teams:
        print(f'  - {team.name} (ID: {team.id})')
    print()

print('Teams with no game assigned:')
teams_no_game = Team.objects.filter(game__isnull=True)
if teams_no_game.exists():
    for team in teams_no_game:
        print(f'  - {team.name} (ID: {team.id})')
else:
    print('  None')
