"""Django Channels consumers for WebSocket real-time updates"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from core.models import Game, Match, GameAward
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class DashboardConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for public dashboard.
    Handles real-time updates for:
    - Match score changes
    - Leaderboard updates
    - Game awards/results
    
    Groups:
    - "dashboard" - all connected dashboard clients
    - "game_<id>" - clients watching a specific game
    """
    
    async def connect(self):
        """Join dashboard group on WebSocket connect"""
        self.room_group_name = 'dashboard'
        
        # Join group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Dashboard client connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        """Leave dashboard group on disconnect"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Dashboard client disconnected: {self.channel_name}")
    
    # ========================================================================
    # Message handlers - receive from WebSocket
    # ========================================================================
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'subscribe_game':
                await self.subscribe_to_game(data.get('game_id'))
            elif action == 'unsubscribe_game':
                await self.unsubscribe_from_game(data.get('game_id'))
            elif action == 'ping':
                # Heartbeat
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error in DashboardConsumer.receive: {e}")
    
    async def subscribe_to_game(self, game_id):
        """Subscribe to game-specific updates"""
        if game_id:
            self.game_group_name = f'game_{game_id}'
            await self.channel_layer.group_add(
                self.game_group_name,
                self.channel_name
            )
            logger.info(f"Client subscribed to game {game_id}")
    
    async def unsubscribe_from_game(self, game_id):
        """Unsubscribe from game-specific updates"""
        if game_id:
            self.game_group_name = f'game_{game_id}'
            await self.channel_layer.group_discard(
                self.game_group_name,
                self.channel_name
            )
            logger.info(f"Client unsubscribed from game {game_id}")
    
    # ========================================================================
    # Event handlers - receive from group_send
    # ========================================================================
    
    async def match_update(self, event):
        """Handle match update event"""
        # Send match data to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'match_update',
            'match_id': event.get('match_id'),
            'game_id': event.get('game_id'),
            'team_a_id': event.get('team_a_id'),
            'team_b_id': event.get('team_b_id'),
            'score_a': event.get('score_a'),
            'score_b': event.get('score_b'),
            'status': event.get('status'),
            'winner_id': event.get('winner_id'),
        }))
    

    async def award_update(self, event):
        """Handle award/result update event"""
        await self.send(text_data=json.dumps({
            'type': 'award_update',
            'award_id': event.get('award_id'),
            'game_id': event.get('game_id'),
            'label': event.get('label'),
        }))
    
    async def leaderboard_update(self, event):
        """Handle leaderboard update event"""
        await self.send(text_data=json.dumps({
            'type': 'leaderboard_update',
            'game_id': event.get('game_id'),
        }))


class GameConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for game-specific updates.
    Used by slideshow to get real-time leaderboard and match data.
    """
    
    async def connect(self):
        """Extract game_id from URL and join appropriate group"""
        self.game_id = self.scope['url_route']['kwargs'].get('game_id')
        self.room_group_name = f'game_{self.game_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial game data
        game_data = await self.get_game_data()
        await self.send(text_data=json.dumps({
            'type': 'game_data',
            'data': game_data
        }))
        
        logger.info(f"Game {self.game_id} consumer connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        """Leave game group on disconnect"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"Game {self.game_id} consumer disconnected")
    
    @database_sync_to_async
    def get_game_data(self):
        """Fetch game data for initial load"""
        try:
            game = Game.objects.get(id=self.game_id)
            
            # Get leaderboard
            from core.models import LeaderboardCache
            leaderboard = LeaderboardCache.objects.filter(
                game=game
            ).order_by('-points').values('team__name', 'points', 'wins', 'losses')
            
            # Get upcoming matches
            matches = game.matches.filter(
                status__in=['upcoming', 'ongoing']
            ).order_by('scheduled_at')[:3].values(
                'id', 'team_a__name', 'team_b__name', 'score_a', 'score_b',
                'scheduled_at', 'status'
            )
            
            return {
                'game_id': game.id,
                'game_name': game.name,
                'leaderboard': list(leaderboard),
                'matches': list(matches),
            }
        except Game.DoesNotExist:
            return {}
    
    async def match_update(self, event):
        """Handle match update"""
        await self.send(text_data=json.dumps({
            'type': 'match_update',
            'match_id': event.get('match_id'),
            'score_a': event.get('score_a'),
            'score_b': event.get('score_b'),
            'status': event.get('status'),
        }))
    
    async def leaderboard_update(self, event):
        """Handle leaderboard update"""
        leaderboard = await self.get_game_data()
        await self.send(text_data=json.dumps({
            'type': 'leaderboard_update',
            'leaderboard': leaderboard.get('leaderboard', []),
        }))
