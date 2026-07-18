from rest_framework import serializers

from .models import Nas


class NasSerializer(serializers.ModelSerializer):
    tenant_slug = serializers.CharField(source='tenant.slug', read_only=True)

    class Meta:
        model = Nas
        fields = [
            'id', 'tenant', 'tenant_slug', 'nasname', 'shortname', 'type', 'ports',
            'secret', 'server', 'community', 'description', 'last_contact_at',
        ]
        # secret SELALU digenerate otomatis di server (lihat views.py perform_create) —
        # tidak pernah diterima dari input client, biar tidak ada yang iseng pasang
        # secret lemah/dipakai ulang. last_contact_at diupdate FreeRADIUS sendiri.
        read_only_fields = ['id', 'secret', 'last_contact_at']
