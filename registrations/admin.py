from django.utils.translation import gettext_lazy as _
from django.contrib import admin
from .models import Participant, Registration


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['reference', 'created_at', 'attending', 'party_size', 'contact_email', 'language', 'practical_updates']
    search_fields = ['participants__name', 'participants__email', 'participants__phone', 'contact_email', 'reference']
    list_filter = ['attending', 'language', 'practical_updates', 'accommodation_help', 'travel_method', 'station_pickup', 'created_at']
    readonly_fields = ['reference', 'created_at']
    inlines = [ParticipantInline]

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'is_primary', 'registration']
    search_fields = ['name', 'email', 'phone']
    list_filter = ['is_primary']


admin.site.site_header = _('Ons trouwfeest')
admin.site.site_title = _('Trouwfeest beheer')
admin.site.index_title = _('Aanmeldingen & deelnemers')
