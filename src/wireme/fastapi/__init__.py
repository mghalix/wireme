"""FastAPI integration for Wireme."""

from wireme.fastapi._dependencies import FromWeb
from wireme.fastapi._overrides import override_web_dependency

__all__ = (
    "FromWeb",
    "override_web_dependency",
)
