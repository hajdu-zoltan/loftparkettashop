from django.core.management.base import BaseCommand
from draw.models import FamilyName

class Command(BaseCommand):
    help = "Betölti az előre definiált családneveket az adatbázisba."

    def handle(self, *args, **kwargs):
        family_names = ["Pap", "Zádori", "Hajdú", "Kúsz", "Zsikó", "Tokodi"]

        for name in family_names:
            FamilyName.objects.get_or_create(name=name)

        self.stdout.write(self.style.SUCCESS("Családnevek betöltve."))
