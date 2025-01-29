from django.db import models
from .location import Location
from .feature import Feature


class RealState(models.Model):
    price = models.DecimalField(max_digits=15, decimal_places=3, db_index=True)
    bedrooms = models.PositiveIntegerField(db_index=True)
    bathrooms = models.PositiveIntegerField(db_index=True)
    sqft = models.DecimalField(max_digits=15, decimal_places=3)
    year_built = models.PositiveIntegerField(db_index=True)
    property_type = models.CharField(
        max_length=50,
        choices=[('residential', 'Residential'), ('commercial', 'Commercial')],
        default='residential',
        db_index=True,
    )
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="properties", null=True
    )
    parking_spaces = models.PositiveIntegerField(default=0)
    has_garage = models.BooleanField(default=False, db_index=True)
    has_pool = models.BooleanField(default=False, db_index=True)
    description = models.TextField(blank=True, null=True)
    features = models.ManyToManyField(Feature, related_name="real_states")

    class Meta:
        verbose_name = "Real Estate Property"
        verbose_name_plural = "Real Estate Properties"
        indexes = [
            models.Index(fields=["price"]),
            models.Index(fields=["year_built"]),
            models.Index(fields=["price", "bedrooms", "bathrooms"]),
        ]

    def __str__(self):
        return f"{self.property_type} - ${self.price} in {self.location.city}, {self.location.country}"
