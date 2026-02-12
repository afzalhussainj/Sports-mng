from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Game, Team, TeamMember, Match


class Command(BaseCommand):
    help = 'Create Tekken tournament matches'

    def handle(self, *args, **options):
        # Create or get the Tekken game
        game, created = Game.objects.get_or_create(
            name='Tekken',
            defaults={'icon': '🎮'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created game: {game.name}'))
        else:
            self.stdout.write(f'Game already exists: {game.name}')
            # Delete existing incomplete data
            existing_matches = Match.objects.filter(game=game)
            if existing_matches.exists():
                self.stdout.write(f'Found {existing_matches.count()} existing matches, deleting...')
                existing_matches.delete()
            existing_teams = Team.objects.filter(game=game)
            if existing_teams.exists():
                self.stdout.write(f'Found {existing_teams.count()} existing teams, deleting...')
                existing_teams.delete()

        # Team data with members
        team_data = {
            'moiez': ['moiez'],
            'Khizer': ['Khizer'],
            'Khawajah Shahoud Murtazah': ['Khawajah Shahoud Murtazah'],
            'mahad': ['mahad'],
            'afzal': ['afzal'],
            'shaheer': ['shaheer'],
            'Hamza': ['Hamza'],
            'huraira': ['huraira'],
        }

        # Create teams
        teams = {}
        for team_name, members in team_data.items():
            team = Team.objects.create(
                name=team_name,
                game=game
            )
            self.stdout.write(self.style.SUCCESS(f'Created team: {team.name}'))
            
            # Add members
            for member_name in members:
                member = TeamMember.objects.create(
                    team=team,
                    name=member_name,
                    role='captain'
                )
                self.stdout.write(f'  Created member: {member.name}')
            
            teams[team_name] = team

        # Match data: (team_a, team_b, winner, score_a, score_b, stage)
        matches = [
            # Quarter Finals
            ('moiez', 'Khizer', 'moiez', 3, 0, 'quarter_final'),
            ('Khawajah Shahoud Murtazah', 'mahad', 'Khawajah Shahoud Murtazah', 3, 1, 'quarter_final'),
            ('afzal', 'shaheer', 'afzal', 3, 2, 'quarter_final'),
            ('Hamza', 'huraira', 'Hamza', 3, 1, 'quarter_final'),
            # Semi Finals
            ('moiez', 'Khawajah Shahoud Murtazah', 'moiez', 3, 1, 'semi_final'),
            ('afzal', 'Hamza', 'afzal', 3, 2, 'semi_final'),
        ]

        # Create matches
        for team_a_name, team_b_name, winner_name, score_a, score_b, match_stage in matches:
            team_a = teams[team_a_name]
            team_b = teams[team_b_name]
            winner_team = teams[winner_name]
            
            match = Match.objects.create(
                game=game,
                team_a=team_a,
                team_b=team_b,
                match_stage=match_stage,
                scheduled_at=timezone.now(),
                score_a=score_a,
                score_b=score_b,
                status='completed',
                winner_team=winner_team
            )
            
            self.stdout.write(self.style.SUCCESS(
                f'Created {match_stage} match: {team_a_name} vs {team_b_name} (Winner: {winner_name}, {score_a}-{score_b})'
            ))

        self.stdout.write(self.style.SUCCESS('\n✅ Tekken tournament setup complete!'))
