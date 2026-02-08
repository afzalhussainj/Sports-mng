"""
Add this to core/views.py after the leaderboard_api function (around line 280):
"""

# Insert this function in views.py:

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from .models import Game

@require_http_methods(["GET"])
def bracket_api(request, game_id):
    """
    Get tournament bracket structure for a game.
    
    Returns rounds organized by auto-calculated tournament levels based on match scheduling.
    
    Response format:
    {
        "rounds": [
            {
                "number": 1,
                "matches": [
                    {
                        "id": 1,
                        "team_a": {"id": 1, "name": "Team A"},
                        "team_b": {"id": 2, "name": "Team B"},
                        "score_a": 0,
                        "score_b": 0,
                        "winner": {"id": 1, "name": "Team A"},
                        "status": "completed",
                        "scheduled_at": "2026-01-31T...",
                        "location": "Field A",
                        "bracket_position": 0,
                        "next_match_id": 2
                    }
                ]
            }
        ],
        "total_rounds": 3
    }
    """
    from .bracket_utils import get_bracket_hierarchy
    
    game = get_object_or_404(Game, id=game_id)
    bracket_data = get_bracket_hierarchy(game)
    
    return JsonResponse(bracket_data)
