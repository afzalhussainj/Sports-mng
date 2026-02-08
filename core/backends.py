"""Custom authentication backends"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class EmailAuthBackend(ModelBackend):
    """
    Authenticate using email address instead of username.
    Users can login with either email or username (for backwards compatibility).
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find user by email first, then username
            user = User.objects.get(Q(email=username) | Q(username=username))
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # If multiple users found by username, try exact email match
            user = User.objects.filter(email=username).first()
            if not user:
                return None
        
        # Check password
        if user.check_password(password):
            return user
        return None
