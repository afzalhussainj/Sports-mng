from core.models import Game, Team, TeamMember

game = Game.objects.get(name='Tekken')
print(f'\nTekken Teams:')
for team in Team.objects.filter(game=game):
    print(f'  Team ID {team.id}: {team.name}')
    for member in team.members.all():
        print(f'    - Member ID {member.id}: {member.name} ({member.role})')
