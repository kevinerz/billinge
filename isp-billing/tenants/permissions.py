from rest_framework.permissions import BasePermission


class IsSuperAdminOnly(BasePermission):
    """Cuma super_admin yang boleh (buat create/delete tenant)."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == 'super_admin'
        )


class IsSuperAdminOrOwnTenant(BasePermission):
    """
    super_admin: akses penuh ke semua tenant.
    tenant_admin / tenant_staff: cuma bisa LIHAT tenant miliknya sendiri.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'super_admin':
            return True
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return obj.id == request.user.tenant_id
        return False
