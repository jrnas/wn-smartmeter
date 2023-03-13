"""Unofficial Python wrapper for the Wiener Netze Smart Meter private API."""
try:
    from importlib.metadata import version
except ModuleNotFoundError:
    from importlib_metadata import version


from contextlib import suppress

from .client import WienerNetzeAPI

with suppress(Exception):
    __version__ = version(__name__)

__all__ = ["WienerNetzeAPI"]
