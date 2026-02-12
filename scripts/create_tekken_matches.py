import os
import django

os.chdir(r'c:\Users\SLCW\Desktop\sports\sports_gala')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from core.models import Game, Team, TeamMember, Match

# Get or create Tekken game
game, created = Game.objects.get_or_create(name='Tekken', defaults={'display_order': 100})
print(f"Game: {game.name} ({'created' if created else 'found'})")

# Teams and captains
teams_data = [
    'moiez', 'Khizer', 'Khawajah Shahoud Murtazah', 'mahad',
    'afzal', 'shaheer', 'Hamza', 'huraira'
]

teams = {}
for team_name in teams_data:
    team, created = Team.objects.get_or_create(game=game, name=team_name)
    print(f"  Team: {team.name} ({'created' if created else 'found'})")
    
    # Ensure captain
    captain, created = TeamMember.objects.get_or_create(
        team=team,
        name=team_name,
        defaults={'role': 'captain'}
    )
    if not created and captain.role != 'captain':
        captain.role = 'captain'
        captain.save()
        print(f"    Captain: {captain.name} (updated)")
    else:
        print(f"    Captain: {captain.name} ({'created' if created else 'found'})")
    
    teams[team_name] = team

# Matches: quarter finals
matches_quarter = [
    ('moiez', 'afzal', 'moiez', 'Quarter Finals'),
    ('Khizer', 'shaheer', 'Khizer', 'Quarter Finals'),
    ('Khawajah Shahoud Murtazah', 'Hamza', 'Khawajah Shahoud Murtazah', 'Quarter Finals'),
    ('mahad', 'huraira', 'mahad', 'Quarter Finals'),
]

# Matches: semi finals
matches_semi = [
    ('moiez', 'Khizer', 'moiez', 'Semi Finals'),
    ('Khawajah Shahoud Murtazah', 'mahad', 'Khawajah Shahoud Murtazah', 'Semi Finals'),
]

all_matches = matches_quarter + matches_semi

for team_a_name, team_b_name, winner_name, stage in all_matches:
    team_a = teams[team_a_name]
    team_b = teams[team_b_name]
    winner = teams[winner_name]
    
    match, created = Match.objects.get_or_create(
        game=game,
        team_a=team_a,
        team_b=team_b,
        stage=stage,
        defaults={
            'status': 'completed',
            'winner_team': winner,
            'score_a': 1 if winner == team_a else 0,
            'score_b': 1 if winner == team_b else 0,
        }
    )
    
    if not created:
        match.status = 'completed'
        match.winner_team = winner
        match.score_a = 1 if winner == team_a else 0
        match.score_b = 1 if winner == team_b else 0
        match.save()
        print(f"Match updated: {team_a_name} vs {team_b_name} ({stage}) -> {winner_name}")
    else:
        print(f"Match created: {team_a_name} vs {team_b_name} ({stage}) -> {winner_name}")

print("\nDone! All Tekken matches created.")
