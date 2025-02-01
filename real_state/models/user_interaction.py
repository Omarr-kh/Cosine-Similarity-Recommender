from django.contrib.auth.models import User
from django.db import models
from .real_state import RealState


class UserInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(RealState, on_delete=models.CASCADE)
    interaction_type = models.CharField(
        max_length=50,
        choices=[('view', 'View'), ('like', 'Like'), ('save', 'Save')],
        default='view',
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["property"]),
            models.Index(fields=["interaction_type"]),
        ]
        unique_together = (
            'user',
            'property',
        )  # Ensure a user can't interact with the same property multiple times
