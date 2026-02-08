"""Core app admin configuration"""
from django.contrib import admin
from django.contrib.auth.models import User
from core.models import (
    Game, Team, TeamMember, Match, ScoreManagerProfile,
    GameAward, LeaderboardCache, AvailableTeam
)


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['name', 'completed', 'display_order', 'created_at']
    list_editable = ['completed', 'display_order']
    search_fields = ['name']
    ordering = ['display_order']


class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 1


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'game', 'created_at']
    search_fields = ['name', 'game__name']
    list_filter = ['game']
    inlines = [TeamMemberInline]


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'team', 'role', 'created_at']
    search_fields = ['name', 'team__name']
    list_filter = ['team', 'role']


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['game', 'team_a', 'team_b', 'status', 'score_a', 'score_b', 'winner_team', 'scheduled_at']
    list_filter = ['game', 'status', 'scheduled_at']
    search_fields = ['team_a__name', 'team_b__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Match Info', {
            'fields': ('game', 'team_a', 'team_b', 'scheduled_at', 'location', 'status')
        }),
        ('Scoring', {
            'fields': ('score_a', 'score_b', 'winner_team')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GameAward)
class GameAwardAdmin(admin.ModelAdmin):
    list_display = ['award_label', 'game', 'team', 'member', 'created_at']
    list_filter = ['game']
    search_fields = ['award_label', 'team__name', 'member__name']


@admin.register(LeaderboardCache)
class LeaderboardCacheAdmin(admin.ModelAdmin):
    list_display = ['team', 'game', 'points', 'wins', 'losses']
    list_filter = ['game']
    search_fields = ['team__name']
    readonly_fields = ['updated_at']


class ScoreManagerProfileInline(admin.TabularInline):
    model = ScoreManagerProfile
    extra = 1
    filter_horizontal = ['assigned_games']


# Extend User admin to show score manager profile
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_staff', 'is_superuser']
    list_filter = ['is_staff', 'is_superuser']
    search_fields = ['username', 'email']
    fieldsets = (
        ('Personal Info', {
            'fields': ('username', 'email', 'first_name', 'last_name')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AvailableTeam)
class AvailableTeamAdmin(admin.ModelAdmin):
    list_display = ['team', 'game', 'added_at', 'added_by']
    list_filter = ['game', 'added_at']
    search_fields = ['team__name', 'game__name']
    readonly_fields = ['added_at', 'added_by']
