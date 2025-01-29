from django.db import models


class Location(models.Model):
    city = models.CharField(max_length=100, db_index=True)
    country = models.CharField(max_length=100, db_index=True)

    class Meta:
        unique_together = ("city", "country")  # Ensure uniqueness
        indexes = [
            models.Index(fields=["city", "country"]),
        ]

    def __str__(self):
        return f"{self.city}, {self.country}"
