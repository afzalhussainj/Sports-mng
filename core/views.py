"""Views for core app"""
import json
import os
import time
from io import BytesIO
from PIL import Image
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.core.serializers.json import DjangoJSONEncoder

from core.models import (
    Game, Team, TeamMember, Match, GameAward,
    ScoreManagerProfile, LeaderboardCache, AvailableTeam
)
from core.forms import (
    CustomAuthenticationForm, GameForm, TeamForm, TeamMemberForm,
    MatchForm, GameAwardForm,
    ScoreManagerProfileForm, ScoreManagerUserForm, ScoreUpdateForm, 
    ScoreManagerScheduleMatchForm, TeamMemberInlineFormSet
)


def is_admin(user):
    """Check if user is admin (superuser)"""
    return user.is_superuser or user.is_staff


def is_score_manager(user):
    """Check if user is a score manager"""
    return hasattr(user, 'score_manager_profile')


def can_upload_photos(user):
    """Check if user can upload slideshow photos - Admin only"""
    return is_admin(user)


def convert_to_16_9(image_file):
    """
    Convert uploaded image to 16:9 aspect ratio.
    Crops the image from center to maintain 16:9 ratio.
    Returns BytesIO object with processed image.
    """
    # Open the image
    img = Image.open(image_file)
    
    # Convert to RGB if necessary (handles PNG with transparency, etc.)
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (0, 0, 0))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Get current dimensions
    width, height = img.size
    target_ratio = 16 / 9
    current_ratio = width / height
    
    # Calculate new dimensions to achieve 16:9
    if current_ratio > target_ratio:
        # Image is wider than 16:9, crop width
        new_width = int(height * target_ratio)
        new_height = height
        left = (width - new_width) // 2
        top = 0
        right = left + new_width
        bottom = height
    else:
        # Image is taller than 16:9, crop height
        new_width = width
        new_height = int(width / target_ratio)
        left = 0
        top = (height - new_height) // 2
        right = width
        bottom = top + new_height
    
    # Crop to 16:9
    img_cropped = img.crop((left, top, right, bottom))
    
    # Optionally resize to a reasonable size (max 1920x1080 for 16:9)
    max_width = 1920
    if img_cropped.width > max_width:
        new_width = max_width
        new_height = int(max_width / target_ratio)
        img_cropped = img_cropped.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Save to BytesIO
    output = BytesIO()
    img_cropped.save(output, format='JPEG', quality=90, optimize=True)
    output.seek(0)
    
    return output


def get_supabase_client():
    """Create Supabase client if configured"""
    try:
        from decouple import config as decouple_config
    except ImportError:
        def decouple_config(key, default=None):
            return os.getenv(key, default)

    supabase_url = decouple_config('SUPABASE_URL', default=None)
    supabase_key = decouple_config('SUPABASE_SERVICE_ROLE_KEY', default=None)

    if not supabase_url or not supabase_key:
        return None

    try:
        from supabase import create_client
        return create_client(supabase_url, supabase_key)
    except Exception:
        return None


def fetch_slideshow_images(limit=50):
    """Fetch slideshow images from Supabase"""
    supabase = get_supabase_client()
    if not supabase:
        return []

    try:
        res = supabase.table("slideshow_images").select("public_url,created_at").order("created_at", desc=True).limit(limit).execute()
        return [row.get("public_url") for row in (res.data or []) if row.get("public_url")]
    except Exception:
        return []


def login_view(request):
    """Login page with role-aware redirect"""
    if request.user.is_authenticated:
        if is_admin(request.user):
            return redirect('admin_panel')
        elif is_score_manager(request.user):
            return redirect('score_manager_panel')
        return redirect('public_dashboard')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Role-aware redirect
            if is_admin(user):
                return redirect('admin_panel')
            elif is_score_manager(user):
                return redirect('score_manager_panel')
            return redirect('public_dashboard')
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    """Logout"""
    logout(request)
    return redirect('public_dashboard')


