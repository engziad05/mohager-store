"""
Management command to ensure a superuser exists.
Safe to run on every deploy — only creates if missing.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create a superuser from env vars if one does not already exist.'

    def handle(self, *args, **options):
        User = get_user_model()
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'zeiad0453@gmail.com')
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'Ziad')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'Mohager@2026')

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'Superuser with email {email} already exists — skipping.'))
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )
        self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully.'))
