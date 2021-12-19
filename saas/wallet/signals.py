from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from rest_framework.authtoken.models import Token
from stellar_sdk import MuxedAccount

from wallet.models import Account


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """Create an auth token for the API when a user registers."""
    if created:
        Token.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_wallet(sender, instance=None, created=False, **kwargs):
    """Create a muxed wallet when a user registers."""
    if created:
        Account.objects.create(
            owner=instance,
            address=MuxedAccount(settings.VAULT_PUBLIC_KEY, instance.id).account_muxed,
        )
