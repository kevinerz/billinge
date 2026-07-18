from rest_framework.permissions import BasePermission


class IsSuperAdminOnly(BasePermission):
    """Cuma super_admin yang boleh (buat create/delete data platform-level)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'super_admin'
        )


class IsSuperAdminOrOwnTenant(BasePermission):
    """
    Aturan umum buat semua tabel yang punya kolom tenant_id:
    - super_admin: akses penuh ke semua tenant
    - tenant_admin / tenant_staff: cuma boleh lihat/ubah data tenant-nya sendiri
    Dipakai di get_queryset() ViewSet buat filter list, dan di sini buat
    jaga-jaga di level object (misal akses langsung /api/xxx/<id>/).
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'super_admin':
            return True
        return getattr(obj, 'tenant_id', None) == request.user.tenant_id


class IsSuperAdminOrTenantAdmin(BasePermission):
    """Buat aksi tulis (create/update/delete) di data milik tenant sendiri
    (misal service_plans) — tenant_admin boleh, tenant_staff TIDAK boleh."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ('super_admin', 'tenant_admin')
        )


def scope_queryset_to_tenant(queryset, user):
    """Helper dipakai di get_queryset(): super_admin lihat semua, selain itu
    cuma baris yang tenant_id-nya sama dengan tenant_id user yang login."""
    if user.role == 'super_admin':
        return queryset
    return queryset.filter(tenant_id=user.tenant_id)
