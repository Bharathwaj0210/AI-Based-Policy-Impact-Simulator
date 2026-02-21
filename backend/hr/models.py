from django.db import models

# Create your models here.
class HRPolicy(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    policy_type = models.CharField(max_length=100) # e.g., Leave, Conduct, etc.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
