# Ons trouwfeest

Nederlandse en Engelse Django-website met SQLite voor aanmeldingen voor een trouwfeest.

## Starten (Windows / PowerShell)

Python 3.10 of nieuwer is nodig. De projectomgeving is `.venv`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Als `.venv` al is aangemaakt, kun je de eerste stap overslaan. Op een systeem met uv kun je de eerste twee stappen ook uitvoeren met `uv venv --python 3.12 .venv` en `uv pip install --python .venv/Scripts/python.exe -r requirements.txt`.

Open http://127.0.0.1:8000/ voor de aanmeldpagina. Beheer aanmeldingen via http://127.0.0.1:8000/admin/ met het account dat je met `createsuperuser` hebt aangemaakt. Er is geen standaardwachtwoord.

## Functionaliteit

- Hoofdaanmelder plus maximaal tien extra gasten per aanmelding.
- Vijf formulierpagina's: Aanwezigheid, Eten en drinken, Overnachting, Reis en vervoer, Contact en communicatie.
- Bij afmelding worden de stappen voor eten, overnachting en vervoer overgeslagen.
- Naam, e-mailadres en telefoonnummer voor elke deelnemer; alle drie zijn verplicht.
- Extra gasten toevoegen en verwijderen zonder paginavernieuwing.
- Het aantal aanwezigen moet gelijk zijn aan het aantal ingevulde personen, inclusief de hoofdaanmelder.
- Dieetwensen en allergieën zijn optioneel; vermeld bij de antwoorden voor wie ze gelden.
- Accommodatiehulp, aantal personen, nachten, type accommodatie en vervoer naar de feestlocatie.
- Reismethode naar Frankrijk, carpoolen, meerijden en ophalen vanaf een station.
- E-mailadres voor communicatie, voorkeurstaal (Nederlands, Engels, Frans of Duits) en afzonderlijke toestemming voor praktische updates.
- Optioneel opmerkingenveld en bevestiging na het opslaan.
- Aanmelding en deelnemers worden samen opgeslagen; bij fouten wordt niets opgeslagen.
- Tussentijdse antwoorden staan in de serversessie na ‘Volgende’; definitieve opslag gebeurt pas na ‘Antwoord versturen’. De sessie wordt niet in de URL gedeeld. Gebruik ‘Volgende’ om wijzigingen op een stap te bewaren voordat je via de navigatie naar een andere stap gaat.
- Beveiligde Django-beheeromgeving met zoekfunctie, filters en bewerkbare deelnemers.
- Deelnemerslijsten en contactgegevens zijn niet publiek zichtbaar.

Er worden geen bevestigingsmails of praktische updates verstuurd. De voorkeurstaal en toestemming worden opgeslagen voor de organisatie. De bevestiging verschijnt op de website. Telefoonnummers worden op formaat gecontroleerd, niet op bereikbaarheid. Zonder JavaScript kun je via ‘Gastenvelden tonen’ alsnog extra gasten invullen.

## Nederlands en Engels

Gebruik de NL/EN-knoppen bovenaan om van taal te wisselen. De Engelse versie begint op http://127.0.0.1:8000/en/. De Nederlandse URL's blijven ongewijzigd. De taalkeuze wordt onthouden in een cookie; opgeslagen antwoorden uit eerdere stappen blijven beschikbaar bij het wisselen. Klik op ‘Volgende’ om wijzigingen te bewaren voordat je wisselt.

Pagina's, vragen, keuzelijsten, foutmeldingen, gastenknoppen, locatie-informatie en bevestigingen zijn vertaald via Django i18n. De taal voor praktische informatie is een afzonderlijke formulierkeuze en wordt bij een nieuwe aanmelding voorgesteld op basis van de huidige taal van de website. Zelf ingevulde namen en antwoorden worden niet vertaald.

Engelse teksten staan in `locale/en/translations.json`. Na wijzigingen bouw je de standaard Django-catalogus opnieuw met:

```powershell
.\.venv\Scripts\python.exe tools/compile_translations.py
```

Dit genereert `locale/en/LC_MESSAGES/django.po` en `django.mo` zonder extra installatie van GNU gettext. Herstart de ontwikkelserver na wijzigingen aan vertalingen. Bij nieuwe Python-teksten gebruik je `gettext_lazy`; in templates `translate` of `blocktranslate`. Het hulpmiddel ondersteunt enkelvoudige berichten met optionele variabelen; de bevestiging gebruikt afzonderlijke berichten voor één persoon en meerdere personen.

Er is nog geen persoonlijke uitnodigingslijst. Gasten vullen zelf de namen uit hun uitnodiging in; deze worden niet gecontroleerd tegen een vooraf geladen gastenlijst. Bij afmelding bewaren we de contactgegevens van de respondent, met nul aanwezige personen. Bestaande aanmeldingen blijven bewaard; een gegevensmigratie vult hun communicatieadres en aantal personen in op basis van hun deelnemers.

## Personaliseren

Pas `WEDDING` onderaan `wedding/settings.py` aan:

```python
WEDDING = {
    'names': 'Naam & Naam',
    'date': 'Zaterdag 12 juni 2027 · vanaf 19:00',
    'location': 'Naam van de feestlocatie',
}
```

De datum is 10 juli 2027 en de locatie Clairey, Frankrijk, met een Google Maps-link naar 6, Rue de l'ecole, Clairey. De namen zijn nog neutraal. Vormgeving staat in `static/css/style.css` en `static/css/wizard.css`; de pagina's in `templates/`. Lettertypen laden van Google Fonts met lokale terugvallettertypen. Voeg bij aangepaste vertaalbare datum- en locatieteksten ook een Engelse vertaling aan het catalogusbestand toe.

## Database en controles

SQLite bewaart alles lokaal in `db.sqlite3`. Dit bestand staat buiten versiebeheer; maak er een back-up van als er echte aanmeldingen in staan. Een latere overstap naar MySQL vereist een databaseconfiguratie, driver en gegevensmigratie.

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

## Online zetten

Dit project is lokaal voorbereid en niet gepubliceerd. Django's `runserver` is bedoeld voor ontwikkeling. Voor productie zijn een geschikte Python-host, HTTPS, statische-bestandenconfiguratie en back-ups nodig. Zet `DJANGO_DEBUG=0`, stel een willekeurige `DJANGO_SECRET_KEY` in en configureer `DJANGO_ALLOWED_HOSTS`. Bij uitgeschakelde debug worden HTTPS en veilige cookies afgedwongen. Controleer de configuratie met `manage.py check --deploy` en verzamel statische bestanden met `manage.py collectstatic`.
