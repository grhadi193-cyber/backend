from django.db import models
from store.models import Order


class Transaction(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED  = "failed",  "Failed"

    order            = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="transactions")
    amount           = models.DecimalField(max_digits=14, decimal_places=0)
    provider         = models.CharField(max_length=50, default="zarinpal")
    ref_id           = models.CharField(max_length=128, blank=True, default="")
    status           = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    gateway_response = models.JSONField(default=dict, blank=True)
    callback_token   = models.CharField(max_length=64, blank=True, db_index=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Transaction #{self.pk} | Order #{self.order_id} | {self.status}"
