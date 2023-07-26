from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    sub = models.UUIDField(null=True, unique=True)
