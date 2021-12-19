from django.contrib import admin

from wallet.models import Account


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("owner", "address", "balance")
