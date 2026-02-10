"""
URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import (
    public_dashboard,
    login_view,
    logout_view,
    admin_panel,
    score_manager_panel,
    game_detail_api,
    matches_api,
    bracket_api,
    leaderboard_api,
    manage_games,
    manage_teams_members,
    manage_matches,
    manage_awards,
    manage_score_managers,
    assign_score_manager_games,
    delete_score_manager,
    change_score_manager_password,
    score_manager_game_detail,
    score_manager_update_match,
    score_manager_schedule_match,
    toggle_game_completed,
    randomizer_panel,
    randomizer_api_available_teams,
    randomizer_api_clear_available,
    randomizer_api_pick_teams,
    upload_photo,
    manage_memories,
    slideshow_json,
    edit_game,
    delete_game,
    edit_team,
    delete_team,
    edit_member,
    delete_member,
    edit_match,
    delete_match,
    edit_award,
    delete_award,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    
    # Public pages
    path('', public_dashboard, name='public_dashboard'),
    path('upload/', upload_photo, name='upload_photo'),
    
    # Auth
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Manager pages
    path('manager/', admin_panel, name='admin_panel'),
    path('manager/games/', manage_games, name='manage_games'),
    path('manager/games/<int:game_id>/edit/', edit_game, name='edit_game'),
    path('manager/games/<int:game_id>/delete/', delete_game, name='delete_game'),
    path('manager/teams-members/', manage_teams_members, name='manage_teams_members'),
    path('manager/teams/<int:team_id>/edit/', edit_team, name='edit_team'),
    path('manager/teams/<int:team_id>/delete/', delete_team, name='delete_team'),
    path('manager/members/<int:member_id>/edit/', edit_member, name='edit_member'),
    path('manager/members/<int:member_id>/delete/', delete_member, name='delete_member'),
    path('manager/matches/', manage_matches, name='manage_matches'),
    path('manager/matches/<int:match_id>/edit/', edit_match, name='edit_match'),
    path('manager/matches/<int:match_id>/delete/', delete_match, name='delete_match'),
    path('manager/awards/', manage_awards, name='manage_awards'),
    path('manager/awards/<int:award_id>/edit/', edit_award, name='edit_award'),
    path('manager/awards/<int:award_id>/delete/', delete_award, name='delete_award'),
    path('manager/score-managers/', manage_score_managers, name='manage_score_managers'),
    path('manager/score-managers/<int:manager_id>/assign/', assign_score_manager_games, name='assign_score_manager_games'),
    path('manager/score-managers/<int:manager_id>/delete/', delete_score_manager, name='delete_score_manager'),
    path('manager/score-managers/<int:manager_id>/change-password/', change_score_manager_password, name='change_score_manager_password'),
    path('manager/memories/', manage_memories, name='manage_memories'),
    
    # Score Manager pages
    path('score-manager/', score_manager_panel, name='score_manager_panel'),
    path('score-manager/game/<int:game_id>/', score_manager_game_detail, name='score_manager_game_detail'),
    path('score-manager/match/<int:match_id>/update/', score_manager_update_match, name='score_manager_update_match'),
    path('score-manager/game/<int:game_id>/schedule-match/', score_manager_schedule_match, name='score_manager_schedule_match'),
    
    # Game completion toggle
    path('game/<int:game_id>/toggle-completed/', toggle_game_completed, name='toggle_game_completed'),
    
    # Randomizer panel (for both admin and score managers)
    path('randomizer/', randomizer_panel, name='randomizer_panel'),
    path('api/randomizer/<int:game_id>/available-teams/', randomizer_api_available_teams, name='randomizer_api_available_teams'),
    path('api/randomizer/<int:game_id>/clear-available/', randomizer_api_clear_available, name='randomizer_api_clear_available'),
    path('api/randomizer/<int:game_id>/pick-teams/', randomizer_api_pick_teams, name='randomizer_api_pick_teams'),
    
    # API endpoints for real-time updates
    path('api/games/<int:game_id>/', game_detail_api, name='game_detail_api'),
    path('api/games/<int:game_id>/matches/', matches_api, name='matches_api'),
    path('api/games/<int:game_id>/bracket/', bracket_api, name='bracket_api'),
    path('api/games/<int:game_id>/leaderboard/', leaderboard_api, name='leaderboard_api'),
    path('slideshow-json/', slideshow_json, name='slideshow_json'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
