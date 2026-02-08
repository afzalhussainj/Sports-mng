"""Core app configuration"""
import os
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.contrib.auth import get_user_model


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Sports Gala Core'

    def _create_default_admin(self, **kwargs):
        """Create a default admin (staff) user if missing."""
        User = get_user_model()

        email = os.environ.get('DEFAULT_ADMIN_EMAIL', 'admin@gmail.com')
        password = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'talha123456')

        if not email or not password:
            return

        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                'email': email,
                'is_staff': True,
                'is_superuser': False,
            }
        )

        if not created:
            updates = []
            if user.email != email:
                user.email = email
                updates.append('email')
            if not user.is_staff:
                user.is_staff = True
                updates.append('is_staff')
            if user.is_superuser:
                user.is_superuser = False
                updates.append('is_superuser')
            if updates:
                user.save(update_fields=updates)

        # Ensure password matches expected default
        user.set_password(password)
        user.save(update_fields=['password'])

    def ready(self):
        """Import signals when app is ready"""
        import core.signals  # noqa

        post_migrate.connect(self._create_default_admin, sender=self)
