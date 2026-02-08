"""
Management command to seed sample data for development.

Usage:
    python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from core.models import (
    Game, Team, TeamMember, Match, GameAward,
    ScheduledMessage, ScoreManagerProfile, LeaderboardCache
)


class Command(BaseCommand):
    help = 'Seed database with sample data for testing'

    def handle(self, *args, **options):
        # Clear existing data (optional)
        # Game.objects.all().delete()

        self.stdout.write('Creating sample data...')

        # Create games
        cricket = Game.objects.get_or_create(
            name='Cricket',
            defaults={'description': '20 over cricket tournament', 'status': 'upcoming', 'display_order': 1}
        )[0]

        badminton = Game.objects.get_or_create(
            name='Badminton',
            defaults={'description': 'Badminton singles tournament', 'status': 'upcoming', 'display_order': 2}
        )[0]

        football = Game.objects.get_or_create(
            name='Football',
            defaults={'description': '7-a-side football', 'status': 'upcoming', 'display_order': 3}
        )[0]

        self.stdout.write(f'✓ Created games: {cricket.name}, {badminton.name}, {football.name}')

        # Create teams for Cricket
        team_a, _ = Team.objects.get_or_create(game=cricket, name='Team Alpha')
        team_b, _ = Team.objects.get_or_create(game=cricket, name='Team Beta')

        # Create team members for Cricket
        captain_a, _ = TeamMember.objects.get_or_create(
            team=team_a, name='Player A1',
            defaults={'role': 'captain'}
        )
        TeamMember.objects.get_or_create(team=team_a, name='Player A2', defaults={'role': 'member'})
        TeamMember.objects.get_or_create(team=team_a, name='Player A3', defaults={'role': 'member'})

        captain_b, _ = TeamMember.objects.get_or_create(
            team=team_b, name='Player B1',
            defaults={'role': 'captain'}
        )
        TeamMember.objects.get_or_create(team=team_b, name='Player B2', defaults={'role': 'member'})
        TeamMember.objects.get_or_create(team=team_b, name='Player B3', defaults={'role': 'member'})

        # Create teams for Badminton
        team_c, _ = Team.objects.get_or_create(game=badminton, name='Team Gamma')
        team_d, _ = Team.objects.get_or_create(game=badminton, name='Team Delta')

        captain_c, _ = TeamMember.objects.get_or_create(
            team=team_c, name='Player C1',
            defaults={'role': 'captain'}
        )
        TeamMember.objects.get_or_create(team=team_c, name='Player C2', defaults={'role': 'member'})

        captain_d, _ = TeamMember.objects.get_or_create(
            team=team_d, name='Player D1',
            defaults={'role': 'captain'}
        )
        TeamMember.objects.get_or_create(team=team_d, name='Player D2', defaults={'role': 'member'})

        # Create teams for Football
        team_e, _ = Team.objects.get_or_create(game=football, name='Team Echo')
        team_f, _ = Team.objects.get_or_create(game=football, name='Team Foxtrot')

        captain_e, _ = TeamMember.objects.get_or_create(
            team=team_e, name='Player E1',
            defaults={'role': 'captain'}
        )
        for i in range(2, 8):
            TeamMember.objects.get_or_create(team=team_e, name=f'Player E{i}', defaults={'role': 'member'})

        captain_f, _ = TeamMember.objects.get_or_create(
            team=team_f, name='Player F1',
            defaults={'role': 'captain'}
        )
        for i in range(2, 8):
            TeamMember.objects.get_or_create(team=team_f, name=f'Player F{i}', defaults={'role': 'member'})

        self.stdout.write('✓ Created teams and members')

        # Create matches
        now = timezone.now()
        
        match1, created = Match.objects.get_or_create(
            game=cricket,
            team_a=team_a,
            team_b=team_b,
            defaults={
                'scheduled_at': now + timedelta(hours=1),
                'location': 'Ground A',
                'status': 'upcoming',
                'score_a': 0,
                'score_b': 0,
            }
        )
        if created:
            self.stdout.write('✓ Created Cricket match: Team Alpha vs Team Beta')

        # Create a completed match with results
        match2, created = Match.objects.get_or_create(
            game=badminton,
            team_a=team_c,
            team_b=team_d,
            defaults={
                'scheduled_at': now - timedelta(hours=2),
                'location': 'Court B',
                'status': 'completed',
                'score_a': 21,
                'score_b': 15,
                'winner_team': team_c,
            }
        )
        if created:
            self.stdout.write('✓ Created Badminton match (completed): Team Gamma vs Team Delta')
            # Update leaderboard
            LeaderboardCache.update_for_match(match2)

        # Create Football matches
        match3, _ = Match.objects.get_or_create(
            game=football,
            team_a=team_e,
            team_b=team_f,
            defaults={
                'scheduled_at': now + timedelta(hours=4),
                'location': 'Field C',
                'status': 'upcoming',
                'score_a': 0,
                'score_b': 0,
            }
        )

        self.stdout.write('✓ Created matches')

        # Create scheduled messages
        msg1, _ = ScheduledMessage.objects.get_or_create(
            title='Welcome to Sports Gala',
            defaults={
                'message': 'Welcome to the annual departmental sports festival! All games will be held on the main grounds.',
                'start_time': now,
                'end_time': now + timedelta(hours=24),
                'active': True,
                'display_order': 1,
            }
        )

        msg2, _ = ScheduledMessage.objects.get_or_create(
            title='Cricket Match Starting Soon',
            defaults={
                'message': 'Cricket match between Team Alpha and Team Beta will start in 1 hour at Ground A.',
                'start_time': now + timedelta(minutes=30),
                'end_time': now + timedelta(hours=3),
                'active': True,
                'display_order': 2,
            }
        )

        self.stdout.write('✓ Created scheduled messages')

        # Create awards
        GameAward.objects.get_or_create(
            game=badminton,
            award_label='1st Position',
            defaults={'team': team_c, 'notes': 'Best performance in tournament'}
        )

        GameAward.objects.get_or_create(
            game=badminton,
            award_label='Best Player',
            defaults={'member': captain_c, 'notes': 'Exceptional performance'}
        )

        self.stdout.write('✓ Created awards')

        # Create admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@sportsgala.local',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('✓ Created admin user (username: admin, password: admin123)')

        # Create score manager users
        manager_user, created = User.objects.get_or_create(
            username='scoremanager',
            defaults={
                'email': 'manager@sportsgala.local',
                'is_staff': False,
                'is_superuser': False,
            }
        )
        if created:
            manager_user.set_password('manager123')
            manager_user.save()
            self.stdout.write('✓ Created score manager user (username: scoremanager, password: manager123)')

        # Create score manager profile
        profile, _ = ScoreManagerProfile.objects.get_or_create(user=manager_user)
        profile.assigned_games.set([cricket, badminton])
        self.stdout.write('✓ Assigned score manager to Cricket and Badminton')

        self.stdout.write(self.style.SUCCESS('✓ Database seeding completed!'))
        self.stdout.write('\nTest credentials:')
        self.stdout.write('  Admin: admin / admin123')
        self.stdout.write('  Score Manager: scoremanager / manager123')
