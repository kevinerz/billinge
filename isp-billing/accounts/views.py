from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auditlog.helpers import log_action
from common.permissions import IsSuperAdminOrTenantAdmin

from .models import User
from .serializers import UserSerializer, MeSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    Manajemen akun dashboard (bukan tenant_subscribers). Dibatasi
    tenant_admin ke atas — tenant_staff tidak diberi akses sama sekali,
    sama seperti NAS/tenant-integrations (akun = akses login).
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]

    def get_queryset(self):
        qs = User.objects.all().order_by('-created_at')
        user = self.request.user
        if user.role == 'super_admin':
            return qs
        # tenant_admin cuma lihat/kelola user di tenant-nya sendiri
        return qs.filter(tenant_id=user.tenant_id)

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'super_admin':
            created = serializer.save()
        else:
            role = serializer.validated_data.get('role')
            if role == 'super_admin':
                raise PermissionDenied('tenant_admin tidak boleh membuat user super_admin.')
            # Paksa tenant_id ke tenant sendiri, abaikan apa pun yang dikirim di body
            created = serializer.save(tenant_id=user.tenant_id)
        log_action(
            self.request, 'user.created', entity_type='user', entity_id=created.id,
            metadata={'email': created.email, 'role': created.role}, tenant_id=created.tenant_id,
        )

    def perform_update(self, serializer):
        old_role = serializer.instance.role
        user = self.request.user
        if user.role == 'super_admin':
            updated = serializer.save()
        else:
            role = serializer.validated_data.get('role', old_role)
            if role == 'super_admin':
                raise PermissionDenied('tenant_admin tidak boleh menaikkan role user jadi super_admin.')
            updated = serializer.save(tenant_id=user.tenant_id)
        if updated.role != old_role:
            log_action(
                self.request, 'user.role_changed', entity_type='user', entity_id=updated.id,
                metadata={'email': updated.email, 'old_role': old_role, 'new_role': updated.role},
                tenant_id=updated.tenant_id,
            )

    def perform_destroy(self, instance):
        if instance.pk == self.request.user.pk:
            raise ValidationError('Tidak bisa menghapus akun sendiri.')
        log_action(
            self.request, 'user.deleted', entity_type='user', entity_id=instance.id,
            metadata={'email': instance.email, 'role': instance.role}, tenant_id=instance.tenant_id,
        )
        instance.delete()


class MeView(APIView):
    """Profil user yang sedang login — dipakai dashboard buat tahu
    role/tenant_id sendiri tanpa perlu decode JWT di frontend."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)
