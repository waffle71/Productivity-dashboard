from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Task
from .models import UserAccount

admin.site.register(Task)
admin.site.register(UserAccount)
