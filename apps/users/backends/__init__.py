# apps/users/backends/__init__.py
from .auth_backends import EmailOrUsernameModelBackend

__all__ = ['EmailOrUsernameModelBackend']
