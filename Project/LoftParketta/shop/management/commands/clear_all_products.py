from django.core.management.base import BaseCommand
from shop.models import Product, Category

class Command(BaseCommand):
    help = 'Törli az összes terméket a Product táblából'

    def handle(self, *args, **kwargs):
        Product.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Minden termék törölve lett.'))
