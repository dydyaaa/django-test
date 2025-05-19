from django.db import models
from django.contrib.auth.models import User


class Ad(models.Model):
    ad_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    description = models.TextField()
    image_url = models.URLField(max_length=250, null=True, blank=True)
    category = models.CharField(max_length=128)
    condition = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self) -> str:
        return self.title


class ExchangeProposal(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
    )

    exchange_id = models.AutoField(primary_key=True)
    ad_sender = models.ForeignKey('Ad', on_delete=models.CASCADE, related_name='sent_proposals')
    ad_receiver = models.ForeignKey('Ad', on_delete=models.CASCADE, related_name='received_proposals')
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Предложение от {self.ad_sender} к {self.ad_receiver} ({self.status})"
    