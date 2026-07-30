from app.exceptions.auth import AuthenticationException


class PasswordPolicyService:
    @staticmethod
    def validate_password(password: str) -> None:
        if not password or len(password) < 8:
            raise AuthenticationException("Password must be at least 8 characters long.")
        if not any(c.isupper() for c in password):
            raise AuthenticationException("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in password):
            raise AuthenticationException("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in password):
            raise AuthenticationException("Password must contain at least one digit.")
        special_chars = set("!@#$%^&*()_+-=[]{}|;:,.<>?")
        if not any(c in special_chars for c in password):
            raise AuthenticationException("Password must contain at least one special character.")
