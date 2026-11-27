from django.db import migrations


def backfill_existing_registrations(apps, schema_editor):
    Registration = apps.get_model('registrations', 'Registration')
    for registration in Registration.objects.using(schema_editor.connection.alias).filter(contact_email='').iterator():
        participants = registration.participants.using(schema_editor.connection.alias)
        primary = participants.filter(is_primary=True).first()
        registration.party_size = participants.count()
        if primary:
            registration.contact_email = primary.email
        registration.save(using=schema_editor.connection.alias, update_fields=['party_size', 'contact_email'])


class Migration(migrations.Migration):
    dependencies = [('registrations', '0002_registration_accommodation_help_and_more')]
    operations = [migrations.RunPython(backfill_existing_registrations, migrations.RunPython.noop)]
