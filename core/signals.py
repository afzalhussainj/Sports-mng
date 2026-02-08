"""Signals for core app - handle WebSocket notifications on data changes"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
import logging

from core.models import Match, GameAward, Team

logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


@receiver(post_save, sender=Match)
def match_updated(sender, instance, created, **kwargs):
    """
    Send WebSocket notification when a match is created or updated.
    This triggers real-time updates on the public dashboard.
    """
    try:
        # Notify dashboard about leaderboard and match changes
        async_to_sync(channel_layer.group_send)(
            f"game_{instance.game.id}",
            {
                "type": "match_update",
                "match_id": instance.id,
                "game_id": instance.game.id,
                "team_a_id": instance.team_a.id,
                "team_b_id": instance.team_b.id,
                "score_a": instance.score_a,
                "score_b": instance.score_b,
                "status": instance.status,
                "winner_id": instance.winner_team.id if instance.winner_team else None,
            }
        )
        
        # Also notify the global dashboard group
        async_to_sync(channel_layer.group_send)(
            "dashboard",
            {
                "type": "match_update",
                "match_id": instance.id,
                "game_id": instance.game.id,
            }
        )
    except Exception as e:
        logger.error(f"Error sending match update: {e}")


@receiver(post_save, sender=GameAward)
def award_updated(sender, instance, created, **kwargs):
    """Send WebSocket notification when an award is created or updated."""
    try:
        async_to_sync(channel_layer.group_send)(
            f"game_{instance.game.id}",
            {
                "type": "award_update",
                "award_id": instance.id,
                "game_id": instance.game.id,
                "label": instance.award_label,
            }
        )
        
        async_to_sync(channel_layer.group_send)(
            "dashboard",
            {
                "type": "award_update",
                "award_id": instance.id,
                "game_id": instance.game.id,
            }
        )
    except Exception as e:
        logger.error(f"Error sending award update: {e}")
