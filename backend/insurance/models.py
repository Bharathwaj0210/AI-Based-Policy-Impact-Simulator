from django.db import models

# Create your models here.
class InsurancePolicy(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100) # Health, Vehicle, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
