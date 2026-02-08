"""
Tournament Bracket Utilities

Organizes matches into tournament brackets using match_stage field.

The bracket hierarchy is determined by match_stage:
- quarter_final: Quarter Finals (typically 4 matches)
- semi_final: Semi Finals (typically 2 matches) 
- final: Final (1 match)

No automatic round calculation - match_stage is the single source of truth.
"""

from datetime import timedelta
from django.db.models import Q
from .models import Match, Team


# Tournament round calculation removed - use match_stage field instead


def get_bracket_hierarchy(game):
    """
    Get structured bracket data for frontend rendering.
    Organizes matches by match_stage (quarter_final, semi_final, final).
    
    Returns:
        dict with rounds organized by stage, ready for frontend
    """
    matches = game.matches.all().order_by('scheduled_at')
    
    # Only include matches that have match_stage set
    bracket_matches = matches.filter(match_stage__isnull=False)
    
    if not bracket_matches.exists():
        return {
            'rounds': [],
            'total_rounds': 0,
        }
    
    # Group matches by stage in correct order
    stage_order = ['quarter_final', 'semi_final', 'final']
    bracket = {}
    
    for stage in stage_order:
        stage_matches = bracket_matches.filter(match_stage=stage)
        if stage_matches.exists():
            bracket[stage] = {
                'stage': stage,
                'matches': [
                    {
                        'id': match.id,
                        'team_a': {
                            'id': match.team_a.id if match.team_a else None,
                            'name': match.team_a.name if match.team_a else 'TBD',
                        },
                        'team_b': {
                            'id': match.team_b.id if match.team_b else None,
                            'name': match.team_b.name if match.team_b else 'TBD',
                        },
                        'score_a': match.score_a,
                        'score_b': match.score_b,
                        'winner': {
                            'id': match.winner_team.id if match.winner_team else None,
                            'name': match.winner_team.name if match.winner_team else None,
                        },
                        'status': match.status,
                        'match_stage': match.match_stage,
                        'scheduled_at': match.scheduled_at.isoformat(),
                        'location': match.location,
                        'bracket_position': match.bracket_position,
                        'next_match_id': match.next_match_id,
                    }
                    for match in stage_matches
                ]
            }
    
    # Convert to list format that frontend expects
    rounds = [bracket[stage] for stage in stage_order if stage in bracket]
    
    return {
        'rounds': rounds,
        'total_rounds': len(rounds),
    }


def update_bracket_on_match_save(match):
    """
    Called when a match is saved.
    Bracket structure is now determined solely by match_stage field.
    """
    # match_stage field determines the bracket stage
    # No automatic calculation needed
    pass
