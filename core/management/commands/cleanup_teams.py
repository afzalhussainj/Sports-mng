from django.core.management.base import BaseCommand
from core.models import Team, Game


class Command(BaseCommand):
    help = 'Remove all teams and their members except ones associated with cricket and test tournament'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--no-confirm',
            action='store_true',
            help='Skip confirmation prompt and delete directly',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Get games that should be kept (cricket and test tournament)
        keep_games = Game.objects.filter(name__icontains='cricket') | Game.objects.filter(name__icontains='test')
        keep_game_ids = set(keep_games.values_list('id', flat=True))
        
        self.stdout.write(self.style.SUCCESS(f'Games to keep: {list(keep_games.values_list("name", flat=True))}'))
        self.stdout.write('')
        
        # Find teams NOT associated with cricket or test tournament
        teams_to_delete = Team.objects.exclude(game_id__in=keep_game_ids)
        
        if not teams_to_delete.exists():
            self.stdout.write(self.style.SUCCESS('No teams to delete. All existing teams are from cricket or test tournament.'))
            return
        
        # Show what will be deleted
        self.stdout.write(self.style.WARNING(f'Teams to delete: {teams_to_delete.count()}'))
        self.stdout.write('')
        
        for team in teams_to_delete:
            members_count = team.members.count()
            matches_count = team.matches_as_team_a.count() + team.matches_as_team_b.count()
            
            self.stdout.write(
                f'  • {team.name} (Game: {team.game.name if team.game else "No Game"})'
                f' - {members_count} member{"s" if members_count != 1 else ""}, '
                f'{matches_count} match{"es" if matches_count != 1 else ""}'
            )
        
        self.stdout.write('')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN: No teams were deleted. Run without --dry-run to actually delete.'))
            return
        
        no_confirm = options.get('no_confirm', False)
        
        # Confirm deletion
        if not no_confirm:
            confirmation = input(f'Are you sure you want to delete {teams_to_delete.count()} teams and all their members and matches? (yes/no): ')
            
            if confirmation.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Deletion cancelled.'))
                return
        
        # Delete the teams (cascade will handle members and matches)
        deleted_count, deleted_details = teams_to_delete.delete()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {teams_to_delete.count()} teams'))
        self.stdout.write(self.style.SUCCESS(f'Total objects deleted: {deleted_count}'))
        self.stdout.write(self.style.SUCCESS('All associated members and matches were also deleted (cascade delete).'))
