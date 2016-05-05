from django.contrib import admin

from .models import *

# Register your models here.

admin.site.register(SBikeUser)
admin.site.register(Client)
admin.site.register(Admin)
admin.site.register(Employee)
admin.site.register(Station)
admin.site.register(Bike)
admin.site.register(Loan)
admin.site.register(Sanction)
admin.site.register(Notification)
