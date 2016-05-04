from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(PaperModel)
admin.site.register(ChoiceModel)
admin.site.register(FillBlankModel)