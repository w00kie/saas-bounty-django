from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from stellar_sdk import Server
from decimal import Decimal

user_model = get_user_model()


class Command(BaseCommand):
    help = "Watches payments made to the vault account."

    def tx_handler(self, pmt):
        try:
            pmt_id = pmt.get("id")
            from_account = pmt.get("from")
            to_account = pmt.get("to")
            to_muxed = pmt.get("to_muxed")
            to_muxed_id = pmt.get("to_muxed_id")
            asset_type = pmt.get("asset_type")
            amount = pmt.get("amount")

            # Ignore non-incoming payments
            if to_account != settings.VAULT_PUBLIC_KEY:
                return None
            # Ignore non-native assets
            if asset_type != "native":
                return None

            user = user_model.objects.get(id=to_muxed_id)
            user.account.balance += Decimal(amount)
            user.account.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f"INCOMING TRANSACTION for {user.username}, amount={amount}"
                )
            )
        except user_model.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"USER NOT FOUND for muxed id = {to_muxed_id}")
            )
        except TypeError:
            self.stdout.write(self.style.ERROR(f"INVALID AMOUNT {amount}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"ERROR: {e}"))

    def handle(self, *args, **options):
        try:
            server = Server(settings.STELLAR_SERVER)
            for pmt in (
                server.payments()
                .for_account(settings.VAULT_PUBLIC_KEY)
                .cursor("now")
                .stream()
            ):
                self.tx_handler(pmt)
        except KeyboardInterrupt:
            self.stdout.write(self.style.NOTICE("SHUTTING DOWN WATCHER"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"ERROR: {e}"))
