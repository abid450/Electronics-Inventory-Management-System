from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(PaymentTransaction)
admin.site.register(PaymentLog)