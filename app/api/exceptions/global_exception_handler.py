from fastapi import HTTPException, status

class GeoDataFrameEmptyException(HTTPException):
    def __init__(self, message: str, status: int = status.HTTP_404_NOT_FOUND):
        super().__init__(
            status_code=status,
            detail=message
        )

class MissingCrsInfoException(HTTPException):
    def __init__(self, message: str, status: int = status.HTTP_404_NOT_FOUND):
        super().__init__(
            status_code=status,
            detail=message
        )

class InvalidFileException(HTTPException):
    def __init__(self, message: str, status: int = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE):
        super().__init__(
            status_code=status,
            detail=message
        )

class MaximumFileSizeException(HTTPException):
    def __init__(self, message: str, status: int = status.HTTP_413_CONTENT_TOO_LARGE):
        super().__init__(
            status_code=status,
            detail=message
        )