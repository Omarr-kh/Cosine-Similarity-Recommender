from django.urls import path

from .views import *

urlpatterns = [
    path(
        'cosine-similarity-recommendations/',
        cosine_similarity_recommendations,
        name='cosine-similarity-recommendations/',
    ),
    path(
        'content-based-recommendations/',
        content_based_recommendations,
        name='content-based-recommendations',
    ),
    path(
        'user-based-cf-recommendations/',
        user_based_recommend_properties_cf,
        name='user-based-cf-recommendations',
    ),
    path(
        'item-based-cf-recommendations/',
        item_based_recommend_properties_cf,
        name='item-based-cf-recommendations',
    ),
]
