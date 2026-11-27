from django.test import Client, TestCase
from django.utils import translation
from .models import Registration
from .tests import RegistrationTests as Payloads


class EnglishRegistrationTests(TestCase):
    attendance = Payloads.attendance
    accommodation = Payloads.accommodation
    travel = Payloads.travel
    contact = Payloads.contact

    def tearDown(self):
        translation.activate('nl')

    def url(self, step):
        return f'/en/aanmelden/{step}/'

    def reach_contact(self, guests=0):
        pages = [
            ('aanwezigheid', self.attendance(guests), 'Will you be attending the wedding celebration?'),
            ('eten-en-drinken', {'dietary_requirements': 'Sam: vegetarian'}, 'Do you have any dietary requirements?'),
            ('overnachting', self.accommodation(), 'Which nights would you like to stay?'),
            ('reis-en-vervoer', self.travel(), 'How will you travel to France?'),
        ]
        for step, data, question in pages:
            page = self.client.get(self.url(step))
            self.assertContains(page, question)
            self.assertContains(page, '<html lang="en">')
            self.assertNotContains(page, 'Je antwoorden')
            response = self.client.post(self.url(step), data)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith('/en/'))

    def test_english_page_and_maps_are_translated(self):
        response = self.client.get(self.url('aanwezigheid'))
        for text in ['Attendance', 'Food and drink', 'Accommodation', 'Travel and transport',
                     'Contact and communication', '10 July 2027', 'Clairey, France',
                     'View the address on Google Maps', 'Add a guest', 'Full name',
                     'Email address', 'Phone number', 'First and last name',
                     'Step 1 of 5', 'Guest', 'Remove', 'Show guest fields',
                     'You have reached the maximum of 10 additional guests.']:
            self.assertContains(response, text)
        self.assertContains(response, 'https://www.google.com/maps/search/?api=1')
        self.assertNotContains(response, 'Een gast toevoegen')
        self.assertNotContains(response, 'Frankrijk')

    def test_complete_english_group_registration(self):
        self.reach_contact(1)
        page = self.client.get(self.url('contact-en-communicatie'))
        self.assertContains(page, 'What is your email address?')
        self.assertContains(page, 'May we send you practical updates about the celebration?')
        self.assertContains(page, 'Submit RSVP')
        self.assertEqual(page.context['form']['language'].value(), 'en')
        response = self.client.post(self.url('contact-en-communicatie'), self.contact(), follow=True)
        self.assertContains(response, 'Your RSVP for 2 people has been saved.')
        self.assertContains(response, 'RSVP reference:')
        registration = Registration.objects.get()
        self.assertEqual(registration.party_size, 2)
        self.assertEqual(registration.dietary_requirements, 'Sam: vegetarian')
        self.assertEqual(registration.language, 'fr')  # Communication language is independent.

    def test_english_single_person_confirmation(self):
        self.reach_contact()
        response = self.client.post(self.url('contact-en-communicatie'), self.contact(), follow=True)
        self.assertContains(response, 'Your RSVP for 1 person has been saved.')

    def test_english_decline(self):
        response = self.client.post(self.url('aanwezigheid'), self.attendance(attending='no'))
        self.assertEqual(response.url, self.url('contact-en-communicatie'))
        response = self.client.post(self.url('contact-en-communicatie'), self.contact(False), follow=True)
        self.assertContains(response, 'Thank you for letting us know.')
        self.assertFalse(Registration.objects.get().attending)

    def test_english_validation_messages(self):
        data = self.attendance(1)
        data['primary-phone'] = '-------'
        data['guests-0-email'] = 'invalid'
        response = self.client.post(self.url('aanwezigheid'), data)
        self.assertContains(response, 'Enter a phone number containing 7 to 15 digits.')
        self.assertContains(response, 'Enter a valid email address.')
        self.assertContains(response, 'Your answers have not been saved yet.')
        self.assertNotContains(response, 'Vul een')
        data = self.attendance()
        data['party_size'] = 3
        response = self.client.post(self.url('aanwezigheid'), data)
        self.assertContains(response, 'The number of people must match yourself and the guests entered below.')

    def test_english_accommodation_and_travel_options_and_errors(self):
        self.client.post(self.url('aanwezigheid'), self.attendance())
        self.client.post(self.url('eten-en-drinken'), {})
        response = self.client.get(self.url('overnachting'))
        self.assertContains(response, 'Holiday home')
        self.assertContains(response, 'Campsite')
        self.assertContains(response, 'No preference')
        response = self.client.post(self.url('overnachting'), {'accommodation_help': 'yes', 'accommodation_transport': 'no'})
        self.assertContains(response, 'Please fill this in so we can help you find accommodation.')
        self.client.post(self.url('overnachting'), self.accommodation())
        response = self.client.get(self.url('reis-en-vervoer'))
        for option in ['Car', 'Train', 'Plane', 'Other']:
            self.assertContains(response, f'>{option}</option>')
        response = self.client.post(self.url('reis-en-vervoer'), {'travel_method': 'other', 'wants_ride': 'no', 'station_pickup': 'no'})
        self.assertContains(response, 'Please tell us how you will travel to France.')

    def test_switch_language_preserves_saved_draft_and_step(self):
        self.client.post('/aanmelden/aanwezigheid/', self.attendance(1))
        response = self.client.post('/i18n/setlang/', {'language': 'en', 'next': self.url('eten-en-drinken')})
        self.assertEqual(response.url, self.url('eten-en-drinken'))
        self.assertEqual(self.client.cookies['django_language'].value, 'en')
        self.assertContains(self.client.get(response.url), 'Food and drink')
        response = self.client.get(self.url('aanwezigheid'))
        self.assertContains(response, 'sam@example.com')
        self.assertContains(response, 'gast0@example.com')
        self.assertContains(response, 'name="next" value="/aanmelden/aanwezigheid/"')
        response = self.client.post('/i18n/setlang/', {'language': 'nl', 'next': '/aanmelden/aanwezigheid/'})
        self.assertEqual(response.url, '/aanmelden/aanwezigheid/')
        response = self.client.get(response.url)
        self.assertContains(response, 'Kom je naar het trouwfeest?')
        self.assertContains(response, 'gast0@example.com')

    def test_language_switch_enforces_csrf(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/i18n/setlang/', {'language': 'en'}).status_code, 403)
        client.get(self.url('aanwezigheid'))
        token = client.cookies['csrftoken'].value
        response = client.post('/i18n/setlang/', {'language': 'nl', 'next': '/aanmelden/aanwezigheid/', 'csrfmiddlewaretoken': token})
        self.assertEqual(response.status_code, 302)
