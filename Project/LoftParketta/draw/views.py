from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, JsonResponse
from draw.models import FamilyName, DrawnFamilyName
from uuid import uuid4, UUID  # Fontos: uuid4 importálása
import random

def generate_guest_id(request):
    """
    Létrehozza a vendég felhasználó egyedi azonosítóját a session-ben,
    ha még nincs ilyen.
    """
    guest_id = request.session.get('guest_id', None)
    if not guest_id:
        guest_id = str(uuid4())  # Véletlenszerű egyedi azonosító generálása
        request.session['guest_id'] = guest_id
    return guest_id

def wheel_page(request, link):
    try:
        valid_link = UUID(link) if not isinstance(link, UUID) else link
    except ValueError:
        raise Http404("Invalid link format")

    family_name = get_object_or_404(FamilyName, unique_link=valid_link)

    # Ellenőrizzük, hogy a vendég már sorsolt-e
    guest_id = generate_guest_id(request)
    drawn_family_name = DrawnFamilyName.objects.filter(guest_id=guest_id, family_name=family_name).first()

    if request.method == 'POST' and not drawn_family_name:
        # Csak a még nem kiosztott családneveket vegyük figyelembe
        available_family_names = FamilyName.objects.filter(is_assigned=False).exclude(unique_link=valid_link)

        if not available_family_names.exists():
            # Ha nincs elérhető családnév, jelezzük a felhasználónak
            return render(request, 'wheel.html', {
                'family_name': family_name,
                'error_message': 'Nincs több elérhető családnév a sorsoláshoz.'
            })

        # Véletlenszerűen válasszunk egy elérhető családnevet
        drawn_name = random.choice(available_family_names)

        # Beállítjuk az is_assigned értékét True-ra
        drawn_name.is_assigned = True
        drawn_name.save()

        # Elmentjük a sorsolt értéket a vendég azonosítóhoz
        DrawnFamilyName.objects.create(
            guest_id=guest_id,
            family_name=family_name,
            drawn_name=drawn_name.name
        )

        return redirect('draw:wheel_page', link=family_name.unique_link)

    return render(request, 'wheel.html', {
        'family_name': family_name,
        'drawn_family_name': drawn_family_name.drawn_name if drawn_family_name else None
    })

def spin_wheel(request, link):
    try:
        # Validáljuk és konvertáljuk a linket UUID típusra
        valid_link = UUID(link) if not isinstance(link, UUID) else link
        # Megkeressük a FamilyName objektumot a link alapján
        family_name = FamilyName.objects.get(unique_link=valid_link)

        # Ne sorsoljunk ugyanarra a családnévre
        all_family_names = list(FamilyName.objects.exclude(id=family_name.id))

        if all_family_names:
            drawn_family_name = random.choice(all_family_names)  # Véletlenszerű kiválasztás
            # Átirányítjuk a felhasználót egy új oldalra, ahol megjelenítjük az eredményt
            return redirect('draw:result_page', link=valid_link, drawn_family_name=drawn_family_name.name)
        else:
            return JsonResponse({'error': 'Nincs több családnév a sorsoláshoz.'})

    except FamilyName.DoesNotExist:
        return JsonResponse({'error': 'Nincs ilyen családnév.'})
    except ValueError:
        return JsonResponse({'error': 'Érvénytelen link.'})

def result_page(request, link, drawn_family_name):
    # Ezen az oldalon jelenítjük meg a sorsolás eredményét
    try:
        valid_link = UUID(link) if not isinstance(link, UUID) else link
        family_name = get_object_or_404(FamilyName, unique_link=valid_link)
    except ValueError:
        raise Http404("Invalid link format")

    return render(request, 'result.html', {'family_name': family_name, 'drawn_family_name': drawn_family_name})
