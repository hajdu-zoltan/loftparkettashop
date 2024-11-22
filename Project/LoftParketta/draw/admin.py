from django.contrib import admin
from .models import FamilyName, Participant, Result

# FamilyName admin beállítása
@admin.register(FamilyName)
class FamilyNameAdmin(admin.ModelAdmin):
    list_display = ('name', 'unique_link', 'is_assigned')  # Mezők, amik a listában megjelennek
    search_fields = ('name',)  # Lehetővé teszi a keresést a családnév alapján
    list_filter = ('is_assigned',)  # Szűrés a 'is_assigned' mező alapján

# Participant admin beállítása
@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'unique_link', 'has_drawn')  # Mezők, amik a listában megjelennek
    search_fields = ('name',)  # Lehetővé teszi a keresést a név alapján
    list_filter = ('has_drawn',)  # Szűrés a 'has_drawn' mező alapján

# Result admin beállítása
@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('participant', 'drawn_family_name')  # Mezők, amik a listában megjelennek
    search_fields = ('participant__name', 'drawn_family_name')  # Keresés a résztvevő neve és a kisorsolt családnév alapján
