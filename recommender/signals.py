from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from real_state.models import RealState

from .system import get_real_state_recommender


@receiver(post_save, sender=RealState)
def handle_property_save(sender, instance, created, **kwargs):
    real_state_recommender = get_real_state_recommender()
    # Create the property data from the instance
    property_data = {
        'id': instance.id,
        'price': instance.price,
        'bedrooms': instance.bedrooms,
        'bathrooms': instance.bathrooms,
        'sqft': instance.sqft,
        'year_built': instance.year_built,
        'parking_spaces': instance.parking_spaces,
    }

    if created:
        # Add the property if it's a new one
        real_state_recommender.add_property(property_data)
    else:
        # Remove the old property if it's an update
        real_state_recommender.remove_property(instance.id)
        # Add the updated property
        real_state_recommender.add_property(property_data)


@receiver(post_delete, sender=RealState)
def handle_property_delete(sender, instance, **kwargs):
    real_state_recommender = get_real_state_recommender()
    try:
        # Remove the property from the recommender
        real_state_recommender.remove_property(instance.id)
    except:
        pass
