from django.urls import path

from .views import *

urlpatterns = [
    path('recommendations/', get_recommendations, name='get-recommendations'),
    path('recommendations2/', recommend_properties, name='recommend-properties'),
    path('recommendations3/', recommend_properties_cf, name='recommend-properties3'),
]
