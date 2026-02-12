"""Forms for core app"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.forms import inlineformset_factory
from core.models import (
    Game, Team, TeamMember, Match, GameAward, ScoreManagerProfile
)
import time


# Cache for team options to avoid repeated database queries in form rendering
_TEAM_OPTIONS_CACHE = {}
_TEAM_OPTIONS_CACHE_TIME = {}
CACHE_DURATION_SECONDS = 300  # 5 minutes


class TeamSelectWidget(forms.Select):
    """Custom select widget that includes game ID as data attribute"""
    def create_option(self, name, value, label, selected, index, **kwargs):
        option = super().create_option(name, value, label, selected, index, **kwargs)
        if value:
            try:
                # Extract the actual ID if it's a ModelChoiceIteratorValue
                team_id = value.value if hasattr(value, 'value') else value
                team = Team.objects.get(pk=team_id)
                option['attrs']['data-game-id'] = team.game.id
            except (Team.DoesNotExist, ValueError, AttributeError, TypeError):
                pass
        return option


class MatchTeamSelectWidget(forms.Select):
    """Custom select widget for match teams that includes game ID"""
    def create_option(self, name, value, label, selected, index, **kwargs):
        option = super().create_option(name, value, label, selected, index, **kwargs)
        if value:
            try:
                # Extract the actual ID if it's a ModelChoiceIteratorValue
                team_id = value.value if hasattr(value, 'value') else value
                # Cache team lookups to avoid N+1 queries
                cache_key = f'team_{team_id}'
                current_time = time.time()
                
                if cache_key not in _TEAM_OPTIONS_CACHE or (current_time - _TEAM_OPTIONS_CACHE_TIME.get(cache_key, 0)) > CACHE_DURATION_SECONDS:
                    team = Team.objects.select_related('game').get(pk=team_id)
                    _TEAM_OPTIONS_CACHE[cache_key] = team.game.id
                    _TEAM_OPTIONS_CACHE_TIME[cache_key] = current_time
                
                option['attrs']['data-game-id'] = _TEAM_OPTIONS_CACHE[cache_key]
            except (Team.DoesNotExist, ValueError, AttributeError, TypeError):
                pass
        return option


class TeamMemberSelectWidget(forms.Select):
    """Custom select widget that includes team ID as data attribute"""
    def create_option(self, name, value, label, selected, index, **kwargs):
        option = super().create_option(name, value, label, selected, index, **kwargs)
        if value:
            try:
                # Extract the actual ID if it's a ModelChoiceIteratorValue
                member_id = value.value if hasattr(value, 'value') else value
                member = TeamMember.objects.get(pk=member_id)
                option['attrs']['data-team-id'] = member.team.id
            except (TeamMember.DoesNotExist, ValueError, AttributeError, TypeError):
                pass
        return option


class CustomAuthenticationForm(AuthenticationForm):
    """Custom authentication form with email-based login"""
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-cyan-500 bg-gray-900 text-cyan-300 rounded focus:outline-none focus:ring-2 focus:ring-cyan-400',
            'placeholder': 'Email Address',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-cyan-500 bg-gray-900 text-cyan-300 rounded focus:outline-none focus:ring-2 focus:ring-cyan-400',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })
    )


class GameForm(forms.ModelForm):
    """Form for creating/editing games"""
    class Meta:
        model = Game
        fields = ['name', 'completed', 'display_order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'completed': forms.CheckboxInput(attrs={'class': 'w-5 h-5 bg-gray-800 border border-cyan-500 text-cyan-500 rounded focus:ring-cyan-400'}),
            'display_order': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
        }


class TeamForm(forms.ModelForm):
    """Form for creating/editing teams"""
    captain_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded',
            'placeholder': 'Captain name *'
        })
    )
    
    class Meta:
        model = Team
        fields = ['game', 'name']
        widgets = {
            'game': forms.Select(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded', 'placeholder': 'Team name'}),
        }


class TeamMemberForm(forms.ModelForm):
    """Form for creating/editing team members"""
    class Meta:
        model = TeamMember
        fields = ['team', 'name', 'role']
        widgets = {
            'team': forms.Select(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'role': forms.Select(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
        }


class MatchForm(forms.ModelForm):
    """Form for creating/editing matches"""
    class Meta:
        model = Match
        fields = ['game', 'team_a', 'team_b', 'scheduled_at', 'location', 'status', 'match_stage', 'score_a', 'score_b', 'winner_team', 'notes']
        widgets = {
            'game': forms.Select(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'team_a': MatchTeamSelectWidget(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'team_b': MatchTeamSelectWidget(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'scheduled_at': forms.DateTimeInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'match_stage': forms.Select(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'score_a': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'score_b': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'winner_team': MatchTeamSelectWidget(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make team_a and team_b required
        self.fields['team_a'].required = True
        self.fields['team_b'].required = True
        # Make winner_team optional
        self.fields['winner_team'].required = False


class ScoreUpdateForm(forms.ModelForm):
    """Form for score managers to update match scores"""
    class Meta:
        model = Match
        fields = ['score_a', 'score_b', 'status', 'winner_team']
        widgets = {
            'score_a': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'score_b': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'winner_team': forms.Select(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
        }


class ScoreManagerScheduleMatchForm(forms.ModelForm):
    """Form for score managers to schedule new matches"""
    class Meta:
        model = Match
        fields = ['team_a', 'team_b', 'scheduled_at', 'location', 'match_stage', 'winner_team', 'notes']
        widgets = {
            'team_a': MatchTeamSelectWidget(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'team_b': MatchTeamSelectWidget(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'scheduled_at': forms.DateTimeInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded', 'placeholder': 'e.g., Court A, Field B'}),
            'match_stage': forms.Select(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'winner_team': forms.Select(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded', 'rows': 2, 'placeholder': 'Optional notes about the match'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make team_a and team_b required
        self.fields['team_a'].required = True
        self.fields['team_b'].required = True
        # Make winner_team optional
        self.fields['winner_team'].required = False


class GameAwardForm(forms.ModelForm):
    """Form for creating/editing awards"""
    class Meta:
        model = GameAward
        fields = ['game', 'award_label', 'team', 'member']
        widgets = {
            'game': forms.Select(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'award_label': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'team': TeamSelectWidget(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'member': TeamMemberSelectWidget(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
        }


class ScoreManagerProfileForm(forms.ModelForm):
    """Form for assigning score managers to games"""
    class Meta:
        model = ScoreManagerProfile
        fields = ['assigned_games']
        widgets = {
            'assigned_games': forms.CheckboxSelectMultiple(attrs={'class': 'space-y-2'}),
        }


class ScoreManagerUserForm(forms.ModelForm):
    """Form for creating new score manager users"""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
        help_text='Password for the score manager user'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
        label='Confirm Password',
        help_text='Re-enter the password'
    )
    
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded', 'required': True}),
            'username': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 bg-gray-800 border border-cyan-500 text-cyan-300 rounded'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError('Email is required.')
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            # Create ScoreManagerProfile for this user
            ScoreManagerProfile.objects.get_or_create(user=user)
        return user


# Inline formset for creating teams with members
TeamMemberInlineFormSet = inlineformset_factory(
    Team,
    TeamMember,
    form=TeamMemberForm,
    extra=0,  # Start with 0 forms, add dynamically via JavaScript
    can_delete=True
)
