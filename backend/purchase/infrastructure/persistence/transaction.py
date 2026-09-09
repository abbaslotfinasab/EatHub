from django.db import transaction

from purchase.application.ports.goods_receipt import TransactionManager


class DjangoTransactionManager(TransactionManager):
    def atomic(self):
        return transaction.atomic()
