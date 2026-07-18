from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    # write_only + tidak wajib di update (PATCH ganti field lain tanpa
    # perlu kirim ulang password). Wajib diisi saat create — dicek di
    # validate() karena instance belum ada.
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'tenant_id', 'role', 'email', 'password', 'full_name', 'status', 'last_login', 'created_at', 'updated_at']
        read_only_fields = ['id', 'last_login', 'created_at', 'updated_at']

    def validate(self, data):
        if self.instance is None and not data.get('password'):
            raise serializers.ValidationError({'password': 'Wajib diisi saat membuat user baru.'})

        role = data.get('role', getattr(self.instance, 'role', None))
        tenant_id = data.get('tenant_id', getattr(self.instance, 'tenant_id', None))
        # Cermin dari CHECK constraint chk_users_role_tenant di sql/007_users_roles.sql
        if role == 'super_admin' and tenant_id is not None:
            raise serializers.ValidationError('super_admin tidak boleh punya tenant_id.')
        if role in ('tenant_admin', 'tenant_staff'):
            if tenant_id is None:
                raise serializers.ValidationError('tenant_admin/tenant_staff wajib punya tenant_id.')
            from tenants.models import Tenant
            if not Tenant.objects.filter(id=tenant_id).exists():
                raise serializers.ValidationError('tenant_id tidak ditemukan.')
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'tenant_id', 'role', 'email', 'full_name', 'status', 'last_login']
        read_only_fields = fields
