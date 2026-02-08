# Sports Gala API Documentation

## Overview

The Sports Gala application provides a RESTful API for real-time access to game data, leaderboards, and match information. All API responses are in JSON format.

## Base URL

```
http://localhost:8000/api/  (development)
https://yourdomain.com/api/  (production)
```

## Authentication

- Public endpoints: No authentication required
- Admin endpoints: Session-based authentication (Django admin)
- Manager endpoints: User must have `ScoreManagerProfile`

## Endpoints

### Public Endpoints (No Auth)

#### Get Game Details

```
GET /api/games/{game_id}/
```

Returns game information including all teams with their current leaderboard position.

**Response:**
```json
{
  "id": 1,
  "name": "Cricket",
  "status": "ongoing",
  "teams": [
    {
      "id": 1,
      "name": "Team Alpha",
      "captain": "Player A1",
      "members_count": 3,
      "points": 6,
      "wins": 2,
      "losses": 0
    }
  ]
}
```

---

#### Get Upcoming Matches

```
GET /api/games/{game_id}/matches/
```

Returns upcoming and ongoing matches for a specific game (limited to top 3).

**Response:**
```json
{
  "matches": [
    {
      "id": 1,
      "team_a": "Team Alpha",
      "team_b": "Team Beta",
      "scheduled_at": "2026-01-27T14:00:00Z",
      "location": "Ground A",
      "status": "upcoming",
      "score_a": 0,
      "score_b": 0
    }
  ]
}
```

---

#### Get Leaderboard

```
GET /api/games/{game_id}/leaderboard/
```

Returns the leaderboard for a specific game ordered by points.

**Response:**
```json
{
  "leaderboard": [
    {
      "team": "Team Alpha",
      "points": 6,
      "wins": 2,
      "losses": 0,
      "draws": 0
    },
    {
      "team": "Team Beta",
      "points": 3,
      "wins": 1,
      "losses": 1,
      "draws": 0
    }
  ]
}
```

---

### Authenticated Endpoints

#### Update Match Score (Score Manager)

```
POST /score-manager/match/{match_id}/update/
Content-Type: application/x-www-form-urlencoded

score_a=120&score_b=105&status=completed&winner_team=1
```

**Parameters:**
- `score_a` (integer): Score of team A
- `score_b` (integer): Score of team B
- `status` (string): upcoming, ongoing, or completed
- `winner_team` (integer, optional): ID of winning team

**Response:** Redirects to game detail page on success

---

## WebSocket Endpoints

### Public Dashboard Stream

```
WS /ws/dashboard/
```

Real-time updates for the public dashboard.

**Client Actions:**
```json
{
  "action": "subscribe_game",
  "game_id": 1
}
```

**Server Messages:**
```json
{
  "type": "match_update",
  "match_id": 1,
  "game_id": 1,
  "team_a_id": 1,
  "team_b_id": 2,
  "score_a": 50,
  "score_b": 45,
  "status": "ongoing",
  "winner_id": null
}
```

```json
{
  "type": "message_update",
  "message_id": 1,
  "title": "Match Update",
  "message": "Team Alpha leads by 5 points"
}
```

```json
{
  "type": "award_update",
  "award_id": 1,
  "game_id": 1,
  "label": "1st Position"
}
```

---

### Game-Specific Stream

```
WS /ws/game/{game_id}/
```

Real-time leaderboard and match updates for a specific game.

**Server Messages:**
```json
{
  "type": "leaderboard_update",
  "leaderboard": [
    {
      "team__name": "Team Alpha",
      "points": 6,
      "wins": 2,
      "losses": 0
    }
  ]
}
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 302 | Redirect - Form submission redirect |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 500 | Server Error - Internal error |

---

## Error Responses

```json
{
  "error": "Description of error",
  "details": {
    "field": ["Error message for field"]
  }
}
```

---

## Rate Limiting

- No rate limiting on public endpoints
- WebSocket connections limited to 100 concurrent per game
- API calls in development: unlimited
- API calls in production: 1000/hour per IP (recommended)

---

## CORS

CORS is enabled for:
- `http://localhost:3000`
- `http://127.0.0.1:3000`

Customize in `config/settings/base.py`:
```python
CORS_ALLOWED_ORIGINS = [
    'https://yourdomain.com',
]
```

---

## Best Practices

1. **WebSocket Updates**: Use WebSocket for real-time updates instead of polling
2. **Caching**: Leaderboard data is cached - cache headers: max-age=60
3. **Error Handling**: Always check WebSocket close codes for graceful reconnect
4. **Authentication**: Include session cookies for authenticated endpoints
5. **HTTPS**: Use wss:// (WebSocket Secure) in production

---

## Example: JavaScript Client

```javascript
// Connect to WebSocket
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const socket = new WebSocket(`${protocol}//${window.location.host}/ws/dashboard/`);

// Subscribe to game
socket.onopen = function(e) {
    socket.send(JSON.stringify({
        action: 'subscribe_game',
        game_id: 1
    }));
};

// Handle messages
socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    switch(data.type) {
        case 'match_update':
            console.log('Match updated:', data);
            // Update UI
            break;
        case 'message_update':
            console.log('Message:', data);
            break;
        case 'award_update':
            console.log('Award:', data);
            break;
    }
};

// Handle disconnection
socket.onclose = function(e) {
    console.log('Disconnected, reconnecting...');
    setTimeout(() => location.reload(), 3000);
};

// Fetch game data
fetch('/api/games/1/')
    .then(r => r.json())
    .then(data => console.log('Game:', data));
```

---

## Support

For API issues:
- Check WebSocket connection status
- Verify CSRF token for form submissions
- Review browser console for errors
- Check server logs: `docker logs web`

---

**Last Updated**: January 2026
