"""
Management command to load provinces and cities from JSON.

Usage:
    python manage.py load_provinces_cities
"""

from django.core.management.base import BaseCommand
from shipping.models import load_provinces_and_cities_from_json


class Command(BaseCommand):
    help = "Load provinces and cities from iran_provinces_cities.json"

    def handle(self, *args, **options):
        self.stdout.write("Loading provinces and cities from JSON...")
        load_provinces_and_cities_from_json()
        self.stdout.write(self.style.SUCCESS("Done!"))
