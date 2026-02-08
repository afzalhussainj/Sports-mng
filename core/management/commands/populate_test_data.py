"""
Management command to populate test bracket data.

Creates:
- Test game with 16 teams
- Quarter final matches (8 matches)
- Semi final matches (4 matches) 
- Final match (1 match)
- Some completed matches with winners showing bracket progression
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Game, Team, Match, LeaderboardCache
from core.bracket_utils import calculate_tournament_rounds


class Command(BaseCommand):
    help = 'Populate test bracket data for testing'

    def handle(self, *args, **options):
        # Check if test data already exists
        game = Game.objects.filter(name='Test Tournament').first()
        if game:
            self.stdout.write(self.style.WARNING('Test game already exists. Skipping...'))
            return

        # Create test game
        game = Game.objects.create(
            name='Test Tournament',
            completed=False,
            display_order=1
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created game: {game.name}'))

        # Create 16 teams
        teams = []
        team_names = [
            'Phoenix Rising', 'Dragon Force', 'Tiger Squad', 'Eagle Warriors',
            'Lion Pride', 'Wolf Pack', 'Bear Strength', 'Shark Finz',
            'Falcon Flyers', 'Viper Vipers', 'Puma Power', 'Cheetah Chase',
            'Hawk Vision', 'Cobra Kings', 'Leopard Legends', 'Panther Fury'
        ]
        
        for name in team_names:
            team = Team.objects.create(game=game, name=name)
            teams.append(team)
            # Create leaderboard cache entry
            LeaderboardCache.objects.create(
                game=game,
                team=team,
                points=0,
                wins=0,
                losses=0,
                draws=0
            )
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(teams)} teams'))

        # Create matches - Quarter Finals (8 matches)
        now = timezone.now()
        base_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
        
        quarter_final_matches = []
        for i in range(0, 16, 2):
            match = Match.objects.create(
                game=game,
                team_a=teams[i],
                team_b=teams[i + 1],
                scheduled_at=base_time + timedelta(days=1, hours=i//2),
                location=f'Court {i//2 + 1}',
                status='upcoming',
                match_stage='quarter_final',
                notes=f'Quarter Final Match {i//2 + 1}'
            )
            quarter_final_matches.append(match)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(quarter_final_matches)} Quarter Final matches'))

        # Create Semi Finals (4 matches) - scheduled 3 days later
        semi_final_matches = []
        semi_base_time = base_time + timedelta(days=3)
        for i in range(0, 8, 2):
            match = Match.objects.create(
                game=game,
                team_a=None,  # Will be filled by winners
                team_b=None,
                scheduled_at=semi_base_time + timedelta(hours=i//2),
                location=f'Court {i//2 + 1}',
                status='upcoming',
                match_stage='semi_final',
                notes=f'Semi Final Match {i//2 + 1}'
            )
            semi_final_matches.append(match)
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(semi_final_matches)} Semi Final matches'))

        # Create Final (1 match) - scheduled 7 days later
        final_match = Match.objects.create(
            game=game,
            team_a=None,  # Will be filled by winners
            team_b=None,
            scheduled_at=base_time + timedelta(days=7),
            location='Grand Arena',
            status='upcoming',
            match_stage='final',
            notes='Tournament Final'
        )
        self.stdout.write(self.style.SUCCESS(f'✓ Created Final match'))

        # Complete some quarter final matches to show bracket progression
        # Complete first 2 quarter finals with winners
        quarter_final_matches[0].status = 'completed'
        quarter_final_matches[0].score_a = 3
        quarter_final_matches[0].score_b = 1
        quarter_final_matches[0].winner_team = teams[0]  # Phoenix Rising wins
        quarter_final_matches[0].save()

        quarter_final_matches[1].status = 'completed'
        quarter_final_matches[1].score_a = 2
        quarter_final_matches[1].score_b = 2
        quarter_final_matches[1].winner_team = teams[3]  # Eagle Warriors wins (on tiebreaker)
        quarter_final_matches[1].save()

        quarter_final_matches[2].status = 'completed'
        quarter_final_matches[2].score_a = 4
        quarter_final_matches[2].score_b = 0
        quarter_final_matches[2].winner_team = teams[4]  # Lion Pride wins
        quarter_final_matches[2].save()

        quarter_final_matches[3].status = 'completed'
        quarter_final_matches[3].score_a = 1
        quarter_final_matches[3].score_b = 3
        quarter_final_matches[3].winner_team = teams[7]  # Shark Finz wins
        quarter_final_matches[3].save()

        self.stdout.write(self.style.SUCCESS(f'✓ Completed 4 Quarter Final matches with winners'))

        # Update semi finals with completed quarter final winners
        semi_final_matches[0].team_a = teams[0]  # Phoenix Rising
        semi_final_matches[0].team_b = teams[3]  # Eagle Warriors
        semi_final_matches[0].save()

        semi_final_matches[1].team_a = teams[4]  # Lion Pride
        semi_final_matches[1].team_b = teams[7]  # Shark Finz
        semi_final_matches[1].save()

        # Complete one semi final
        semi_final_matches[0].status = 'completed'
        semi_final_matches[0].score_a = 2
        semi_final_matches[0].score_b = 1
        semi_final_matches[0].winner_team = teams[0]  # Phoenix Rising wins
        semi_final_matches[0].save()

        self.stdout.write(self.style.SUCCESS(f'✓ Updated Semi Final matches with winners and completed 1'))

        # Update final with semi final winner
        final_match.team_a = teams[0]  # Phoenix Rising
        final_match.team_b = None  # Waiting for other semi final winner
        final_match.save()

        self.stdout.write(self.style.SUCCESS(f'✓ Updated Final match'))

        # Update leaderboard cache for teams with wins
        for team in [teams[0], teams[3], teams[4], teams[7]]:
            cache = LeaderboardCache.objects.get(game=game, team=team)
            cache.wins = 1
            cache.points = 3
            cache.save()

        self.stdout.write(self.style.SUCCESS(f'✓ Updated leaderboard cache'))

        self.stdout.write(self.style.SUCCESS('\n✅ Test bracket data created successfully!\n'))
        self.stdout.write(self.style.WARNING('Summary:'))
        self.stdout.write(f'  • Game: {game.name}')
        self.stdout.write(f'  • Teams: 16')
        self.stdout.write(f'  • Quarter Finals: 8 matches (4 completed)')
        self.stdout.write(f'  • Semi Finals: 4 matches (1 completed)')
        self.stdout.write(f'  • Final: 1 match')
        self.stdout.write(f'\nYou should now see a bracket with completed Quarter and Semi Final rounds!')
