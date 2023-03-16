"""Constants for WienerNetze."""
from typing import Final
import re

API_GATEWAY_TOKEN_REGEX = re.compile(
    r"b2cApiKey\:\s*\"([A-Za-z0-9\-_]+)\"", re.IGNORECASE
)

PAGE_URL = "https://smartmeter-web.wienernetze.at/"
API_URL = "https://api.wstw.at/gateway/WN_SMART_METER_PORTAL_API_B2C/1.0/"
REDIRECT_URI = "https://smartmeter-web.wienernetze.at/"
API_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"
AUTH_URL = "https://log.wien/auth/realms/logwien/protocol/openid-connect/"


LOGIN_ARGS = {
    "client_id": "wn-smartmeter",
    "redirect_uri": REDIRECT_URI,
    "response_mode": "fragment",
    "response_type": "code",
    "scope": "openid",
    "nonce": "",
}

API_TIMEOUT = 30


def build_access_token_args(**kwargs):
    """Build access token and add kwargs."""
    args = {
        "grant_type": "authorization_code",
        "client_id": "wn-smartmeter",
        "redirect_uri": REDIRECT_URI,
    }
    args.update(**kwargs)
    return args


# config
DOMAIN = "wn_smartmeter"
NAME = "WN Smartmeter"
TIMEZONE = "Europe/Vienna"
DEFAULT_SCAN_INTERVAL: Final = 60
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_METER_READER: Final = "meter_reader"
CONF_SCAN_INTERVAL: Final = "scan_interval"

ATTR_METER_READER: Final = "MeterReader"
ATTR_CONSUMPTION_YESTERDAY: Final = "ConsumptionYesterday"
ATTR_CONSUMPTION_DAY_BEFORE_YESTERDAY: Final = "ConsumptionDayBeforeYesterday"
