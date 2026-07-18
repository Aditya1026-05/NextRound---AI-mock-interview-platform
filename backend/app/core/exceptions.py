from fastapi import HTTPException, status


class AuthenticationException(HTTPException):
    """Base exception for all authentication-related errors."""

    def __init__(
        self,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        detail: str = "Could not validate credentials",
        headers: dict[str, str] | None = None,
    ):
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(
            status_code=status_code, detail=detail, headers=headers
        )


class InvalidCredentialsException(AuthenticationException):
    """Exception raised when email/password check fails."""

    def __init__(self):
        super().__init__(detail="Invalid email or password")


class InvalidTokenException(AuthenticationException):
    """Exception raised when JWT token is invalid or malformed."""

    def __init__(self, detail: str = "Invalid token"):
        super().__init__(detail=detail)


class ExpiredTokenException(AuthenticationException):
    """Exception raised when JWT token is expired."""

    def __init__(self):
        super().__init__(detail="Expired token")


class InactiveUserException(HTTPException):
    """Exception raised when the authenticated user is marked inactive."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is inactive"
        )


class AuthenticationRequiredException(AuthenticationException):
    """Exception raised when a route requires authentication but none was provided."""

    def __init__(self):
        super().__init__(detail="Authentication required")


class EmailAlreadyRegisteredException(HTTPException):
    """Exception raised when registration email is already taken."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )


class UnauthorizedAccessException(HTTPException):
    """Exception raised when a user attempts to access a resource they do not own."""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class ResumeNotFoundException(HTTPException):
    """Exception raised when a requested resume is not found."""

    def __init__(self, detail: str = "Resume not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class EducationNotFoundException(HTTPException):
    """Exception raised when a requested education record is not found."""

    def __init__(self, detail: str = "Education record not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class WorkExperienceNotFoundException(HTTPException):
    """Exception raised when a requested work experience record is not found."""

    def __init__(self, detail: str = "Work experience record not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class ProjectNotFoundException(HTTPException):
    """Exception raised when a requested project record is not found."""

    def __init__(self, detail: str = "Project record not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class SkillNotFoundException(HTTPException):
    """Exception raised when a requested skill record is not found."""

    def __init__(self, detail: str = "Skill record not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )
