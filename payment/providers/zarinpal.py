import logging
from decimal import Decimal
from django.conf import settings
from .base import BasePaymentProvider

logger = logging.getLogger(__name__)

class ZarinpalProvider(BasePaymentProvider):
    @property
    def name(self) -> str:
        return "zarinpal"

    def initiate(self, transaction) -> str:
        from azbankgateways import bankfactories, models as bank_models
        factory = bankfactories.BankFactory()
        bank = factory.create(bank_type=bank_models.BankType.ZARINPAL)

        amount = Decimal(str(transaction.amount))
        bank.set_amount(int(amount) * 10)
        bank.set_mobile_number(transaction.order.user.phone_number)
        bank.set_client_callback_url(settings.PAYMENT_CALLBACK_URL)
        bank.set_order_id(str(transaction.order.pk))

        redirect_url = bank.redirect_gateway_url()
        transaction.ref_id = bank.get_transaction_id() or ""
        transaction.gateway_response = {"gateway_token": transaction.ref_id}
        
        return redirect_url

    def verify(self, transaction, raw_params: dict) -> bool:
        from azbankgateways import bankfactories, models as bank_models
        factory = bankfactories.BankFactory()
        bank = factory.create(bank_type=bank_models.BankType.ZARINPAL)

        bank.set_gateway_callback_parameters(raw_params, bank_models.BankType.ZARINPAL)
        bank.verify_from_gateway(request=None)

        tracking_code = bank.get_tracking_code()
        success = bank.is_success()

        transaction.ref_id = str(tracking_code or "")
        transaction.gateway_response = {
            **transaction.gateway_response,
            "tracking_code": tracking_code,
            "verify_params": raw_params,
        }
        
        return success
