from django.db import models

# Create your models here.
class inventory_model(models.Model):
    category = models.CharField(max_length=150)
    text = models.TextField()
    email = models.EmailField(unique=True)