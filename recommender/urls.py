from django.urls import path

from .views import *

urlpatterns = [
    path('recommendations/', get_recommendations, name='get-recommendations'),
]
