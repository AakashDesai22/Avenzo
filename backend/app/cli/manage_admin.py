"""
AVENZO Backend — Administrative Account Management CLI
Safely creates an initial ADMIN account or resets/promotes an existing account
without exposing passwords or password hashes.
"""

import asyncio
import getpass
import os
import sys
from collections.abc import Callable

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import Role, User
from app.services.auth_service import ensure_roles_seeded

MIN_PASSWORD_LENGTH = 8


async def bootstrap_initial_admin(
    session: AsyncSession,
    email: str | None = None,
    password: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    stdout=sys.stdout,
    stderr=sys.stderr,
) -> bool:
    """
    Explicit one-time bootstrap command that creates the initial ADMIN only
    when the account does not already exist.

    If the account already exists, it does NOT reset its password or promote it silently.
    """
    # 1. Resolve and validate target email (defaults to configured INITIAL_ADMIN_EMAIL)
    raw_email = (
        email
        or settings.INITIAL_ADMIN_EMAIL
        or os.getenv("INITIAL_ADMIN_EMAIL")
        or os.getenv("ADMIN_EMAIL")
        or "admin@avenzo.dev"
    ).strip()

    email_adapter = TypeAdapter(EmailStr)
    try:
        normalized_email = str(email_adapter.validate_python(raw_email)).strip().lower()
    except ValidationError:
        print(f"Error: Invalid admin email format '{raw_email}'.", file=stderr)
        return False

    # 2. Seed and verify system roles
    try:
        await ensure_roles_seeded(session)
    except Exception as exc:  # noqa: BLE001
        await session.rollback()
        print(f"Error: Failed to seed system roles: {exc.__class__.__name__}", file=stderr)
        return False

    admin_role_result = await session.execute(select(Role).where(Role.name == "ADMIN"))
    admin_role = admin_role_result.scalars().first()
    if not admin_role:
        print("Error: ADMIN role not found in database.", file=stderr)
        return False

    # 3. Check if user already exists — strict duplicate-account protection
    user_result = await session.execute(
        select(User).options(joinedload(User.role)).where(User.email == normalized_email)
    )
    existing_user = user_result.scalars().first()

    if existing_user:
        current_role = existing_user.role.name if existing_user.role else "UNKNOWN"
        print(
            f"Notice: Account '{normalized_email}' already exists (role: {current_role}). "
            "Initial bootstrap aborted without modifying existing account.",
            file=stdout,
        )
        return False

    # 4. Resolve password from parameter, environment, or interactive input
    resolved_password = (
        password
        or settings.INITIAL_ADMIN_PASSWORD
        or os.getenv("INITIAL_ADMIN_PASSWORD")
        or os.getenv("ADMIN_PASSWORD")
    )

    if not resolved_password:
        if sys.stdin.isatty():
            try:
                p1 = getpass.getpass(f"Enter initial admin password for '{normalized_email}': ")
                p2 = getpass.getpass("Confirm initial admin password: ")
                if p1 != p2:
                    print("Error: Passwords do not match.", file=stderr)
                    return False
                resolved_password = p1
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled by user.", file=stderr)
                return False
        else:
            print(
                "Error: Initial admin password must be supplied via INITIAL_ADMIN_PASSWORD environment "
                "variable or interactive prompt.",
                file=stderr,
            )
            return False

    if len(resolved_password) < MIN_PASSWORD_LENGTH:
        print(
            f"Error: Initial admin password must be at least {MIN_PASSWORD_LENGTH} characters long.",
            file=stderr,
        )
        return False

    # 5. Create the initial administrator in a safe transaction
    try:
        fn = first_name or settings.INITIAL_ADMIN_FIRST_NAME or "Admin"
        ln = last_name or settings.INITIAL_ADMIN_LAST_NAME or "User"
        new_password_hash = hash_password(resolved_password)

        new_admin = User(
            email=normalized_email,
            password_hash=new_password_hash,
            first_name=fn,
            last_name=ln,
            role_id=admin_role.id,
            user_type="business",
            is_active=True,
        )
        session.add(new_admin)
        await session.commit()
        print(
            f"Success: Successfully bootstrapped initial administrator '{normalized_email}'.",
            file=stdout,
        )
        return True

    except SQLAlchemyError as exc:
        await session.rollback()
        print(f"Error: Database transaction failed: {exc.__class__.__name__}", file=stderr)
        return False
    except Exception as exc:  # noqa: BLE001
        await session.rollback()
        print(f"Error: An unexpected error occurred: {exc.__class__.__name__}", file=stderr)
        return False


