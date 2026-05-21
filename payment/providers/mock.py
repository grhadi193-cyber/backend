import logging
from .base import BasePaymentProvider

logger = logging.getLogger(__name__)

class MockProvider(BasePaymentProvider):
    @property
    def name(self) -> str:
        return "mock"

    def initiate(self, transaction) -> str:
        transaction_id = transaction.pk
        fake_url = (
            f"http://127.0.0.1:8000/api/payment/callback"
            f"?Authority=SANDBOX_{transaction_id}&Status=OK&transaction_id={transaction_id}"
        )
        transaction.gateway_response = {"debug": True, "fake_url": fake_url}
        logger.debug(f"[MockProvider] Returning fake URL: {fake_url}")
        return fake_url

    def verify(self, transaction, raw_params: dict) -> bool:
        authority = raw_params.get("Authority", "")
        status = raw_params.get("Status", "")
        success = authority.startswith("SANDBOX_") and status == "OK"
        
        transaction.ref_id = authority
        transaction.gateway_response = {**transaction.gateway_response, "verify_params": raw_params, "debug": True}
        
        return success
