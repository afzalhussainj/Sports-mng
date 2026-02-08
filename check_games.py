import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from core.models import Game
from django.db.models import Count

games = Game.objects.all()
print('All Games:')
for game in games:
    print(f'  ID: {game.id}, Name: {game.name}, Teams: {game.teams.count()}')

print()
duplicates = Game.objects.values('name').annotate(count=Count('id')).filter(count__gt=1)
if duplicates:
    print('Duplicate game names found:')
    for dup in duplicates:
        print(f'  {dup["name"]}: {dup["count"]} records')
        # Show the duplicate IDs
        dup_games = Game.objects.filter(name=dup['name'])
        for g in dup_games:
            print(f'    - ID: {g.id}')
else:
    print('No duplicate game names found.')
