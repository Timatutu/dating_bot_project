from dataclasses import dataclass


@dataclass
class Customer:
    id: int | None
    first_name: str
    last_name: str
    email: str

    def change_email(self, new_email: str) -> None:
        new_email = new_email.strip().lower()
        if "@" not in new_email or "." not in new_email:
            raise ValueError("invalid email")
        self.email = new_email
