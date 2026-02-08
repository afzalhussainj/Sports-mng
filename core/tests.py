"""Tests for core app models and views"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from core.models import (
    Game, Team, TeamMember, Match, GameAward,
    ScheduledMessage, ScoreManagerProfile, LeaderboardCache
)


class GameModelTest(TestCase):
    """Test Game model"""
    
    def setUp(self):
        self.game = Game.objects.create(
            name='Cricket',
            description='A cricket tournament',
            status='upcoming',
            display_order=1
        )
    
    def test_game_creation(self):
        """Test creating a game"""
        self.assertEqual(self.game.name, 'Cricket')
        self.assertEqual(self.game.status, 'upcoming')
    
    def test_game_str(self):
        """Test game string representation"""
        self.assertEqual(str(self.game), 'Cricket')


class TeamModelTest(TestCase):
    """Test Team model"""
    
    def setUp(self):
        self.game = Game.objects.create(name='Cricket', status='upcoming', display_order=1)
        self.team = Team.objects.create(game=self.game, name='Team A')
    
    def test_team_creation(self):
        """Test creating a team"""
        self.assertEqual(self.team.name, 'Team A')
        self.assertEqual(self.team.game, self.game)
    
    def test_team_captain(self):
        """Test getting team captain"""
        # No captain yet
        self.assertIsNone(self.team.get_captain())
        
        # Add captain
        captain = TeamMember.objects.create(team=self.team, name='Captain', role='captain')
        self.assertEqual(self.team.get_captain(), captain)


class TeamMemberModelTest(TestCase):
    """Test TeamMember model"""
    
    def setUp(self):
        self.game = Game.objects.create(name='Cricket', status='upcoming', display_order=1)
        self.team = Team.objects.create(game=self.game, name='Team A')
    
    def test_captain_creation(self):
        """Test creating a captain"""
        captain = TeamMember.objects.create(team=self.team, name='Captain', role='captain')
        self.assertEqual(captain.role, 'captain')
    
    def test_member_creation(self):
        """Test creating a regular member"""
        member = TeamMember.objects.create(team=self.team, name='Player 1', role='member')
        self.assertEqual(member.role, 'member')


class MatchModelTest(TestCase):
    """Test Match model"""
    
    def setUp(self):
        self.game = Game.objects.create(name='Cricket', status='ongoing', display_order=1)
        self.team_a = Team.objects.create(game=self.game, name='Team A')
        self.team_b = Team.objects.create(game=self.game, name='Team B')
        
        self.match = Match.objects.create(
            game=self.game,
            team_a=self.team_a,
            team_b=self.team_b,
            scheduled_at=timezone.now() + timedelta(hours=1),
            location='Ground A',
            status='upcoming',
            score_a=0,
            score_b=0
        )
    
    def test_match_creation(self):
        """Test creating a match"""
        self.assertEqual(self.match.game, self.game)
        self.assertEqual(self.match.team_a, self.team_a)
        self.assertEqual(self.match.team_b, self.team_b)
        self.assertEqual(self.match.status, 'upcoming')
    
    def test_same_team_validation(self):
        """Test that a team cannot play against itself"""
        from django.core.exceptions import ValidationError
        
        invalid_match = Match(
            game=self.game,
            team_a=self.team_a,
            team_b=self.team_a,
            scheduled_at=timezone.now(),
            status='upcoming'
        )
        
        with self.assertRaises(ValidationError):
            invalid_match.full_clean()
    
    def test_determine_winner(self):
        """Test auto-determining winner"""
        self.match.score_a = 120
        self.match.score_b = 100
        self.match.determine_winner()
        
        self.assertEqual(self.match.winner_team, self.team_a)


class AuthenticationTest(TestCase):
    """Test authentication and authorization"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        self.score_manager_user = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='manager123'
        )
        ScoreManagerProfile.objects.create(user=self.score_manager_user)
    
    def test_public_dashboard_no_auth(self):
        """Test public dashboard is accessible without authentication"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_login_page(self):
        """Test login page loads"""
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)
    
    def test_admin_panel_requires_auth(self):
        """Test admin panel requires authentication"""
        response = self.client.get('/manager/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_admin_panel_admin_only(self):
        """Test admin panel is only for admins"""
        self.client.login(username='manager', password='manager123')
        response = self.client.get('/manager/')
        self.assertEqual(response.status_code, 302)  # Redirect
    
    def test_admin_login(self):
        """Test admin can login"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get('/manager/')
        self.assertEqual(response.status_code, 200)


class APIEndpointTest(TestCase):
    """Test API endpoints"""
    
    def setUp(self):
        self.game = Game.objects.create(name='Cricket', status='ongoing', display_order=1)
        self.team_a = Team.objects.create(game=self.game, name='Team A')
        self.team_b = Team.objects.create(game=self.game, name='Team B')
        
        # Add captain
        TeamMember.objects.create(team=self.team_a, name='Captain A', role='captain')
        TeamMember.objects.create(team=self.team_b, name='Captain B', role='captain')
    
    def test_game_detail_api(self):
        """Test game detail API endpoint"""
        response = self.client.get(f'/api/games/{self.game.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Cricket')
        self.assertEqual(len(data['teams']), 2)
    
    def test_leaderboard_api(self):
        """Test leaderboard API endpoint"""
        response = self.client.get(f'/api/games/{self.game.id}/leaderboard/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('leaderboard', data)


class LeaderboardCacheTest(TestCase):
    """Test leaderboard caching"""
    
    def setUp(self):
        self.game = Game.objects.create(name='Cricket', status='completed', display_order=1)
        self.team_a = Team.objects.create(game=self.game, name='Team A')
        self.team_b = Team.objects.create(game=self.game, name='Team B')
        
        self.match = Match.objects.create(
            game=self.game,
            team_a=self.team_a,
            team_b=self.team_b,
            scheduled_at=timezone.now(),
            status='completed',
            score_a=100,
            score_b=80,
            winner_team=self.team_a
        )
    
    def test_leaderboard_update(self):
        """Test leaderboard cache is updated on match completion"""
        LeaderboardCache.update_for_match(self.match)
        
        winner_cache = LeaderboardCache.objects.get(game=self.game, team=self.team_a)
        self.assertEqual(winner_cache.wins, 1)
        self.assertEqual(winner_cache.points, 3)
        
        loser_cache = LeaderboardCache.objects.get(game=self.game, team=self.team_b)
        self.assertEqual(loser_cache.losses, 1)
        self.assertEqual(loser_cache.points, 0)
