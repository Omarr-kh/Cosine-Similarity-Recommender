from django.db import models


class RealState(models.Model):
    price = models.PositiveBigIntegerField()
    bedrooms = models.PositiveIntegerField()
    bathrooms = models.PositiveIntegerField()
    sqft = models.DecimalField(max_digits=10, decimal_places=3)
    year_built = models.PositiveIntegerField()
    property_type = models.CharField(
        max_length=50,
        choices=[('residential', 'Residential'), ('commercial', 'Commercial')],
        default='residential',
    )
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    parking_spaces = models.PositiveIntegerField(default=0)
    has_garage = models.BooleanField(default=False)
    has_pool = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Real Estate Property"
        verbose_name_plural = "Real Estate Properties"