async def manage_admin(
    session: AsyncSession,
    input_func: Callable[[str], str] = input,
    getpass_func: Callable[[str], str] = getpass.getpass,
    stdout=sys.stdout,
    stderr=sys.stderr,
    email: str | None = None,
    seed_roles: bool = True,
) -> bool:
    """
    Safely creates or resets an administrator account.

    Args:
        session: Active SQLAlchemy AsyncSession.
        input_func: Callable for reading general interactive input.
        getpass_func: Callable for reading masked password input.
        stdout: Output stream for informational messages.
        stderr: Output stream for error messages.
        email: Optional pre-supplied email; if None, prompts interactively.
        seed_roles: Whether to ensure default system roles are seeded.

    Returns:
        bool: True if operation succeeded, False otherwise.
    """
    # 1. Obtain and validate target email
    if email is None:
        try:
            email = input_func("Enter admin email address: ")
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled by user.", file=stderr)
            return False

    raw_email = (email or "").strip()
    if not raw_email:
        print("Error: Email address is required.", file=stderr)
        return False

    email_adapter = TypeAdapter(EmailStr)
    try:
        normalized_email = str(email_adapter.validate_python(raw_email)).strip().lower()
    except ValidationError:
        print(f"Error: Invalid email format '{raw_email}'.", file=stderr)
        return False

    # 2. Seed and verify system roles
    if seed_roles:
        try:
            await ensure_roles_seeded(session)
        except Exception as exc:  # noqa: BLE001
            await session.rollback()
            print(f"Error: Failed to seed system roles: {exc.__class__.__name__}", file=stderr)
            return False

    admin_role_result = await session.execute(select(Role).where(Role.name == "ADMIN"))
    admin_role = admin_role_result.scalars().first()
    if not admin_role:
        print("Error: ADMIN role not found in database.", file=stderr)
        return False

    # 3. Check for existing user
    user_result = await session.execute(
        select(User).options(joinedload(User.role)).where(User.email == normalized_email)
    )
    user = user_result.scalars().first()

    is_new_user = user is None
    first_name = "Admin"
    last_name = "User"
    current_role_name = ""

    if is_new_user:
        print(f"Creating initial administrator account for '{normalized_email}'.", file=stdout)
        try:
            fn_in = input_func("Enter first name [Admin]: ").strip()
            if fn_in:
                first_name = fn_in
            ln_in = input_func("Enter last name [User]: ").strip()
            if ln_in:
                last_name = ln_in
        except (EOFError, KeyboardInterrupt):
            print("\nOperation cancelled by user.", file=stderr)
            return False
    else:
        if user.role:
            current_role_name = user.role.name
        else:
            role_lookup = await session.execute(select(Role).where(Role.id == user.role_id))
            role_obj = role_lookup.scalars().first()
            current_role_name = role_obj.name if role_obj else "UNKNOWN"

        if current_role_name != "ADMIN":
            print(
                f"Existing account found: '{user.email}' currently has role '{current_role_name}'.",
                file=stdout,
            )
            print(
                f"Confirm promoting account '{user.email}' to ADMIN? [y/N]",
                file=stdout,
            )
            try:
                confirm = input_func("Confirm [y/N]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nOperation cancelled by user.", file=stderr)
                return False

            if confirm not in ("y", "yes"):
                print(
                    f"Promotion cancelled. Account '{user.email}' was not modified.",
                    file=stdout,
                )
                return False
        else:
            print(
                f"Existing account found: '{user.email}' is an ADMIN. Resetting password.",
                file=stdout,
            )

    # 4. Interactive password entry with masking and confirmation
    try:
        password = getpass_func("Enter new password: ")
        password_confirm = getpass_func("Confirm new password: ")
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled by user.", file=stderr)
        return False

    if password != password_confirm:
        print("Error: Passwords do not match.", file=stderr)
        return False

    if len(password) < MIN_PASSWORD_LENGTH:
        print(
            f"Error: Password must be at least {MIN_PASSWORD_LENGTH} characters long.",
            file=stderr,
        )
        return False

    # 5. Execute database transaction
    try:
        new_password_hash = hash_password(password)

        if is_new_user:
            new_admin = User(
                email=normalized_email,
                password_hash=new_password_hash,
                first_name=first_name,
                last_name=last_name,
                role_id=admin_role.id,
                user_type="business",
                is_active=True,
            )
            session.add(new_admin)
            await session.commit()
            print(
                f"Success: Successfully created administrator account for '{normalized_email}'.",
                file=stdout,
            )
        else:
            user.password_hash = new_password_hash
            user.role = admin_role
            user.role_id = admin_role.id
            user.user_type = "business"
            user.is_active = True
            if getattr(user, "is_deleted", False):
                user.is_deleted = False
                user.deleted_at = None
                user.deleted_by = None

            await session.commit()
            if current_role_name == "ADMIN":
                print(
                    f"Success: Successfully reset password for administrator '{user.email}'.",
                    file=stdout,
                )
            else:
                print(
                    f"Success: Successfully promoted account '{user.email}' to ADMIN and updated password.",
                    file=stdout,
                )

        return True

    except SQLAlchemyError as exc:
        await session.rollback()
        print(f"Error: Database transaction failed: {exc.__class__.__name__}", file=stderr)
        return False
    except Exception as exc:  # noqa: BLE001
        await session.rollback()
        print(f"Error: An unexpected error occurred: {exc.__class__.__name__}", file=stderr)
        return False


async def main() -> None:
    """Main CLI entrypoint for managing administrative accounts."""
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "bootstrap"
    async with AsyncSessionLocal() as session:
        if command in ("interactive", "--interactive", "manage", "--manage"):
            success = await manage_admin(session)
        else:
            # Defaults to explicit one-time bootstrap
            success = await bootstrap_initial_admin(session)
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
