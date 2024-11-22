from django.db import models
import uuid
from users.models import CustomUser

class FamilyName(models.Model):
    name = models.CharField(max_length=100)
    unique_link = models.UUIDField(default=uuid.uuid4, unique=True)  # Egyszerű UUID mező
    is_assigned = models.BooleanField(default=False)
    def __str__(self):
        return self.name

class Participant(models.Model):
    name = models.CharField(max_length=100, unique=True)
    unique_link = models.UUIDField(default=uuid.uuid4, unique=True)
    has_drawn = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Result(models.Model):
    participant = models.OneToOneField(Participant, on_delete=models.CASCADE)
    drawn_family_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.participant.name} -> {self.drawn_family_name}"

class DrawnFamilyName(models.Model):
    family_name = models.ForeignKey('FamilyName', on_delete=models.CASCADE)
    drawn_name = models.CharField(max_length=255)
    guest_id = models.CharField(max_length=36, null=True, blank=True)  # Tárolja a vendég azonosítót
    drawn_at = models.DateTimeField(auto_now_add=True)