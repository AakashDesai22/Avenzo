"""
AVENZO Backend — Tests for Administrative Account Management CLI
Tests create, password reset, role promotion, validation errors, and secret masking.
"""

import io
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from app.cli.manage_admin import bootstrap_initial_admin, manage_admin
from app.core.security import hash_password, verify_password
from app.models.user import Role, User
from app.services.auth_service import ensure_roles_seeded


@pytest.mark.asyncio
async def test_create_initial_admin_success(db_session):
    """Test creating a new administrator account when one does not exist."""
    email = "initial_superadmin@avenzo.dev"
    password = "SuperSecurePassword123!"

    # Clean up if existed
    res = await db_session.execute(select(User).where(User.email == email))
    existing = res.scalars().first()
    if existing:
        await db_session.delete(existing)
        await db_session.commit()

    inputs = ["AdminFirstName", "AdminLastName"]
    input_func = lambda prompt: inputs.pop(0) if inputs else ""
    getpass_func = lambda prompt: password

    stdout = io.StringIO()
    stderr = io.StringIO()

    success = await manage_admin(
        session=db_session,
        input_func=input_func,
        getpass_func=getpass_func,
        stdout=stdout,
        stderr=stderr,
        email=email,
    )

    assert success is True
    out = stdout.getvalue()
    err = stderr.getvalue()

    assert "Successfully created administrator account" in out
    assert err == ""

    # Verify user in database
    res = await db_session.execute(
        select(User).options(joinedload(User.role)).where(User.email == email)
    )
    user = res.scalars().first()
    assert user is not None
    assert user.email == email
    assert user.first_name == "AdminFirstName"
    assert user.last_name == "AdminLastName"
    assert user.user_type == "business"
    assert user.is_active is True
    assert user.role.name == "ADMIN"
    assert verify_password(password, user.password_hash) is True

    # Ensure secrets not printed
    assert password not in out
    assert password not in err
    assert "$2b$" not in out
    assert "$2b$" not in err


