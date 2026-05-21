from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class PaymentSession:
    payment_url: str
    transaction_id: int
    provider: str

class BasePaymentProvider(ABC):
    @abstractmethod
    def initiate(self, transaction) -> str:
        """Returns payment_url and may mutate transaction"""

    @abstractmethod
    def verify(self, transaction, raw_params: dict) -> bool:
        """Returns True if paid"""

    @property
    @abstractmethod
    def name(self) -> str: ...
