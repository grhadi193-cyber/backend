from pydantic import BaseModel


class InitiatePaymentIn(BaseModel):
    order_id: int


class InitiatePaymentOut(BaseModel):
    payment_url: str
    transaction_id: int


class VerifyCallbackIn(BaseModel):
    # Zarinpal uses Authority + Status query params
    Authority: str = ""
    Status:    str = ""
    # Generic fallback fields (other gateways)
    transaction_id: int = 0
    # توکن یک‌بارمصرف برای تأیید اصالت کالبک
    cb_token: str = ""
