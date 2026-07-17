from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email harus diisi')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'super_admin')
        extra_fields.setdefault('status', 'active')
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('tenant_admin', 'Tenant Admin'),
        ('tenant_staff', 'Tenant Staff'),
    ]
    STATUS_CHOICES = [('active', 'Active'), ('suspended', 'Suspended')]

    id = models.BigAutoField(primary_key=True)
    tenant_id = models.BigIntegerField(null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255, db_column='password_hash')
    full_name = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    last_login = models.DateTimeField(null=True, blank=True, db_column='last_login_at')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role']

    class Meta:
        db_table = 'users'
        managed = False

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def is_staff(self):
        return True

    @property
    def is_superuser(self):
        return self.role == 'super_admin'

    def has_perm(self, perm, obj=None):
        return self.role == 'super_admin'

    def has_module_perms(self, app_label):
        return self.role == 'super_admin'

    def __str__(self):
        return self.email
