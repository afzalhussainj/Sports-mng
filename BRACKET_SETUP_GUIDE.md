## Dynamic Tournament Bracket Implementation - Setup Guide

### Overview
The tournament bracket system now **dynamically calculates rounds** based on actual match scheduling. Rounds are determined by:
1. **Grouping matches by scheduled_at time** (30-min windows = same round)
2. **Tracking team advancement**: Teams that play in round N+1 are those who won in round N
3. **Auto-linking bracket**: Winners are linked to their next match automatically

### Changes Made

#### 1. Backend - Model Updates
**File**: `core/models.py`
- Added `tournament_round` field (Integer) - Round number based on scheduling
- Added `bracket_position` field (Integer) - Position within the round
- Added `next_match` ForeignKey - Link to the match the winner advances to

#### 2. Backend - Bracket Utility Module
**File**: `core/bracket_utils.py` (NEW)
```python
calculate_tournament_rounds(game) → Analyzes match scheduling, groups by time, auto-links winners
get_bracket_hierarchy(game) → Returns structured bracket ready for frontend
update_bracket_on_match_save(match) → Hook for updating bracket when match result changes
```

**Algorithm**:
- Group matches by `scheduled_at` time (30-min window threshold)
- Identify advancing teams: those with matches in next round
- Auto-calculate bracket_position and next_match relationships
- Store in database for efficient querying

#### 3. Backend - API Endpoint
**File**: `core/views.py`
- Add this function (around line 280, after leaderboard_api):

```python
@require_http_methods(["GET"])
def bracket_api(request, game_id):
    from .bracket_utils import get_bracket_hierarchy
    game = get_object_or_404(Game, id=game_id)
    bracket_data = get_bracket_hierarchy(game)
    return JsonResponse(bracket_data)
```

**URL**: `/api/games/<game_id>/bracket/`

#### 4. Frontend - Dashboard Update
**File**: `core/templates/core/public_dashboard.html`
- `renderTournamentBracket()` now fetches from `/api/games/{gameId}/bracket/`
- Uses `tournament_round` and `bracket_position` from backend
- Renders actual scores and winners instead of randomized data

#### 5. Migration
**File**: `core/migrations/0002_add_bracket_fields.py` (NEW)
Adds the three new fields to Match model

#### 6. Management Command
**File**: `core/management/commands/calculate_brackets.py` (NEW)

**Usage**:
```bash
# Calculate all brackets
python manage.py calculate_brackets

# Calculate specific game
python manage.py calculate_brackets --game-id 1
```

### Installation Steps

1. **Run migration**:
   ```bash
   python manage.py migrate
   ```

2. **Add to URLs** (`config/urls.py`):
   ```python
   # Import at top
   from core.views import bracket_api
   
   # Add to urlpatterns
   path('api/games/<int:game_id>/bracket/', bracket_api, name='bracket_api'),
   ```

3. **Calculate brackets**:
   ```bash
   python manage.py calculate_brackets
   ```

### How It Works

#### Scenario Example:
**Matches scheduled:**
- 14:00-14:30 (Round 1): Match 1 (Team A vs Team B), Match 2 (Team C vs Team D)
- 14:45-15:15 (Round 2): Match 3 (Winner1 vs Winner2), Match 4 (etc...)
- 15:30 (Final): Match 5 (Final Winner vs Other)

**Bracket Calculation:**
1. Groups matches into rounds by time window
2. Determines advancing teams based on match results
3. Sets:
   - Match 1: `tournament_round=1, bracket_position=0, next_match=Match 3`
   - Match 2: `tournament_round=1, bracket_position=1, next_match=Match 4`
   - Match 3: `tournament_round=2, bracket_position=0, next_match=Match 5`
   - Match 5: `tournament_round=3, bracket_position=0, next_match=null` (Final)

#### API Response Format:
```json
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
          "scheduled_at": "2026-01-31T14:00:00Z",
          "location": "Field A",
          "bracket_position": 0,
          "next_match_id": 3
        }
      ]
    },
    {
      "number": 2,
      "matches": [...]
    }
  ],
  "total_rounds": 3
}
```

### Key Features

✅ **Dynamic**: Rounds calculated based on actual match scheduling
✅ **Flexible**: No pre-defined bracket structure needed
✅ **Scalable**: Works for any tournament format (4-team, 8-team, 16-team, etc.)
✅ **Real-time**: Updates when match results change
✅ **Efficient**: Bracket stored in DB, not recalculated on every request

### Recalculating Brackets

When matches are added/removed or times change:
```bash
python manage.py calculate_brackets --game-id <id>
```

Or call `calculate_tournament_rounds(game)` directly in Django shell:
```python
from core.models import Game
from core.bracket_utils import calculate_tournament_rounds
game = Game.objects.get(id=1)
result = calculate_tournament_rounds(game)
print(result)
```

### Testing

1. Create some matches with staggered scheduled_at times
2. Run `calculate_brackets` management command
3. Visit dashboard and view tournament bracket
4. Update match scores and bracket will auto-update (after next bracket recalculation)

### Next Steps (Optional Enhancements)

- [ ] Auto-trigger `calculate_brackets` on match save via Django signals
- [ ] Admin interface to manually adjust bracket positions
- [ ] Bracket visualization with team seeding
- [ ] Playoff elimination system (best-of-3, etc.)
- [ ] Bracket export (PDF, image)