def public_dashboard(request):
    """
    Public dashboard - no authentication required.
    Shows:
    - Live leaderboards (rotating slideshow by game)
    - Final results (awards)
    """
    games = Game.objects.all().order_by('display_order')
    
    slideshow_images = fetch_slideshow_images(limit=50)
    context = {
        'games': games,
        'slideshow_images_json': json.dumps(slideshow_images, cls=DjangoJSONEncoder),
        'is_admin': is_admin(request.user),
        'is_score_manager': is_score_manager(request.user),
    }
    return render(request, 'core/public_dashboard.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def upload_photo(request):
    """Upload slideshow photos to Supabase (Admin only, converts to 16:9)"""
    supabase = get_supabase_client()
    if not supabase:
        messages.error(request, 'Supabase is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.')
        return render(request, 'core/upload_photo.html')

    if request.method == 'POST':
        photo = request.FILES.get('photo')
        if not photo:
            messages.error(request, 'Please choose a photo to upload.')
            return redirect('upload_photo')

        try:
            # Convert image to 16:9 aspect ratio
            processed_image = convert_to_16_9(photo)
            
            filename = f"{int(time.time())}_{photo.name.rsplit('.', 1)[0]}.jpg"
            path = f"event/{filename}"

            # Upload to Supabase
            supabase.storage.from_("gala-slideshow").upload(
                path, 
                processed_image.read(), 
                {"content-type": "image/jpeg"}
            )
            
            public_url = supabase.storage.from_("gala-slideshow").get_public_url(path)
            supabase.table("slideshow_images").insert({
                "path": path,
                "public_url": public_url
            }).execute()
            
            messages.success(request, 'Photo uploaded successfully! (Converted to 16:9 aspect ratio)')
        except Exception as exc:
            messages.error(request, f'Upload failed: {exc}')

        return redirect('upload_photo')

    return render(request, 'core/upload_photo.html')


def slideshow_json(request):
    """Return slideshow images as JSON for polling"""
    images = fetch_slideshow_images(limit=100)
    return JsonResponse({"images": images})


@login_required(login_url='login')
def admin_panel(request):
    """
    Admin panel - full CRUD for everything.
    Only accessible to superusers.
    """
    if not is_admin(request.user):
        return redirect('public_dashboard')
    
    games = Game.objects.all()
    context = {
        'games': games,
        'title': 'Admin Panel - Sports Gala Management',
    }
    return render(request, 'core/admin_panel.html', context)


@login_required(login_url='login')
@user_passes_test(is_score_manager)
def score_manager_panel(request):
    """
    Score manager panel.
    Only can update scores for their assigned games.
    """
    profile = request.user.score_manager_profile
    assigned_games = profile.assigned_games.all()
    
    context = {
        'assigned_games': assigned_games,
        'title': 'Score Manager Panel',
    }
    return render(request, 'core/score_manager_panel.html', context)


# ============================================================================
# API Endpoints for Real-time Data
# ============================================================================

def game_detail_api(request, game_id):
    """Get game details as JSON for frontend"""
    game = get_object_or_404(Game, id=game_id)
    teams = game.teams.all()
    
    teams_data = []
    for team in teams:
        captain = team.get_captain()
        members = team.get_members()
        leaderboard = LeaderboardCache.objects.filter(game=game, team=team).first()
        
        teams_data.append({
            'id': team.id,
            'name': team.name,
            'captain': captain.name if captain else None,
            'members_count': members.count(),
            'points': leaderboard.points if leaderboard else 0,
            'wins': leaderboard.wins if leaderboard else 0,
            'losses': leaderboard.losses if leaderboard else 0,
        })
    
    data = {
        'id': game.id,
        'name': game.name,
        'completed': game.completed,
        'teams': teams_data,
    }
    return JsonResponse(data)


def matches_api(request, game_id):
    """Get upcoming/ongoing matches for a game"""
    game = get_object_or_404(Game, id=game_id)
    
    # Get upcoming and ongoing matches, limit to top 3
    matches = game.matches.filter(
        status__in=['upcoming', 'ongoing']
    ).order_by('scheduled_at')[:3]
    
    matches_data = []
    for match in matches:
        matches_data.append({
            'id': match.id,
            'team_a': match.team_a.name if match.team_a else 'TBD',
            'team_b': match.team_b.name if match.team_b else 'TBD',
            'scheduled_at': match.scheduled_at.isoformat(),
            'location': match.location,
            'status': match.status,
            'score_a': match.score_a,
            'score_b': match.score_b,
        })
    
    return JsonResponse({'matches': matches_data})


def bracket_api(request, game_id):
    """Get tournament bracket structure for a game"""
    from .bracket_utils import get_bracket_hierarchy

    game = get_object_or_404(Game, id=game_id)
    bracket_data = get_bracket_hierarchy(game)
    return JsonResponse(bracket_data)


def leaderboard_api(request, game_id):
    """Get leaderboard for a game"""
    game = get_object_or_404(Game, id=game_id)
    
    leaderboard = LeaderboardCache.objects.filter(game=game).order_by('-points', '-wins')
    
    leaderboard_data = []
    for entry in leaderboard:
        leaderboard_data.append({
            'team': entry.team.name,
            'points': entry.points,
            'wins': entry.wins,
            'losses': entry.losses,
            'draws': entry.draws,
        })
    
    return JsonResponse({'leaderboard': leaderboard_data})


# ============================================================================
# Admin Management Views (CRUD Operations)
# ============================================================================

@login_required(login_url='login')
@user_passes_test(is_admin)
def manage_games(request):
    """List and manage games"""
    if request.method == 'POST':
        form = GameForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_games')
    else:
        form = GameForm()
    
    games = Game.objects.all()
    context = {'games': games, 'form': form, 'title': 'Manage Games'}
    return render(request, 'core/admin/manage_games.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def manage_teams_members(request):
    """Manage teams and members in one panel"""
    # Initialize forms
    team_form_with_members = TeamForm(prefix='team')
    formset = TeamMemberInlineFormSet(instance=None, prefix='members')
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'team_with_members':
            # Create team with inline members
            team_form_with_members = TeamForm(request.POST, prefix='team')
            if team_form_with_members.is_valid():
                # Extract captain name before saving
                captain_name = team_form_with_members.cleaned_data.get('captain_name', '').strip()
                
                # Save team first
                team = team_form_with_members.save()
                
                # Create captain member if captain_name is provided
                if captain_name:
                    TeamMember.objects.create(
                        team=team,
                        name=captain_name,
                        role='captain'
                    )
                
                # Now handle the formset with the created team instance
                formset = TeamMemberInlineFormSet(request.POST, instance=team, prefix='members')
                if formset.is_valid():
                    # Force all formset members to be 'member' role
                    members = formset.save(commit=False)
                    for member in members:
                        member.role = 'member'
                        member.save()
                    formset.save_m2m()
                    
                    messages.success(request, f"Team '{team.name}' created with members!")
                    return redirect('manage_teams_members')
                else:
                    # Formset has errors, show them
                    team_form_with_members = TeamForm(prefix='team')
                    formset = TeamMemberInlineFormSet(instance=None, prefix='members')
            else:
                # Team form has errors, reinitialize formset
                formset = TeamMemberInlineFormSet(instance=None, prefix='members')
    
    teams = Team.objects.select_related('game').order_by('game__name', 'name')
    
    context = {
        'teams': teams,
        'team_form': team_form_with_members,
        'formset': formset,
        'title': 'Manage Teams & Members'
    }
    return render(request, 'core/admin/manage_teams_members.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def manage_teams(request):
    """List and manage teams"""
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            captain_name = form.cleaned_data.get('captain_name', '').strip()
            team = form.save()
            
            # Create captain member if captain_name is provided
            if captain_name:
                TeamMember.objects.create(
                    team=team,
                    name=captain_name,
                    role='captain'
                )
                messages.success(request, f"Team '{team.name}' created with captain {captain_name}!")
            else:
                messages.success(request, f"Team '{team.name}' created!")
            return redirect('manage_teams')
    else:
        form = TeamForm()
    
    teams = Team.objects.select_related('game').order_by('game__name', 'name')
    context = {'teams': teams, 'form': form, 'title': 'Manage Teams'}
    return render(request, 'core/admin/manage_teams.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def manage_members(request):
    """List and manage team members"""
    if request.method == 'POST':
        form = TeamMemberForm(request.POST)
        if form.is_valid():
            member = form.save()
            messages.success(request, f"Member '{member.name}' added to {member.team.name}!")
            return redirect('manage_members')
    else:
        form = TeamMemberForm()
    
    members = TeamMember.objects.select_related('team').all()
    context = {'members': members, 'form': form, 'title': 'Manage Members'}
    return render(request, 'core/admin/manage_members.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def manage_matches(request):
    """List and manage matches"""
    if request.method == 'POST':
        if request.POST.get('set_winner'):
            match_id = request.POST.get('match_id')
            winner_id = request.POST.get('winner_team')
            match = get_object_or_404(Match, id=match_id)

            if not match.team_a or not match.team_b:
                messages.error(request, 'Both Team A and Team B must be selected before setting a winner.')
                return redirect('manage_matches')

            if not winner_id:
                messages.error(request, 'Please select a winner team.')
                return redirect('manage_matches')

            if str(match.team_a_id) != str(winner_id) and str(match.team_b_id) != str(winner_id):
                messages.error(request, 'Selected winner must be Team A or Team B for this match.')
                return redirect('manage_matches')

            match.winner_team_id = winner_id
            match.save(update_fields=['winner_team'])
            messages.success(request, 'Winner updated successfully!')
            return redirect('manage_matches')

        form = MatchForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_matches')
    else:
        form = MatchForm()
    
    matches = Match.objects.select_related('game', 'team_a', 'team_b').order_by('game__name')
    context = {'matches': matches, 'form': form, 'title': 'Manage Matches'}
    return render(request, 'core/admin/manage_matches.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def manage_awards(request):
    """List and manage awards"""
    if request.method == 'POST':
        form = GameAwardForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_awards')
    else:
        form = GameAwardForm()
    
    awards = GameAward.objects.select_related('game', 'team', 'member').all()
    context = {'awards': awards, 'form': form, 'title': 'Manage Awards'}
    return render(request, 'core/admin/manage_awards.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def manage_score_managers(request):
    """Create and assign score managers to games"""
    # Handle user creation
    if request.method == 'POST' and 'create_manager' in request.POST:
        form = ScoreManagerUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Score manager '{user.username}' created successfully!")
            return redirect('manage_score_managers')
    # Handle game assignment
    elif request.method == 'POST' and 'assign_games' in request.POST:
        manager_id = request.POST.get('manager_id')
        manager = get_object_or_404(User, pk=manager_id, score_manager_profile__isnull=False)
        profile = manager.score_manager_profile
        assign_form = ScoreManagerProfileForm(request.POST, instance=profile)
        if assign_form.is_valid():
            assign_form.save()
            messages.success(request, f"Games assigned to '{manager.username}' successfully!")
            return redirect('manage_score_managers')
    else:
        form = ScoreManagerUserForm()
    
    score_managers = User.objects.filter(score_manager_profile__isnull=False)
    # Get all games for the assignment checkboxes
    all_games = Game.objects.all()
    
    context = {
        'score_managers': score_managers,
        'form': form,
        'all_games': all_games,
        'title': 'Manage Score Managers'
    }
    return render(request, 'core/admin/manage_score_managers.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def assign_score_manager_games(request, manager_id):
    """Assign games to a score manager"""
    manager = get_object_or_404(User, pk=manager_id, score_manager_profile__isnull=False)
    profile = manager.score_manager_profile
    
    if request.method == 'POST':
        form = ScoreManagerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('manage_score_managers')
    else:
        form = ScoreManagerProfileForm(instance=profile)
    
    context = {
        'manager': manager,
        'form': form,
        'title': f'Assign Games to {manager.username}'
    }
    return render(request, 'core/admin/assign_score_manager_games.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def delete_score_manager(request, manager_id):
    """Delete a score manager user"""
    manager = get_object_or_404(User, pk=manager_id, score_manager_profile__isnull=False)
    
    if request.method == 'POST':
        username = manager.username
        manager.delete()
        messages.success(request, f"Score manager '{username}' deleted successfully!")
        return redirect('manage_score_managers')
    
    context = {
        'manager': manager,
        'title': f'Delete {manager.username}'
    }
    return render(request, 'core/admin/delete_score_manager.html', context)


@login_required(login_url='login')
@user_passes_test(is_admin)
def change_score_manager_password(request, manager_id):
    """Change password for a score manager"""
    manager = get_object_or_404(User, pk=manager_id, score_manager_profile__isnull=False)
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        if not new_password or not confirm_password:
            messages.error(request, "Both password fields are required!")
        elif new_password != confirm_password:
            messages.error(request, "Passwords do not match!")
        elif len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters long!")
        else:
            manager.set_password(new_password)
            manager.save()
            messages.success(request, f"Password for '{manager.username}' changed successfully!")
            return redirect('manage_score_managers')
    
    context = {
        'manager': manager,
        'title': f'Change Password for {manager.username}'
    }
    return render(request, 'core/admin/change_score_manager_password.html', context)



# ============================================================================
# Score Manager Views
# ============================================================================

@login_required(login_url='login')
@user_passes_test(is_score_manager)
def score_manager_game_detail(request, game_id):
    """Score manager view for a specific game"""
    profile = request.user.score_manager_profile
    game = get_object_or_404(Game, id=game_id)
    
    # Check if manager is assigned to this game
    if not profile.can_manage_game(game):
        return redirect('score_manager_panel')
    
    matches = game.matches.all().order_by('scheduled_at')
    context = {
        'game': game,
        'matches': matches,
        'title': f'Score Manager - {game.name}',
    }
    return render(request, 'core/score_manager/game_detail.html', context)


@login_required(login_url='login')
@user_passes_test(is_score_manager)
def score_manager_update_match(request, match_id):
    """Update match scores and result"""
    match = get_object_or_404(Match, id=match_id)
    profile = request.user.score_manager_profile
    
    # Check if manager is assigned to this game
    if not profile.can_manage_game(match.game):
        return redirect('score_manager_panel')
    
    # Cannot update if game is completed
    if match.game.completed:
        return redirect('score_manager_game_detail', game_id=match.game.id)
    
    if request.method == 'POST':
        form = ScoreUpdateForm(request.POST, instance=match)
        if form.is_valid():
            match = form.save(commit=False)
            if match.status == 'completed':
                match.determine_winner()
                # Update leaderboard cache
                LeaderboardCache.update_for_match(match)
            match.save()
            return redirect('score_manager_game_detail', game_id=match.game.id)
    else:
        form = ScoreUpdateForm(instance=match)
    
    context = {
        'match': match,
        'form': form,
        'title': f'Update Score - {match}',
    }
    return render(request, 'core/score_manager/update_match.html', context)




@login_required(login_url='login')
@user_passes_test(is_score_manager)
def score_manager_schedule_match(request, game_id):
    """Allow score managers to schedule new matches for their assigned games"""
    game = get_object_or_404(Game, id=game_id)
    
    # Check permissions (admin or score manager)
    if is_admin(request.user):
        pass  # Admin can schedule for any game
    elif is_score_manager(request.user):
        profile = request.user.score_manager_profile
        if not profile.can_manage_game(game):
            return redirect('score_manager_panel')
    else:
        return redirect('login')
    
    # Cannot schedule if game is completed
    if game.completed:
        if is_admin(request.user):
            return redirect('manage_matches')
        return redirect('score_manager_game_detail', game_id=game_id)
    
    if request.method == 'POST':
        form = ScoreManagerScheduleMatchForm(request.POST)
        if form.is_valid():
            match = form.save(commit=False)
            match.game = game
            match.status = 'upcoming'  # New matches are always upcoming
            match.save()
            messages.success(request, f'Match scheduled successfully: {match.team_a.name} vs {match.team_b.name}')
            
            # Redirect based on user type
            if is_admin(request.user):
                return redirect('randomizer_panel')
            return redirect('score_manager_game_detail', game_id=game_id)
    else:
        # Create form with initial data from query parameters (from randomizer)
        initial_data = {}
        
        if request.GET.get('team_a'):
            initial_data['team_a'] = request.GET.get('team_a')
        if request.GET.get('team_b'):
            initial_data['team_b'] = request.GET.get('team_b')
        if request.GET.get('scheduled_at'):
            initial_data['scheduled_at'] = request.GET.get('scheduled_at')
        if request.GET.get('location'):
            initial_data['location'] = request.GET.get('location')
        if request.GET.get('match_stage'):
            initial_data['match_stage'] = request.GET.get('match_stage')
        if request.GET.get('notes'):
            initial_data['notes'] = request.GET.get('notes')
        
        form = ScoreManagerScheduleMatchForm(initial=initial_data)
        # Filter teams to only show teams in this game
        form.fields['team_a'].queryset = game.teams.all()
        form.fields['team_b'].queryset = game.teams.all()
    
    context = {
        'game': game,
        'form': form,
        'title': f'Schedule Match - {game.name}',
    }
    return render(request, 'core/score_manager/schedule_match.html', context)


@login_required(login_url='login')
def toggle_game_completed(request, game_id):
    """
    Toggle game completed status.
    - Score managers can only mark as completed (True)
    - Only admins can revert from completed (False)
    """
    game = get_object_or_404(Game, id=game_id)
    
    # Check permissions
    if is_admin(request.user):
        # Admin can toggle both ways
        game.completed = not game.completed
        game.save()
    elif is_score_manager(request.user):
        # Score manager can only mark as completed
        profile = request.user.score_manager_profile
        if profile.can_manage_game(game) and not game.completed:
            game.completed = True
            game.save()
    
    # Redirect based on user type
    if is_admin(request.user):
        return redirect('manage_games')
    else:
        return redirect('score_manager_game_detail', game_id=game_id)


# ============================================================================
# Randomizer Panel for Admin and Score Managers
# ============================================================================

@login_required(login_url='login')
def randomizer_panel(request):
    """
    Randomizer panel accessible to both admin and score managers.
    Allows managing available teams and randomly selecting two teams for a match.
    """
    # Get games based on user role
    if is_admin(request.user):
        games = Game.objects.all()
        title = 'Admin Randomizer Panel'
    elif is_score_manager(request.user):
        profile = request.user.score_manager_profile
        games = profile.assigned_games.all()
        title = 'Score Manager Randomizer Panel'
    else:
        return redirect('public_dashboard')
    
    context = {
        'games': games,
        'title': title,
        'is_admin': is_admin(request.user),
    }
    return render(request, 'core/randomizer_panel.html', context)


@login_required(login_url='login')
def randomizer_api_available_teams(request, game_id):
    """
    API endpoint to get/update available teams for a game.
    GET: Returns list of available teams
    POST: Add team to available list
    DELETE: Remove team from available list
    """
    game = get_object_or_404(Game, id=game_id)
    
    # Check permissions
    if is_admin(request.user):
        pass  # Admin can access all games
    elif is_score_manager(request.user):
        profile = request.user.score_manager_profile
        if not profile.can_manage_game(game):
            return JsonResponse({'error': 'Permission denied'}, status=403)
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method == 'GET':
        # Get available teams
        available = AvailableTeam.objects.filter(game=game).select_related('team')
        available_data = [{
            'id': avail.team.id,
            'name': avail.team.name,
            'available_id': avail.id,
        } for avail in available]
        
        # Get all teams for this game
        all_teams = game.teams.all()
        all_teams_data = [{
            'id': team.id,
            'name': team.name,
            'is_available': team.id in [a['id'] for a in available_data]
        } for team in all_teams]
        
        return JsonResponse({
            'available_teams': available_data,
            'all_teams': all_teams_data
        })
    
    elif request.method == 'POST':
        # Add team to available list
        data = json.loads(request.body)
        team_id = data.get('team_id')
        
        if not team_id:
            return JsonResponse({'error': 'team_id required'}, status=400)
        
        team = get_object_or_404(Team, id=team_id, game=game)
        
        # Create or get available team
        available, created = AvailableTeam.objects.get_or_create(
            game=game,
            team=team,
            defaults={'added_by': request.user}
        )
        
        return JsonResponse({
            'success': True,
            'created': created,
            'team': {'id': team.id, 'name': team.name}
        })
    
    elif request.method == 'DELETE':
        # Remove team from available list
        data = json.loads(request.body)
        team_id = data.get('team_id')
        
        if not team_id:
            return JsonResponse({'error': 'team_id required'}, status=400)
        
        try:
            available = AvailableTeam.objects.get(game=game, team_id=team_id)
            available.delete()
            return JsonResponse({'success': True})
        except AvailableTeam.DoesNotExist:
            return JsonResponse({'error': 'Team not in available list'}, status=404)


@login_required(login_url='login')
def randomizer_api_clear_available(request, game_id):
    """Clear all available teams for a game"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    game = get_object_or_404(Game, id=game_id)
    
    # Check permissions
    if is_admin(request.user):
        pass
    elif is_score_manager(request.user):
        profile = request.user.score_manager_profile
        if not profile.can_manage_game(game):
            return JsonResponse({'error': 'Permission denied'}, status=403)
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    # Clear all available teams
    count = AvailableTeam.objects.filter(game=game).delete()[0]
    
    return JsonResponse({'success': True, 'cleared': count})


@login_required(login_url='login')
def randomizer_api_pick_teams(request, game_id):
    """Randomly pick two teams from available teams and create a match"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    game = get_object_or_404(Game, id=game_id)
    
    # Check permissions
    if is_admin(request.user):
        pass
    elif is_score_manager(request.user):
        profile = request.user.score_manager_profile
        if not profile.can_manage_game(game):
            return JsonResponse({'error': 'Permission denied'}, status=403)
    else:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        # Get data from POST body
        data = json.loads(request.body) if request.body else {}

        team_a_id = data.get('team_a_id')
        team_b_id = data.get('team_b_id')

        if team_a_id and team_b_id:
            selected_qs = AvailableTeam.objects.filter(
                game=game,
                team_id__in=[team_a_id, team_b_id]
            ).select_related('team')
            selected_map = {str(item.team_id): item for item in selected_qs}
            if str(team_a_id) not in selected_map or str(team_b_id) not in selected_map:
                return JsonResponse({'error': 'Selected teams are not in available list'}, status=400)
            selected = [selected_map[str(team_a_id)], selected_map[str(team_b_id)]]
        else:
            # Get available teams
            available_teams = list(AvailableTeam.objects.filter(game=game).select_related('team'))
            
            if len(available_teams) < 2:
                return JsonResponse({'error': 'Need at least 2 available teams'}, status=400)
            
            # Randomly select 2 teams
            import random
            selected = random.sample(available_teams, 2)

        # Preview mode: only return selected teams
        if data.get('preview') or data.get('create_match') is False:
            return JsonResponse({
                'success': True,
                'team_a': {'id': selected[0].team.id, 'name': selected[0].team.name},
                'team_b': {'id': selected[1].team.id, 'name': selected[1].team.name},
                'game_id': game.id,
                'game_name': game.name
            })
        
        # Create the match
        scheduled_at_raw = data.get('scheduled_at') or None
        scheduled_at = parse_datetime(scheduled_at_raw) if scheduled_at_raw else None
        if scheduled_at and timezone.is_naive(scheduled_at):
            scheduled_at = timezone.make_aware(scheduled_at, timezone.get_current_timezone())

        location = data.get('location', '')
        match_stage = data.get('match_stage', '')
        notes = data.get('notes', '')
        
        match = Match.objects.create(
            game=game,
            team_a=selected[0].team,
            team_b=selected[1].team,
            scheduled_at=scheduled_at if scheduled_at else timezone.now(),
            location=location,
            match_stage=match_stage if match_stage else None,
            notes=notes,
            status='upcoming'
        )
        
        # Remove selected teams from available list
        AvailableTeam.objects.filter(id__in=[selected[0].id, selected[1].id]).delete()
        
        return JsonResponse({
            'success': True,
            'match_id': match.id,
            'team_a': {'id': selected[0].team.id, 'name': selected[0].team.name},
            'team_b': {'id': selected[1].team.id, 'name': selected[1].team.name},
            'game_id': game.id,
            'game_name': game.name,
            'scheduled_at': match.scheduled_at.isoformat(),
            'message': f'Match created successfully between {match.team_a.name} and {match.team_b.name}'
        })
    except Exception as e:
        return JsonResponse({'error': f'Failed to create match: {str(e)}'}, status=500)


# Edit and Delete Views

@login_required(login_url='login')
@user_passes_test(is_admin)
def edit_game(request, game_id):
    """Edit game details"""
    game = get_object_or_404(Game, id=game_id)
    
    if request.method == 'POST':
        form = GameForm(request.POST, instance=game)
        if form.is_valid():
            form.save()
            messages.success(request, f'Game "{game.name}" updated successfully!')
            return redirect('manage_games')
    else:
        form = GameForm(instance=game)
    
    return render(request, 'core/admin/edit_game.html', {
        'form': form,
        'game': game
    })


@login_required(login_url='login')
@user_passes_test(is_admin)
def delete_game(request, game_id):
    """Delete a game"""
    game = get_object_or_404(Game, id=game_id)
    
    if request.method == 'POST':
        game_name = game.name
        game.delete()
        messages.success(request, f'Game "{game_name}" deleted successfully!')
        return redirect('manage_games')
    
    return render(request, 'core/admin/delete_game.html', {
        'game': game
    })


@login_required(login_url='login')
@user_passes_test(is_admin)
def edit_team(request, team_id):
    """Edit team details"""
    team = get_object_or_404(Team, id=team_id)
    
    if request.method == 'POST':
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, f'Team "{team.name}" updated successfully!')
            return redirect('manage_teams_members')
    else:
        form = TeamForm(instance=team)
    
    return render(request, 'core/admin/edit_team.html', {
        'form': form,
        'team': team
    })


@login_required(login_url='login')
@user_passes_test(is_admin)
def delete_team(request, team_id):
    """Delete a team"""
    team = get_object_or_404(Team, id=team_id)
    
    if request.method == 'POST':
        team_name = team.name
        team.delete()
        messages.success(request, f'Team "{team_name}" deleted successfully!')
        return redirect('manage_teams_members')
    
    return render(request, 'core/admin/delete_team.html', {
        'team': team
    })


@login_required(login_url='login')
@user_passes_test(is_admin)
def edit_member(request, member_id):
    """Edit team member details"""
    member = get_object_or_404(TeamMember, id=member_id)
    
    if request.method == 'POST':
        form = TeamMemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f'Member "{member.name}" updated successfully!')
            return redirect('manage_teams_members')
    else:
        form = TeamMemberForm(instance=member)
    
    return render(request, 'core/admin/edit_member.html', {
        'form': form,
        'member': member
    })


@login_required(login_url='login')
@user_passes_test(is_admin)
def delete_member(request, member_id):
    """Delete a team member"""
    member = get_object_or_404(TeamMember, id=member_id)
    
    if request.method == 'POST':
        member_name = member.name
        member.delete()
        messages.success(request, f'Member "{member_name}" deleted successfully!')
        return redirect('manage_teams_members')
    
    return render(request, 'core/admin/delete_member.html', {
        'member': member
    })


@login_required(login_url='login')
@user_passes_test(is_admin)
def edit_match(request, match_id):
    """Edit match details"""
    match = get_object_or_404(Match, id=match_id)
    
    if request.method == 'POST':
        form = MatchForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            messages.success(request, f'Match updated successfully!')
            return redirect('manage_matches')
    else:
        form = MatchForm(instance=match)
    
    return render(request, 'core/admin/edit_match.html', {
        'form': form,
        'match': match
    })


@login_required(login_url='login')
@user_passes_test(is_admin)
def delete_match(request, match_id):
    """Delete a match"""
    match = get_object_or_404(Match, id=match_id)
    
    if request.method == 'POST':
        match.delete()
        messages.success(request, f'Match deleted successfully!')
        return redirect('manage_matches')
    
    return render(request, 'core/admin/delete_match.html', {
        'match': match
    })


@login_required(login_url='login')
@user_passes_test(is_admin)
def edit_award(request, award_id):
    """Edit award details"""
    award = get_object_or_404(GameAward, id=award_id)
    
    if request.method == 'POST':
        form = GameAwardForm(request.POST, instance=award)
        if form.is_valid():
            form.save()
            messages.success(request, f'Award "{award.award_label}" updated successfully!')
            return redirect('manage_awards')
    else:
        form = GameAwardForm(instance=award)
    
    return render(request, 'core/admin/edit_award.html', {
        'form': form,
        'award': award
    })


@login_required(login_url='login')
@user_passes_test(is_admin)
def delete_award(request, award_id):
    """Delete an award"""
    award = get_object_or_404(GameAward, id=award_id)
    
    if request.method == 'POST':
        award_label = award.award_label
        award.delete()
        messages.success(request, f'Award "{award_label}" deleted successfully!')
        return redirect('manage_awards')
    
    return render(request, 'core/admin/delete_award.html', {
        'award': award
    })
