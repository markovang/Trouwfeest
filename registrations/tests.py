from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from .forms import AccommodationForm, TravelForm
from .models import Participant, Registration


class RegistrationTests(TestCase):
    def url(self, step):
        return reverse('registration_step', kwargs={'step': step})

    def attendance(self, guests=0, attending='yes'):
        data = {
            'attending': attending, 'party_size': guests + 1,
            'primary-name': 'Sam de Vries', 'primary-email': 'sam@example.com',
            'primary-phone': '+31 6 12345678',
            'guests-TOTAL_FORMS': str(guests), 'guests-INITIAL_FORMS': '0',
        }
        for index in range(guests):
            data.update({f'guests-{index}-name': f'Gast {index + 1}',
                         f'guests-{index}-email': f'gast{index}@example.com',
                         f'guests-{index}-phone': '0612345678'})
        return data

    def accommodation(self):
        return {'accommodation_help': 'yes', 'accommodation_people': '2',
                'accommodation_nights': 'Vrijdag 11 juni en zaterdag 12 juni',
                'accommodation_preference': 'bnb', 'accommodation_transport': 'yes'}

    def travel(self):
        return {'travel_method': 'car', 'carpool_available': 'yes',
                'wants_ride': 'no', 'station_pickup': 'no'}

    def contact(self, updates=True):
        data = {'contact_email': 'updates@example.com', 'language': 'fr', 'notes': 'Tot dan!'}
        if updates:
            data['practical_updates'] = 'on'
        return data

    def reach_contact(self, guests=0):
        for step, data in [
            ('aanwezigheid', self.attendance(guests)),
            ('eten-en-drinken', {'dietary_requirements': 'Sam: vegetarisch', 'allergies': 'Gast 1: pinda'}),
            ('overnachting', self.accommodation()),
            ('reis-en-vervoer', self.travel()),
        ]:
            response = self.client.post(self.url(step), data)
            self.assertEqual(response.status_code, 302, response.content)

    def test_home_redirect_and_five_step_navigation(self):
        self.assertRedirects(self.client.get('/'), self.url('aanwezigheid'))
        response = self.client.get(self.url('aanwezigheid'))
        for title in ['Aanwezigheid', 'Eten en drinken', 'Overnachting', 'Reis en vervoer', 'Contact en communicatie']:
            self.assertContains(response, title)
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.assertContains(response, 'id="guest-template"')

    def test_cannot_skip_steps(self):
        for step in ['eten-en-drinken', 'overnachting', 'reis-en-vervoer', 'contact-en-communicatie']:
            self.assertRedirects(self.client.get(self.url(step)), self.url('aanwezigheid'))
        self.assertRedirects(self.client.post(self.url('contact-en-communicatie'), self.contact()), self.url('aanwezigheid'))
        self.assertEqual(Registration.objects.count(), 0)

    def test_complete_group_registration_saves_all_answers(self):
        self.reach_contact(1)
        self.assertEqual(Registration.objects.count(), 0)
        response = self.client.post(self.url('contact-en-communicatie'), self.contact(), follow=True)
        self.assertContains(response, '2 personen')
        registration = Registration.objects.get()
        self.assertTrue(registration.attending)
        self.assertEqual(registration.party_size, 2)
        self.assertEqual(registration.participants.count(), 2)
        self.assertEqual(registration.participants.filter(is_primary=True).count(), 1)
        self.assertEqual(registration.dietary_requirements, 'Sam: vegetarisch')
        self.assertEqual(registration.allergies, 'Gast 1: pinda')
        self.assertTrue(registration.accommodation_help)
        self.assertEqual(registration.accommodation_people, 2)
        self.assertEqual(registration.accommodation_preference, 'bnb')
        self.assertIn('Vrijdag', registration.accommodation_nights)
        self.assertTrue(registration.accommodation_transport)
        self.assertEqual(registration.travel_method, 'car')
        self.assertTrue(registration.carpool_available)
        self.assertFalse(registration.wants_ride)
        self.assertFalse(registration.station_pickup)
        self.assertEqual(registration.contact_email, 'updates@example.com')
        self.assertEqual(registration.language, 'fr')
        self.assertTrue(registration.practical_updates)
        self.assertNotIn('rsvp_draft', self.client.session)

    def test_decline_skips_irrelevant_steps_and_records_zero(self):
        data = self.attendance(2, 'no')
        del data['party_size']
        response = self.client.post(self.url('aanwezigheid'), data)
        self.assertRedirects(response, self.url('contact-en-communicatie'))
        response = self.client.post(self.url('contact-en-communicatie'), self.contact(False), follow=True)
        self.assertContains(response, 'Je afmelding is opgeslagen')
        registration = Registration.objects.get()
        self.assertFalse(registration.attending)
        self.assertEqual(registration.party_size, 0)
        self.assertEqual(registration.participants.count(), 1)  # Respondent only.
        self.assertFalse(registration.practical_updates)
        self.assertFalse(registration.accommodation_help)

    def test_back_navigation_restores_values_and_guest_contacts(self):
        self.reach_contact(1)
        response = self.client.get(self.url('aanwezigheid'))
        self.assertContains(response, 'sam@example.com')
        self.assertContains(response, 'gast0@example.com')
        self.assertTrue(response.context['form']['attending'].value() == 'yes')
        self.assertContains(response, 'href="/aanmelden/contact-en-communicatie/"')
        response = self.client.get(self.url('overnachting'))
        self.assertContains(response, 'Vrijdag 11 juni')
        response = self.client.get(self.url('eten-en-drinken'))
        self.assertContains(response, 'Sam: vegetarisch')

    def test_changing_to_decline_discards_old_travel_answers(self):
        self.reach_contact()
        self.client.post(self.url('aanwezigheid'), self.attendance(attending='no'))
        self.client.post(self.url('contact-en-communicatie'), self.contact(False))
        registration = Registration.objects.get()
        self.assertEqual(registration.travel_method, '')
        self.assertEqual(registration.dietary_requirements, '')
        self.assertFalse(registration.accommodation_help)

    def test_party_size_must_match_guest_list(self):
        data = self.attendance(1)
        data['party_size'] = 3
        response = self.client.post(self.url('aanwezigheid'), data)
        self.assertContains(response, 'Het aantal personen moet overeenkomen')
        self.assertNotIn('aanwezigheid', self.client.session.get('rsvp_draft', {}))

    def test_invalid_guest_does_not_advance_or_save(self):
        for field in ['name', 'email', 'phone']:
            with self.subTest(field=field):
                data = self.attendance(1)
                data[f'guests-0-{field}'] = ''
                response = self.client.post(self.url('aanwezigheid'), data)
                self.assertEqual(response.status_code, 200)
                self.assertNotIn('aanwezigheid', self.client.session.get('rsvp_draft', {}))
        self.assertEqual(Participant.objects.count(), 0)

    def test_invalid_phone_and_excess_guests_are_rejected(self):
        for phone in ['abcdefg', '-------']:
            data = self.attendance()
            data['primary-phone'] = phone
            self.assertEqual(self.client.post(self.url('aanwezigheid'), data).status_code, 200)
        self.assertEqual(self.client.post(self.url('aanwezigheid'), self.attendance(11)).status_code, 200)
        self.assertEqual(Registration.objects.count(), 0)

    def test_missing_management_data_is_rejected_for_attendance(self):
        data = self.attendance()
        del data['guests-TOTAL_FORMS']
        response = self.client.post(self.url('aanwezigheid'), data)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('aanwezigheid', self.client.session.get('rsvp_draft', {}))

    def test_non_javascript_guest_fields_can_be_requested(self):
        data = self.attendance()
        data.update({'party_size': 3, 'show_guests': '1'})
        response = self.client.post(self.url('aanwezigheid'), data)
        self.assertContains(response, 'name="guests-1-name"')
        self.assertEqual(Registration.objects.count(), 0)

    def test_accommodation_requires_details_only_when_help_is_requested(self):
        form = AccommodationForm({'accommodation_help': 'yes', 'accommodation_transport': 'no'})
        self.assertFalse(form.is_valid())
        self.assertIn('accommodation_people', form.errors)
        self.assertIn('accommodation_nights', form.errors)
        self.assertIn('accommodation_preference', form.errors)
        form = AccommodationForm({'accommodation_help': 'no', 'accommodation_transport': 'yes'})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data['accommodation_people'])

    def test_accommodation_person_count_is_bounded(self):
        for count in ['0', '12']:
            data = self.accommodation()
            data['accommodation_people'] = count
            self.assertFalse(AccommodationForm(data).is_valid())

    def test_travel_conditional_answers(self):
        data = {'travel_method': 'train', 'wants_ride': 'yes', 'station_pickup': 'yes'}
        form = TravelForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertFalse(form.cleaned_data['carpool_available'])
        data['travel_method'] = 'other'
        self.assertFalse(TravelForm(data).is_valid())
        data['travel_other'] = 'Fiets'
        self.assertTrue(TravelForm(data).is_valid())

    def test_contact_validation_and_consent_default(self):
        self.reach_contact()
        response = self.client.get(self.url('contact-en-communicatie'))
        self.assertContains(response, 'value="sam@example.com"')
        data = self.contact(False)
        data['contact_email'] = 'geen-email'
        self.assertEqual(self.client.post(self.url('contact-en-communicatie'), data).status_code, 200)
        self.assertEqual(Registration.objects.count(), 0)
        self.client.post(self.url('contact-en-communicatie'), self.contact(False))
        self.assertFalse(Registration.objects.get().practical_updates)

    def test_resubmission_does_not_duplicate_registration(self):
        self.reach_contact()
        for _ in range(2):
            self.client.post(self.url('contact-en-communicatie'), self.contact())
        self.assertEqual(Registration.objects.count(), 1)

    def test_confirmation_privacy_and_csrf(self):
        self.assertRedirects(self.client.get(reverse('confirmation')), reverse('register'), fetch_redirect_response=False)
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(self.url('aanwezigheid'), self.attendance()).status_code, 403)
        self.reach_contact()
        self.client.post(self.url('contact-en-communicatie'), self.contact())
        response = self.client.get(reverse('confirmation'))
        self.assertNotContains(response, 'sam@example.com')
        self.assertNotContains(response, 'updates@example.com')
        self.assertIn('no-store', response.headers['Cache-Control'])

    def test_admin_shows_new_answers(self):
        self.reach_contact()
        self.client.post(self.url('contact-en-communicatie'), self.contact())
        admin = get_user_model().objects.create_superuser('beheer', 'beheer@example.com', 'test-password-only')
        self.client.force_login(admin)
        response = self.client.get(reverse('admin:registrations_registration_change', args=[Registration.objects.get().pk]))
        self.assertContains(response, 'updates@example.com')
        self.assertContains(response, 'Vrijdag 11 juni')
