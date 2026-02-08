"""
Management command to calculate tournament brackets for all games
"""

from django.core.management.base import BaseCommand
from core.models import Game
from core.bracket_utils import calculate_tournament_rounds


class Command(BaseCommand):
    help = 'Calculate tournament bracket structure for games based on match scheduling'

    def add_arguments(self, parser):
        parser.add_argument(
            '--game-id',
            type=int,
            help='Calculate bracket for specific game ID',
        )

    def handle(self, *args, **options):
        if options['game_id']:
            try:
                game = Game.objects.get(id=options['game_id'])
                result = calculate_tournament_rounds(game)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Bracket calculated for {game.name}: {result["total_rounds"]} rounds'
                    )
                )
            except Game.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Game with ID {options["game_id"]} not found')
                )
        else:
            # Calculate for all games
            games = Game.objects.all()
            for game in games:
                result = calculate_tournament_rounds(game)
                if result.get('success'):
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ {game.name}: {result["total_rounds"]} rounds'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⊘ {game.name}: {result.get("error", "Unknown error")}')
                    )
