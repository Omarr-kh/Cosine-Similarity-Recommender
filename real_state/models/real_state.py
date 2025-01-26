from django.db import models


class RealState(models.Model):
    price = models.DecimalField(
        max_digits=15, decimal_places=3, db_index=True
    )  # Frequently filtered/sorted
    bedrooms = models.PositiveIntegerField(db_index=True)  # Useful for filtering
    bathrooms = models.PositiveIntegerField(db_index=True)  # Useful for filtering
    sqft = models.DecimalField(max_digits=15, decimal_places=3)
    year_built = models.PositiveIntegerField(
        db_index=True
    )  # Frequently filtered/sorted
    property_type = models.CharField(
        max_length=50,
        choices=[('residential', 'Residential'), ('commercial', 'Commercial')],
        default='residential',
        db_index=True,  # Frequently filtered
    )
    address = models.CharField(max_length=255)
    city = models.CharField(
        max_length=100, db_index=True
    )  # Useful for filtering by city
    country = models.CharField(max_length=100, db_index=True)  # Filtering by country
    parking_spaces = models.PositiveIntegerField(default=0)
    has_garage = models.BooleanField(
        default=False, db_index=True
    )  # Filtering by boolean
    has_pool = models.BooleanField(default=False, db_index=True)  # Filtering by boolean
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Real Estate Property"
        verbose_name_plural = "Real Estate Properties"
        indexes = [
            models.Index(fields=["price"]),  # Index on price
            models.Index(fields=["year_built"]),  # Index on year_built
            models.Index(
                fields=["city", "country"]
            ),  # Composite index for city and country
        ]
