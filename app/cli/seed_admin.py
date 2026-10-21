
from getpass import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


def main() -> None:
    full_name = input("Admin full name: ").strip()
    email = input("Admin email: ").strip().lower()
    password = getpass("Admin password (minimum 12 characters): ")
    confirmation = getpass("Confirm admin password: ")

    if len(full_name) < 2:
        raise SystemExit("Full name must contain at least 2 characters.")

    if len(password) < 12 or len(password) > 128:
        raise SystemExit("Password must contain 12 to 128 characters.")

    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    if "@" not in email or len(email) > 320:
        raise SystemExit("Enter a valid email address.")

    with SessionLocal() as db:
        existing = db.scalar(
            select(User).where(User.email == email)
        )

        if existing is not None:
            if existing.role == "admin":
                print("An admin account with this email already exists.")
                return

            raise SystemExit(
                "This email already belongs to a non-admin account. "
                "No changes were made."
            )

        admin = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )

        db.add(admin)
        db.commit()

    print("Admin account created successfully.")


if __name__ == "__main__":
    main()
