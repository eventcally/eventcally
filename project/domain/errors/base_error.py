class BaseError(Exception):
    def __init__(self, message: str = None, cause: Exception = None):
        self.message = message or self.default_message
        self.cause = cause
        super().__init__(self.message)

    default_message = "An error occurred"
