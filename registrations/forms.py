from django.utils.translation import gettext_lazy as _
from django import forms
from django.forms import formset_factory
from .models import Participant, Registration


class ParticipantForm(forms.ModelForm):
    def clean_phone(self):
        phone = self.cleaned_data['phone']
        digits = ''.join(character for character in phone if character.isdigit())
        if not 7 <= len(digits) <= 15:
            raise forms.ValidationError(_('Vul een telefoonnummer met 7 tot 15 cijfers in.'))
        return phone

    class Meta:
        model = Participant
        fields = ['name', 'email', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'name', 'placeholder': _('Voor- en achternaam')}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': _('naam@voorbeeld.nl')}),
            'phone': forms.TextInput(attrs={'type': 'tel', 'autocomplete': 'tel', 'placeholder': '+31 6 12345678'}),
        }


GuestFormSet = formset_factory(ParticipantForm, extra=0, max_num=10, absolute_max=10, validate_max=True)


def yes_no(label):
    return forms.TypedChoiceField(label=label, choices=[('yes', _('Ja')), ('no', _('Nee'))], coerce=lambda value: value == 'yes', widget=forms.RadioSelect)


class AttendanceForm(forms.ModelForm):
    attending = yes_no(_('Kom je naar het trouwfeest?'))
    party_size = forms.IntegerField(label=_('Met hoeveel personen kom je?'), min_value=0, max_value=11, help_text=_('Tel jezelf mee. Vul 0 in als je niet komt.'))

    class Meta:
        model = Registration
        fields = ['attending', 'party_size']

    def clean(self):
        data = super().clean()
        if data.get('attending') is False:
            data['party_size'] = 0
            self.errors.pop('party_size', None)
        elif data.get('attending') and data.get('party_size', 0) < 1:
            self.add_error('party_size', _('Vul minimaal 1 persoon in als je komt.'))
        return data


class FoodForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['dietary_requirements', 'allergies']
        labels = {'dietary_requirements': _('Zijn er dieetwensen?'), 'allergies': _('Zijn er allergieën waar we rekening mee moeten houden?')}
        widgets = {'dietary_requirements': forms.Textarea(attrs={'rows': 3, 'placeholder': _('Optioneel. Vermeld ook voor welke persoon dit geldt.')}), 'allergies': forms.Textarea(attrs={'rows': 3, 'placeholder': _('Optioneel. Vermeld ook voor welke persoon dit geldt.')})}


class AccommodationForm(forms.ModelForm):
    accommodation_help = yes_no(_('Heb je hulp nodig bij het vinden van accommodatie?'))
    accommodation_transport = yes_no(_('Heb je vervoer nodig tussen accommodatie en feestlocatie?'))

    class Meta:
        model = Registration
        fields = ['accommodation_help', 'accommodation_people', 'accommodation_nights', 'accommodation_preference', 'accommodation_transport']
        labels = {
            'accommodation_people': _('Voor hoeveel personen zoek je accommodatie?'),
            'accommodation_nights': _('Welke nachten wil je blijven?'),
            'accommodation_preference': _('Heb je voorkeur voor hotel, B&B, camping of vakantiehuis?'),
        }
        widgets = {'accommodation_people': forms.NumberInput(attrs={'min': 1, 'max': 11}), 'accommodation_nights': forms.TextInput(attrs={'placeholder': _('Bijvoorbeeld: vrijdag 9 juli en zaterdag 10 juli')})}

    def clean(self):
        data = super().clean()
        if data.get('accommodation_help'):
            for field in ['accommodation_people', 'accommodation_nights', 'accommodation_preference']:
                if not data.get(field) and field not in self.errors:
                    self.add_error(field, _('Vul dit in zodat we je kunnen helpen met accommodatie.'))
            people = data.get('accommodation_people')
            if people is not None and not 1 <= people <= 11:
                self.add_error('accommodation_people', _('Vul een aantal tussen 1 en 11 in.'))
        else:
            for field, empty in [('accommodation_people', None), ('accommodation_nights', ''), ('accommodation_preference', '')]:
                self.errors.pop(field, None)
                data[field] = empty
        return data


class TravelForm(forms.ModelForm):
    carpool_available = yes_no(_('Heb je een vrije plaats in je auto voor carpoolen?'))
    wants_ride = yes_no(_('Zou je graag met iemand willen meerijden?'))
    station_pickup = yes_no(_('Heb je vervoer nodig vanaf een station?'))

    class Meta:
        model = Registration
        fields = ['travel_method', 'travel_other', 'carpool_available', 'wants_ride', 'station_pickup']
        labels = {'travel_method': _('Hoe kom je naar Frankrijk?'), 'travel_other': _('Hoe reis je anders naar Frankrijk?')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['travel_method'].required = True

    def clean(self):
        data = super().clean()
        if data.get('travel_method') == 'other' and not data.get('travel_other'):
            self.add_error('travel_other', _('Vertel ons hoe je naar Frankrijk reist.'))
        if data.get('travel_method') != 'other':
            data['travel_other'] = ''
        if data.get('travel_method') != 'car':
            self.errors.pop('carpool_available', None)
            data['carpool_available'] = False
        return data


class ContactForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['contact_email', 'language', 'practical_updates', 'notes']
        labels = {
            'contact_email': _('Wat is je e-mailadres?'),
            'language': _('In welke taal wil je informatie ontvangen?'),
            'practical_updates': _('Mogen we je praktische updates sturen over het feest?'),
            'notes': _('Wil je nog iets met ons delen?'),
        }
        widgets = {'contact_email': forms.EmailInput(attrs={'autocomplete': 'email'}), 'notes': forms.Textarea(attrs={'rows': 3})}
        help_texts = {'practical_updates': _('Ja, jullie mogen mij praktische updates sturen. Niet aanvinken betekent geen toestemming.')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contact_email'].required = True
