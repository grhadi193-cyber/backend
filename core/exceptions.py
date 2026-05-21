class NotFoundError(Exception):
    pass


class OTPInvalidError(Exception):
    pass


class OTPExpiredError(Exception):
    pass


class OTPNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    """Raised when a product does not have enough stock to fulfil an order line."""

    def __init__(self, product_name: str, available: int, requested: int):
        self.product_name = product_name
        self.available = available
        self.requested = requested
        super().__init__(
            f"Insufficient stock for '{product_name}': "
            f"requested {requested}, available {available}."
        )


class AppException(Exception):
    """Generic app exception with HTTP status code."""

    def __init__(self, detail: str, status_code: int = 400):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)
