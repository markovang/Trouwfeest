from django.utils.translation import gettext_lazy as _
import uuid
from django.core.validators import RegexValidator
from django.db import models

phone_validator = RegexValidator(r'^\+?[0-9 ()\-.]{7,25}$', _('Vul een geldig telefoonnummer in, bijvoorbeeld +31 6 12345678.'))


class Registration(models.Model):
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(_('aangemeld op'), auto_now_add=True)
    notes = models.TextField(_('opmerkingen'), blank=True, max_length=2000)
    attending = models.BooleanField(_('aanwezig'), default=True)
    party_size = models.PositiveSmallIntegerField(_('aantal aanwezige personen'), default=1)
    dietary_requirements = models.TextField(_('dieetwensen'), blank=True, max_length=2000)
    allergies = models.TextField(_('allergieën'), blank=True, max_length=2000)
    accommodation_help = models.BooleanField(_('hulp bij accommodatie'), default=False)
    accommodation_people = models.PositiveSmallIntegerField(_('personen voor accommodatie'), null=True, blank=True)
    accommodation_nights = models.CharField(_('nachten voor accommodatie'), blank=True, max_length=300)
    accommodation_preference = models.CharField(_('voorkeur accommodatie'), blank=True, max_length=20, choices=[('hotel', _('Hotel')), ('bnb', _('B&B')), ('camping', _('Camping')), ('holiday_home', _('Vakantiehuis')), ('none', _('Geen voorkeur'))])
    accommodation_transport = models.BooleanField(_('vervoer tussen accommodatie en feestlocatie'), default=False)
    travel_method = models.CharField(_('reis naar Frankrijk'), blank=True, max_length=20, choices=[('car', _('Auto')), ('train', _('Trein')), ('plane', _('Vliegtuig')), ('other', _('Anders'))])
    travel_other = models.CharField(_('ander vervoermiddel'), blank=True, max_length=200)
    carpool_available = models.BooleanField(_('vrije plaats voor carpoolen'), default=False)
    wants_ride = models.BooleanField(_('wil meerijden'), default=False)
    station_pickup = models.BooleanField(_('vervoer vanaf station nodig'), default=False)
    contact_email = models.EmailField(_('e-mailadres voor communicatie'), blank=True)
    language = models.CharField(_('informatietaal'), max_length=5, default='nl', choices=[('nl', _('Nederlands')), ('en', 'English'), ('fr', 'Français'), ('de', 'Deutsch')])
    practical_updates = models.BooleanField(_('toestemming voor praktische updates'), default=False)

    class Meta:
        verbose_name = _('aanmelding')
        verbose_name_plural = _('aanmeldingen')
        ordering = ['-created_at']

    def __str__(self):
        return f'Aanmelding {str(self.reference)[:8]}'


class Participant(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='participants', verbose_name=_('aanmelding'))
    name = models.CharField(_('volledige naam'), max_length=150)
    email = models.EmailField(_('e-mailadres'))
    phone = models.CharField(_('telefoonnummer'), max_length=25, validators=[phone_validator])
    is_primary = models.BooleanField(_('hoofdaanmelder'), default=False)

    class Meta:
        verbose_name = _('deelnemer')
        verbose_name_plural = _('deelnemers')
        ordering = ['pk']

    def __str__(self):
        return self.name
