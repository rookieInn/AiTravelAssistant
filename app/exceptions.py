class RefundNotFoundError(Exception):
    pass


class InvalidRefundStateError(Exception):
    pass


class RetryLimitExceededError(Exception):
    pass
