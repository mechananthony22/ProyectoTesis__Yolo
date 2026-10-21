from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    role = models.CharField(max_length=20, choices=[('admin', 'Administrador'), ('researcher', 'Investigador')], default='researcher')
    @property
    def administrator(self):
        return self.is_superuser or self.role == 'admin'
