class DomainError(Exception):
    status_code = 400

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class ResourceNotFound(DomainError):
    status_code = 404


class InvalidMessage(DomainError):
    status_code = 422


class UnsupportedMediaType(DomainError):
    status_code = 415


class UploadTooLarge(DomainError):
    status_code = 413
