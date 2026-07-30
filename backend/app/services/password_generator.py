import secrets
import string


class PasswordGeneratorService:
    @staticmethod
    def generate_temp_password(length: int = 10) -> str:
        if length < 8:
            length = 8

        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special = "!@#$%^&*"

        # Guarantee at least one character from each set
        password = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(special),
        ]

        all_chars = uppercase + lowercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))

        secrets.SystemRandom().shuffle(password)
        return "".join(password)
