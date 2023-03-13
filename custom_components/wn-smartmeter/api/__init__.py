"""Unofficial Python wrapper for the Wiener Netze Smart Meter private API."""
try:
    from importlib.metadata import version
except ModuleNotFoundError:
    from importlib_metadata import version

from .client import WienerNetzeAPI

try:
    __version__ = version(__name__)
except Exception:  # pylint: disable=broad-except
    pass

__all__ = ["WienerNetzeAPI"]
