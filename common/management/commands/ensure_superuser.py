"""
Management command to ensure a superuser exists.
Safe to run on every deploy — creates or resets the superuser.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Create or reset a superuser from env vars.'

    def handle(self, *args, **options):
        User = get_user_model()
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        missing = [
            name
            for name, value in {
                'DJANGO_SUPERUSER_EMAIL': email,
                'DJANGO_SUPERUSER_USERNAME': username,
                'DJANGO_SUPERUSER_PASSWORD': password,
            }.items()
            if not value
        ]
        if missing:
            raise CommandError(f'Missing required environment variables: {", ".join(missing)}')

        # Try to find existing user by username or email
        user = User.objects.filter(username=username).first() or User.objects.filter(email=email).first()

        if user:
            # Reset password and ensure superuser privileges
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.email = email
            user.username = username
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" updated and password reset.'))
        else:
            # Create new superuser
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully.'))
