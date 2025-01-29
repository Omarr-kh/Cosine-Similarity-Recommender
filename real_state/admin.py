from django.contrib import admin
from .models import RealState, UserInteraction, Location, Feature

admin.site.register(RealState)
admin.site.register(UserInteraction)
admin.site.register(Location)
admin.site.register(Feature)