@pytest.mark.asyncio
async def test_reset_existing_admin_password(db_session):
    """Test resetting password of an existing ADMIN account."""
    email = "existing_admin_test@avenzo.dev"
    old_password = "OldAdminPassword123!"
    new_password = "UpdatedAdminPassword456!"

    # Ensure ADMIN role exists
    await ensure_roles_seeded(db_session)
    role_res = await db_session.execute(select(Role).where(Role.name == "ADMIN"))
    admin_role = role_res.scalars().first()

    # Create existing admin
    res = await db_session.execute(select(User).where(User.email == email))
    user = res.scalars().first()
    if not user:
        user = User(
            email=email,
            password_hash=hash_password(old_password),
            first_name="Existing",
            last_name="Admin",
            role_id=admin_role.id,
            user_type="business",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
    else:
        user.password_hash = hash_password(old_password)
        user.role_id = admin_role.id
        await db_session.commit()

    getpass_func = lambda prompt: new_password
    stdout = io.StringIO()
    stderr = io.StringIO()

    success = await manage_admin(
        session=db_session,
        input_func=lambda prompt: "",
        getpass_func=getpass_func,
        stdout=stdout,
        stderr=stderr,
        email=email,
    )

    assert success is True
    out = stdout.getvalue()
    err = stderr.getvalue()

    assert "is an ADMIN. Resetting password." in out
    assert "Successfully reset password for administrator" in out
    assert err == ""

    # Refresh user
    await db_session.refresh(user)
    assert verify_password(new_password, user.password_hash) is True
    assert verify_password(old_password, user.password_hash) is False

    # Ensure secrets not printed
    assert new_password not in out
    assert new_password not in err
    assert "$2b$" not in out
    assert "$2b$" not in err


@pytest.mark.asyncio
async def test_promote_existing_account_with_confirmation(db_session):
    """Test promoting an existing STAFF user to ADMIN after explicit confirmation."""
    email = "staff_to_promote@avenzo.dev"
    old_password = "StaffOriginalPass123!"
    new_password = "PromotedAdminPass789!"

    # Ensure roles seeded
    await ensure_roles_seeded(db_session)
    role_res = await db_session.execute(select(Role).where(Role.name == "STAFF"))
    staff_role = role_res.scalars().first()

    res = await db_session.execute(select(User).where(User.email == email))
    user = res.scalars().first()
    if not user:
        user = User(
            email=email,
            password_hash=hash_password(old_password),
            first_name="Staff",
            last_name="Member",
            role_id=staff_role.id,
            user_type="business",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

    # User confirms promotion with 'y'
    inputs = ["y"]
    input_func = lambda prompt: inputs.pop(0) if inputs else ""
    getpass_func = lambda prompt: new_password

    stdout = io.StringIO()
    stderr = io.StringIO()

    success = await manage_admin(
        session=db_session,
        input_func=input_func,
        getpass_func=getpass_func,
        stdout=stdout,
        stderr=stderr,
        email=email,
    )

    assert success is True
    out = stdout.getvalue()
    err = stderr.getvalue()

    assert "currently has role 'STAFF'" in out
    assert "Confirm promoting account 'staff_to_promote@avenzo.dev' to ADMIN" in out
    assert "Successfully promoted account" in out
    assert err == ""

    res = await db_session.execute(
        select(User).options(joinedload(User.role)).where(User.email == email)
    )
    updated_user = res.scalars().first()
    assert updated_user.role.name == "ADMIN"
    assert updated_user.user_type == "business"
    assert verify_password(new_password, updated_user.password_hash) is True


@pytest.mark.asyncio
async def test_promote_existing_account_declined_confirmation(db_session):
    """Test that declining promotion leaves role and password unchanged."""
    email = "staff_decline_promo@avenzo.dev"
    original_password = "StaffOriginalPass123!"

    await ensure_roles_seeded(db_session)
    role_res = await db_session.execute(select(Role).where(Role.name == "STAFF"))
    staff_role = role_res.scalars().first()

    res = await db_session.execute(select(User).where(User.email == email))
    user = res.scalars().first()
    if not user:
        user = User(
            email=email,
            password_hash=hash_password(original_password),
            first_name="Staff",
            last_name="Decline",
            role_id=staff_role.id,
            user_type="business",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

    # User declines promotion with 'n'
    inputs = ["n"]
    input_func = lambda prompt: inputs.pop(0) if inputs else ""
    getpass_func = lambda prompt: "ShouldNotBeUsed123!"

    stdout = io.StringIO()
    stderr = io.StringIO()

    success = await manage_admin(
        session=db_session,
        input_func=input_func,
        getpass_func=getpass_func,
        stdout=stdout,
        stderr=stderr,
        email=email,
    )

    assert success is False
    out = stdout.getvalue()
    err = stderr.getvalue()

    assert "Promotion cancelled. Account 'staff_decline_promo@avenzo.dev' was not modified." in out
    assert err == ""

    res = await db_session.execute(
        select(User).options(joinedload(User.role)).where(User.email == email)
    )
    unchanged_user = res.scalars().first()
    assert unchanged_user.role.name == "STAFF"
    assert verify_password(original_password, unchanged_user.password_hash) is True


@pytest.mark.asyncio
async def test_password_mismatch(db_session):
    """Test error when password and password confirmation do not match."""
    email = "mismatch_test@avenzo.dev"
    passwords = ["FirstPassword123!", "DifferentPassword123!"]
    getpass_func = lambda prompt: passwords.pop(0)

    stdout = io.StringIO()
    stderr = io.StringIO()

    success = await manage_admin(
        session=db_session,
        input_func=lambda prompt: "",
        getpass_func=getpass_func,
        stdout=stdout,
        stderr=stderr,
        email=email,
    )

    assert success is False
    err = stderr.getvalue()
    assert "Error: Passwords do not match." in err


@pytest.mark.asyncio
async def test_insufficient_password_length(db_session):
    """Test error when password length is under the 8 character requirement."""
    email = "short_pass@avenzo.dev"
    short_pass = "short1"
    getpass_func = lambda prompt: short_pass

    stdout = io.StringIO()
    stderr = io.StringIO()

    success = await manage_admin(
        session=db_session,
        input_func=lambda prompt: "",
        getpass_func=getpass_func,
        stdout=stdout,
        stderr=stderr,
        email=email,
    )

    assert success is False
    err = stderr.getvalue()
    assert "Error: Password must be at least 8 characters long." in err


@pytest.mark.asyncio
async def test_missing_admin_role(db_session):
    """Test failure when ADMIN role is absent from database."""
    email = "no_admin_role@avenzo.dev"

    # Remove users referencing ADMIN role, then remove ADMIN role
    role_res = await db_session.execute(select(Role).where(Role.name == "ADMIN"))
    admin_role = role_res.scalars().first()
    if admin_role:
        await db_session.execute(delete(User).where(User.role_id == admin_role.id))
        await db_session.execute(delete(Role).where(Role.id == admin_role.id))
        await db_session.commit()

    stdout = io.StringIO()
    stderr = io.StringIO()

    success = await manage_admin(
        session=db_session,
        input_func=lambda prompt: "",
        getpass_func=lambda prompt: "ValidPassword123!",
        stdout=stdout,
        stderr=stderr,
        email=email,
        seed_roles=False,
    )

    assert success is False
    err = stderr.getvalue()
    assert "Error: ADMIN role not found in database." in err

    # Restore default roles for subsequent tests
    await ensure_roles_seeded(db_session)


@pytest.mark.asyncio
async def test_database_failure_rollback(db_session):
    """Test that database commit errors trigger rollback and safe error reporting."""
    email = "db_fail_test@avenzo.dev"
    await ensure_roles_seeded(db_session)

    # Ensure user does not already exist
    res = await db_session.execute(select(User).where(User.email == email))
    existing = res.scalars().first()
    if existing:
        await db_session.delete(existing)
        await db_session.commit()

    with (
        patch.object(db_session, "commit", side_effect=SQLAlchemyError("Connection closed")),
        patch.object(db_session, "rollback", new_callable=AsyncMock) as mock_rollback,
    ):
        stdout = io.StringIO()
        stderr = io.StringIO()

        success = await manage_admin(
            session=db_session,
            input_func=lambda prompt: "Admin",
            getpass_func=lambda prompt: "ValidPass123!",
            stdout=stdout,
            stderr=stderr,
            email=email,
            seed_roles=False,
        )

        assert success is False
        err = stderr.getvalue()
        assert "Error: Database transaction failed" in err
        mock_rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_invalid_email_format(db_session):
    """Test validation failure on invalid email format."""
    stdout = io.StringIO()
    stderr = io.StringIO()

    success = await manage_admin(
        session=db_session,
        input_func=lambda prompt: "",
        getpass_func=lambda prompt: "ValidPass123!",
        stdout=stdout,
        stderr=stderr,
        email="not-an-email",
    )

    assert success is False
    err = stderr.getvalue()
    assert "Error: Invalid email format" in err


@pytest.mark.asyncio
async def test_secrets_never_printed(db_session):
    """Explicitly verify that plaintext passwords and bcrypt hashes are never leaked to stdout or stderr."""
    email = "secret_leak_test@avenzo.dev"
    secret_pass = "SuperSecret_NeverPrintMe_999!"

    # Clean up if existed
    res = await db_session.execute(select(User).where(User.email == email))
    existing = res.scalars().first()
    if existing:
        await db_session.delete(existing)
        await db_session.commit()

    stdout = io.StringIO()
    stderr = io.StringIO()

    success = await manage_admin(
        session=db_session,
        input_func=lambda prompt: "TestUser",
        getpass_func=lambda prompt: secret_pass,
        stdout=stdout,
        stderr=stderr,
        email=email,
    )

    assert success is True
    out = stdout.getvalue()
    err = stderr.getvalue()

    assert secret_pass not in out
    assert secret_pass not in err
    assert "$2b$" not in out
    assert "$2b$" not in err


@pytest.mark.asyncio
async def test_bootstrap_initial_admin_success(db_session):
    """Test explicit one-time bootstrap command creating admin@avenzo.dev."""
    email = "admin@avenzo.dev"
    password = "CollegeAdminPass2026!"

    res = await db_session.execute(select(User).where(User.email == email))
    existing = res.scalars().first()
    if existing:
        await db_session.delete(existing)
        await db_session.commit()

    stdout = io.StringIO()
    stderr = io.StringIO()

    success = await bootstrap_initial_admin(
        session=db_session,
        email=email,
        password=password,
        stdout=stdout,
        stderr=stderr,
    )

    assert success is True
    out = stdout.getvalue()
    err = stderr.getvalue()

    assert "Successfully bootstrapped initial administrator" in out
    assert err == ""

    # Verify user in database
    res = await db_session.execute(
        select(User).options(joinedload(User.role)).where(User.email == email)
    )
    user = res.scalars().first()
    assert user is not None
    assert user.email == email
    assert user.role.name == "ADMIN"
    assert user.user_type == "business"
    assert user.is_active is True
    assert verify_password(password, user.password_hash) is True


@pytest.mark.asyncio
async def test_bootstrap_initial_admin_from_env(db_session):
    """Test bootstrap reading password from INITIAL_ADMIN_PASSWORD environment variable."""
    email = "admin@avenzo.dev"
    env_password = "EnvPasswordSecret2026!"

    res = await db_session.execute(select(User).where(User.email == email))
    existing = res.scalars().first()
    if existing:
        await db_session.delete(existing)
        await db_session.commit()

    stdout = io.StringIO()
    stderr = io.StringIO()

    with patch.dict("os.environ", {"INITIAL_ADMIN_PASSWORD": env_password}):
        success = await bootstrap_initial_admin(
            session=db_session,
            email=email,
            stdout=stdout,
            stderr=stderr,
        )

    assert success is True
    res = await db_session.execute(select(User).where(User.email == email))
    user = res.scalars().first()
    assert user is not None
    assert verify_password(env_password, user.password_hash) is True


@pytest.mark.asyncio
async def test_bootstrap_duplicate_account_protection(db_session):
    """Test that bootstrap never resets password or promotes an existing account silently."""
    email = "admin@avenzo.dev"
    original_password = "OriginalUntouchedPass123!"
    new_attempt_password = "AttemptedResetPass999!"

    await ensure_roles_seeded(db_session)
    role_res = await db_session.execute(select(Role).where(Role.name == "ADMIN"))
    admin_role = role_res.scalars().first()

    res = await db_session.execute(select(User).where(User.email == email))
    user = res.scalars().first()
    if not user:
        user = User(
            email=email,
            password_hash=hash_password(original_password),
            first_name="Existing",
            last_name="Admin",
            role_id=admin_role.id,
            user_type="business",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
    else:
        user.password_hash = hash_password(original_password)
        await db_session.commit()

    stdout = io.StringIO()
    stderr = io.StringIO()

    # Attempt to run bootstrap on existing account
    success = await bootstrap_initial_admin(
        session=db_session,
        email=email,
        password=new_attempt_password,
        stdout=stdout,
        stderr=stderr,
    )

    assert success is False
    out = stdout.getvalue()
    err = stderr.getvalue()

    assert "already exists" in out
    assert "Initial bootstrap aborted without modifying existing account" in out
    assert err == ""

    # Verify password was NOT changed / overwritten
    await db_session.refresh(user)
    assert verify_password(original_password, user.password_hash) is True
    assert verify_password(new_attempt_password, user.password_hash) is False


@pytest.mark.asyncio
async def test_bootstrap_password_validation(db_session):
    """Test password length and missing password validations in bootstrap."""
    email = "admin_valid_test@avenzo.dev"

    stdout = io.StringIO()
    stderr = io.StringIO()

    # Too short password
    success = await bootstrap_initial_admin(
        session=db_session,
        email=email,
        password="short",
        stdout=stdout,
        stderr=stderr,
    )
    assert success is False
    assert "must be at least 8 characters" in stderr.getvalue()

    # Missing password in non-interactive environment
    stdout = io.StringIO()
    stderr = io.StringIO()
    with patch("sys.stdin.isatty", return_value=False), patch.dict("os.environ", {}, clear=True):
        success = await bootstrap_initial_admin(
            session=db_session,
            email=email,
            password=None,
            stdout=stdout,
            stderr=stderr,
        )
    assert success is False
    assert "must be supplied via INITIAL_ADMIN_PASSWORD" in stderr.getvalue()


@pytest.mark.asyncio
async def test_bootstrap_secrets_never_printed(db_session):
    """Ensure bootstrap never leaks plain password or password hash to stdout/stderr."""
    email = "leak_check_bootstrap@avenzo.dev"
    secret = "TopSecretBootstrapPassword999!"

    res = await db_session.execute(select(User).where(User.email == email))
    existing = res.scalars().first()
    if existing:
        await db_session.delete(existing)
        await db_session.commit()

    stdout = io.StringIO()
    stderr = io.StringIO()

    success = await bootstrap_initial_admin(
        session=db_session,
        email=email,
        password=secret,
        stdout=stdout,
        stderr=stderr,
    )

    assert success is True
    out = stdout.getvalue()
    err = stderr.getvalue()

    assert secret not in out
    assert secret not in err
    assert "$2b$" not in out
    assert "$2b$" not in err

