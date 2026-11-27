from django.utils.translation import gettext_lazy as _
from django.utils.translation import get_language
from django.conf import settings
from django.db import transaction
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods
from .forms import (AccommodationForm, AttendanceForm, ContactForm, FoodForm,
                    GuestFormSet, ParticipantForm, TravelForm)
from .models import Registration

STEPS = [
    ('aanwezigheid', _('Aanwezigheid'), AttendanceForm, _('Laat weten of je erbij bent en wie er met je meekomt.')),
    ('eten-en-drinken', _('Eten en drinken'), FoodForm, _('Vertel ons waar we rekening mee mogen houden.')),
    ('overnachting', _('Overnachting'), AccommodationForm, _('Een fijne plek om te blijven na een mooi feest.')),
    ('reis-en-vervoer', _('Reis en vervoer'), TravelForm, _('Samen op weg naar Frankrijk.')),
    ('contact-en-communicatie', _('Contact en communicatie'), ContactForm, _('Zo kunnen we je op de hoogte houden.')),
]


def active_steps(draft):
    if draft.get('aanwezigheid', {}).get('attending') == 'no':
        return [STEPS[0], STEPS[-1]]
    return STEPS


def validate_attendance(data):
    form = AttendanceForm(data)
    primary = ParticipantForm(data, prefix='primary')
    guests = GuestFormSet(data, prefix='guests')
    valid = form.is_valid() & primary.is_valid()
    if form.cleaned_data.get('attending'):
        valid = guests.is_valid() & valid
        if valid:
            count = 1 + sum(bool(guest.cleaned_data) for guest in guests)
            if count != form.cleaned_data['party_size']:
                form.add_error('party_size', _('Het aantal personen moet overeenkomen met jezelf en de ingevulde gasten hieronder.'))
                valid = False
    return form, primary, guests, valid


@require_GET
def register(request):
    return redirect('registration_step', step='aanwezigheid')


@never_cache
@require_http_methods(['GET', 'POST'])
def registration_step(request, step):
    draft = request.session.get('rsvp_draft', {})
    steps = active_steps(draft)
    slugs = [item[0] for item in steps]
    if step not in slugs:
        return redirect('register')
    index = slugs.index(step)
    for previous in slugs[:index]:
        if previous not in draft:
            return redirect('registration_step', step=previous)

    _, title, form_class, description = steps[index]
    data = request.POST if request.method == 'POST' else None
    show_guests = step == 'aanwezigheid' and data is not None and 'show_guests' in data
    if show_guests:
        data = data.copy()
        try:
            count = max(0, min(10, int(data.get('party_size', '1')) - 1))
        except ValueError:
            count = 0
        data['guests-TOTAL_FORMS'] = str(count)
        data['guests-INITIAL_FORMS'] = '0'
    initial = draft.get(step, {})
    if step == 'contact-en-communicatie' and not initial:
        initial = {'contact_email': draft.get('aanwezigheid', {}).get('primary-email', ''), 'language': get_language()}
    primary = guests = None
    if step == 'aanwezigheid':
        if data is not None:
            form, primary, guests, valid = validate_attendance(data)
            if show_guests:
                valid = False
        else:
            form = form_class(initial=initial or {'party_size': 1})
            primary = ParticipantForm(initial={key.removeprefix('primary-'): value for key, value in initial.items() if key.startswith('primary-')}, prefix='primary')
            guests = GuestFormSet(initial if initial else None, prefix='guests')
            valid = False
    else:
        form = form_class(data, initial=initial)
        valid = form.is_valid() if data is not None else False

    if request.method == 'POST' and valid:
        draft[step] = {key: value for key, value in request.POST.items() if key != 'csrfmiddlewaretoken'}
        if step == 'aanwezigheid' and not form.cleaned_data['attending']:
            draft = {key: value for key, value in draft.items() if key in ['aanwezigheid', 'contact-en-communicatie']}
        request.session['rsvp_draft'] = draft
        steps = active_steps(draft)
        slugs = [item[0] for item in steps]
        index = slugs.index(step)
        if index < len(steps) - 1:
            return redirect('registration_step', step=slugs[index + 1])

        # Revalidate the entire draft before writing any records.
        attendance, primary, guests, valid_attendance = validate_attendance(draft['aanwezigheid'])
        if not valid_attendance:
            return redirect('register')
        validated = [attendance]
        for slug, _, klass, _ in steps[1:]:
            saved_form = klass(draft.get(slug, {}))
            if not saved_form.is_valid():
                return redirect('registration_step', step=slug)
            validated.append(saved_form)
        with transaction.atomic():
            registration = Registration()
            for saved_form in validated:
                for field in saved_form.Meta.fields:
                    setattr(registration, field, saved_form.cleaned_data[field])
            registration.save()
            person = primary.save(commit=False)
            person.registration = registration
            person.is_primary = True
            person.save()
            if registration.attending:
                for guest_form in guests:
                    if guest_form.cleaned_data:
                        guest = guest_form.save(commit=False)
                        guest.registration = registration
                        guest.save()
        request.session['confirmation'] = {
            'count': registration.party_size, 'attending': registration.attending,
            'reference': str(registration.reference)[:8],
        }
        request.session.pop('rsvp_draft', None)
        return redirect('confirmation')

    navigation = [{'slug': item[0], 'title': item[1], 'number': number + 1,
                   'accessible': all(previous[0] in draft for previous in steps[:number]),
                   'current': number == index} for number, item in enumerate(steps)]
    return render(request, 'registrations/step.html', {
        'form': form, 'primary': primary, 'guests': guests, 'step': step,
        'title': title, 'description': description, 'navigation': navigation,
        'previous': slugs[index - 1] if index else None,
        'is_last': index == len(steps) - 1, 'step_number': index + 1,
        'step_count': len(steps), 'wedding': settings.WEDDING,
    })


@never_cache
@require_GET
def confirmation(request):
    confirmation = request.session.get('confirmation')
    if not confirmation:
        return redirect('register')
    return render(request, 'registrations/confirmation.html', {'confirmation': confirmation, 'wedding': settings.WEDDING})
