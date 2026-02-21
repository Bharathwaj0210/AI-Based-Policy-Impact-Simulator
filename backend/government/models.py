from django.db import models

# Create your models here.
class GovernmentPolicy(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    eligibility_criteria = models.TextField()
    benefit_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
