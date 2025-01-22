from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from real_state.models import RealState

from .system import real_state_recommender


@receiver(post_save, sender=RealState)
def update_recommendation_on_save(sender, instance, **kwargs):
    real_state_recommender.load_properties()


@receiver(post_delete, sender=RealState)
def update_recommendation_on_delete(sender, instance, **kwargs):
    real_state_recommender.load_properties()
