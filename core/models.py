"""
Core Django Models for Sports Gala

Data Model Design:
- Game: represents a sport/event with multiple teams competing
- Team: represents a team participating in a game
- TeamMember: represents a person on a team (captain required per team)
- Match: represents a match between two teams with scores and results
- ScoreManagerProfile: profile linking users to games they can manage
- GameAward: flexible award types per game (1st Position, Best Catcher, etc.)
- LeaderboardCache: denormalized cache of team points for performance

Leaderboard Logic:
- Simple win/loss points system: Win = 3 points, Loss = 0 points
- LeaderboardCache table stores cumulative points, updated on each match save
- This denormalization avoids expensive aggregation on every page load
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import json


class Game(models.Model):
    """
    Represents a sport/game event in the gala.
    
    completed field: when True, score managers cannot make changes
    Only admin can revert from completed=True to completed=False
    display_order determines position in slideshow and menus
    """
    
    name = models.CharField(max_length=255, unique=True)
    completed = models.BooleanField(default=False, help_text="Mark as completed to lock the game from score manager edits")
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class Team(models.Model):
    """
    Represents a team in a game.
    
    Design: OneToOneField to Game (each team competes in one game)
    If we need teams across multiple games in future, change to ManyToMany
    For now: simpler schema, one team per game scenario
    """
    game = models.ForeignKey(Game, on_delete=models.SET_NULL, null=True, blank=True, related_name='teams')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        game_name = self.game.name if self.game else "No Game"
        return f"{self.name} ({game_name})"
    
    def get_captain(self):
        """Returns the captain of this team."""
        return self.members.filter(role='captain').first()
    
    def get_members(self):
        """Returns all members (excluding captain in the list, but captain is included)."""
        return self.members.all()


class TeamMember(models.Model):
    """
    Represents a person on a team.
    
    Captain is required per team (enforced at team level via model validation and forms)
    Members can be 0 or more
    """
    ROLE_CHOICES = [
        ('captain', 'Captain'),
        ('member', 'Member'),
    ]
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('team', 'name')
        ordering = ['-role', 'name']  # Captain first
    
    @property
    def is_captain(self):
        return self.role == 'captain'
    
    def __str__(self):
        return f"{self.name} ({self.role}) - {self.team.name}"


class Match(models.Model):
    """
    Represents a match between two teams.
    
    Includes scheduling, scoring, results, and bracket structure.
    
    Bracket Structure (Dynamic):
    - tournament_round: Auto-calculated based on match scheduling
      (Round 1 = initial matches, Round 2 = teams that played Round 1 and advanced, etc.)
    - bracket_position: Position within the round (0-indexed)
    - next_match: Points to the match this winner advances to (automatically calculated)
    
    Algorithm:
    1. Group matches by scheduled_at time window (e.g., 30-min intervals) → rounds
    2. Track which teams advance to next round (based on match results)
    3. Auto-link next_match when a team wins
    """
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ]

    STAGE_CHOICES = [
        ('quarter_final', 'Quarter Final'),
        ('semi_final', 'Semi Final'),
        ('final', 'Final'),
    ]
    
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='matches')
    team_a = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team_a', null=True, blank=True)
    team_b = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team_b', null=True, blank=True)
    scheduled_at = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    match_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, null=True, blank=True)
    
    # Scores
    score_a = models.PositiveIntegerField(default=0)
    score_b = models.PositiveIntegerField(default=0)
    
    # Winner (nullable for ongoing matches)
    winner_team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='won_matches'
    )
    
    # Bracket Structure - match_stage field now determines bracket organization
    # tournament_round field is deprecated - kept for backwards compatibility only
    tournament_round = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="DEPRECATED - Use match_stage field instead"
    )
    bracket_position = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Position within round (0-indexed)"
    )
    next_match = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='previous_matches',
        help_text="Match that the winner advances to"
    )
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_at']
        # Add indexes for common queries in admin
        indexes = [
            models.Index(fields=['game', 'scheduled_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        team_a_name = self.team_a.name if self.team_a else "TBD"
        team_b_name = self.team_b.name if self.team_b else "TBD"
        return f"{team_a_name} vs {team_b_name} ({self.game.name})"
    
    def clean(self):
        """Validate match data."""
        if self.team_a and self.team_b and self.team_a == self.team_b:
            raise ValidationError("A team cannot play against itself.")
        if self.team_a and self.team_a.game != self.game:
            raise ValidationError("Team A must be in the same game.")
        if self.team_b and self.team_b.game != self.game:
            raise ValidationError("Team B must be in the same game.")
        if self.winner_team and self.winner_team.game != self.game:
            raise ValidationError("Winner must be from the same game.")
        if self.next_match and self.next_match.game != self.game:
            raise ValidationError("Next match must be in the same game.")
    
    def determine_winner(self):
        """Auto-set winner based on scores."""
        if self.score_a > self.score_b:
            self.winner_team = self.team_a
        elif self.score_b > self.score_a:
            self.winner_team = self.team_b
        else:
            self.winner_team = None  # Draw


class ScoreManagerProfile(models.Model):
    """
    One-to-one profile linking a User to their score manager capabilities.
    
    assigned_games: M2M to games this manager can update scores for
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='score_manager_profile')
    assigned_games = models.ManyToManyField(Game, related_name='score_managers', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"ScoreManager: {self.user.username}"
    
    def can_manage_game(self, game):
        """Check if this manager can manage a specific game."""
        return game in self.assigned_games.all()


class GameAward(models.Model):
    """
    Flexible award types per game.
    
    Examples:
    - game=Cricket, award_label="1st Position", team=TeamA
    - game=Cricket, award_label="Best Catcher", member=PlayerX
    - game=Cricket, award_label="Best Batsman", member=PlayerY
    
    Allows multiple awards per game, each can be tied to a team or individual member
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='awards')
    award_label = models.CharField(max_length=255)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True)
    member = models.ForeignKey(TeamMember, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['game', 'award_label']
    
    def __str__(self):
        award_str = f"{self.award_label} ({self.game.name})"
        if self.team:
            award_str += f" - {self.team.name}"
        if self.member:
            award_str += f" - {self.member.name}"
        return award_str


class LeaderboardCache(models.Model):
    """
    Denormalized cache of team points for performance.
    
    Leaderboard Logic:
    - Win = 3 points
    - Loss = 0 points
    - Draw = 1 point (optional)
    
    This table is updated whenever a match is marked as completed or scores change.
    Avoids expensive aggregation queries on page load.
    
    Keyed by game + team
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='leaderboard_cache')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    points = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('game', 'team')
        ordering = ['-points', '-wins']
    
    def __str__(self):
        return f"{self.team.name} - {self.points}pts"
    
    @staticmethod
    def update_for_match(match):
        """Update leaderboard cache after a match is completed/updated."""
        if match.status != 'completed' or not match.winner_team:
            return
        
        # Update winner
        winner_cache, _ = LeaderboardCache.objects.get_or_create(
            game=match.game,
            team=match.winner_team
        )
        winner_cache.wins += 1
        winner_cache.points += 3
        winner_cache.save()
        
        # Update loser (team that didn't win)
        loser_team = match.team_b if match.winner_team == match.team_a else match.team_a
        loser_cache, _ = LeaderboardCache.objects.get_or_create(
            game=match.game,
            team=loser_team
        )
        loser_cache.losses += 1
        loser_cache.save()


class AvailableTeam(models.Model):
    """
    Tracks which teams are available for randomizer selection per game.
    
    This allows users to mark specific teams as 'available' for the day,
    and the randomizer will only pick from these teams.
    The list persists until manually cleared.
    """
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='available_teams')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='availability_records')
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['game', 'team']
        ordering = ['added_at']
    
    def __str__(self):
        return f"{self.team.name} available for {self.game.name}"
