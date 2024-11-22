from django.core.management.base import BaseCommand
from draw.models import FamilyName

class Command(BaseCommand):
    help = "Családnevek linkjeinek generálása"

    def handle(self, *args, **kwargs):
        for family_name in FamilyName.objects.all():
            if not family_name.unique_link:
                family_name.save()  # Ez frissíti a családnevet és generálja a linket
                print(f"Családnév: {family_name.name}, Link: {family_name.unique_link}")

        self.stdout.write(self.style.SUCCESS("Családnevek linkjei generálva és elmentve."))
