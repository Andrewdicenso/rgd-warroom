"""Presentation Components Module."""
from .auth_forms import (
    render_login_form,
    render_registration_form,
    render_password_recovery_form,
    render_login_tabs
)

__all__ = [
    "render_login_form",
    "render_registration_form",
    "render_password_recovery_form",
    "render_login_tabs"
]
