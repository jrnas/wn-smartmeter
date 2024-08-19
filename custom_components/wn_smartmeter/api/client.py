"""WienerNetze API that provides data from the SmartMeter API."""
import logging
from urllib import parse
from datetime import timedelta
from datetime import datetime
from aiohttp import hdrs
from lxml import html
from homeassistant.helpers.aiohttp_client import (
    async_create_clientsession,
)
from homeassistant.core import HomeAssistant
import aiohttp
from ..const import (
    AUTH_URL,
    LOGIN_ARGS,
    API_DATE_FORMAT,
    API_URL,
    API_TIMEOUT,
    API_CONFIG_URL,
    build_access_token_args,
)

_LOGGER = logging.getLogger(__name__)
timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)


class WienerNetzeAPI:
    """WienerNetze API Client."""

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        meter_reader: str = "",
    ) -> None:
        """Access the Smartmeter API."""
        self.hass = hass
        self.username = username
        self.password = password
        self.meter_reader = meter_reader
        self.session = None
        self.lastlogin = None
        self._access_token = None
        self._refresh_token = None
        self._api_gateway_token = None

    async def _get_login_url(self) -> str:
        """Get login url."""
        login_url = AUTH_URL + "auth?" + parse.urlencode(LOGIN_ARGS)

        async with self.session.get(url=login_url, timeout=timeout) as resp:
            status_code = int(resp.status)
            body = await resp.text()

            if status_code != 200:
                raise ConnectionError(
                    f"Could not load login page. Error: status:{status_code} body:{body}"
                ) from Exception

            tree = html.fromstring(body)
            loginurl = tree.xpath("(//form/@action)")

            return loginurl[0]

    async def _set_tokens(self, code: str):
        """Get tokens."""
        async with self.session.post(
            url=AUTH_URL + "token",
            data=build_access_token_args(code=code),
            allow_redirects=False,
            timeout=timeout,
        ) as resp:
            json = await resp.json()
            self._access_token = json["access_token"]
            self._refresh_token = json["refresh_token"]
            self._api_gateway_token = await self._get_api_key(self._access_token)

    async def login(self) -> bool:
        """login."""
        _LOGGER.debug("login()")
        self.session = async_create_clientsession(self.hass, verify_ssl=False)
        self.lastlogin = datetime.now()
        login_url = await self._get_login_url()

        if login_url is not None:
            data = {
                "username": self.username,
                "password": self.password,
            }
            async with self.session.post(
                url=login_url, data=data, allow_redirects=False, timeout=timeout
            ) as resp:
                headers = resp.headers

            if "Location" not in headers:
                return False
            location = headers[hdrs.LOCATION]
            parsed_url = parse.urlparse(location)
            params = parse.parse_qs(parsed_url.query)
            fragment_dict = dict(
                [
                    x.split("=")
                    for x in parsed_url.fragment.split("&")
                    if len(x.split("=")) == 2
                ]
            )
            if "code" in fragment_dict:
                code = fragment_dict["code"]
            elif "code" in params and len(params["code"]) > 0:
                code = params["code"][0]
            else:
                return False

            await self._set_tokens(code)
            return True

    async def _get_api_key(self, token) -> str:
        """Get api key."""
        headers = {"Authorization": f"Bearer {token}"}
        async with self.session.get(
            url=API_CONFIG_URL, headers=headers
        ) as resp:
            body = await resp.json()

        return body["b2cApiKey"]

    async def _call_api(
        self,
        endpoint,
        base_url=None,
        query=None,
        method="GET",
        data=None,
        timeout=60.0
    ):
        """Call api."""
        if base_url is None:
            base_url = API_URL
        url = f"{base_url}{endpoint}"
        if query:
            url += ("?" if "?" not in endpoint else "&") + parse.urlencode(query)
        _LOGGER.debug(url)

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "X-Gateway-APIKey": self._api_gateway_token,
        }

        async with self.session.request(method, url, headers=headers, json=data, timeout=timeout) as resp:
            return await resp.json()

    def _dt_string(self, datetime_string):
        return datetime_string.strftime(API_DATE_FORMAT)[:-3] + "Z"

    async def get_meter_reader(self):
        """Get meter reader from the smartmeter api."""
        _LOGGER.debug("get_meter_reader")
        return await self._call_api("zaehlpunkt/meterReadings")

    async def get_meter_readers(self):
        """Get a list of meter readers from the smartmeter api."""
        _LOGGER.debug("get_meter_readers")
        return await self._call_api("zaehlpunkte")

    async def get_consumption(self, meter_reader: str, customer_id: str):
        """Get verbrauchRaw data from the smartmeter api."""
        _LOGGER.debug("get_consumption")
        endpoint = f"messdaten/{customer_id}/{meter_reader}/verbrauch"
        date_from = datetime.today() - timedelta(days=4)
        date_to = datetime.now()
        query = {
            "dateFrom": self._dt_string(
                date_from.replace(hour=23, minute=00, second=0, microsecond=0)
            ),
            "dateTo": self._dt_string(date_to),
            "granularity": "DAY",
            "dayViewResolution": "HOUR"
        }
        return await self._call_api(endpoint=endpoint, query=query)

    async def get_consumptions(self):
        """Get consumptions data from the smartmeter api."""
        _LOGGER.debug("get_consumptions")
        endpoint = "zaehlpunkt/consumptions"
        return await self._call_api(endpoint=endpoint)

    async def set_default_meterreader(self, meter_reader: str, customer_id: str):
        """Set default meterreader."""
        _LOGGER.debug("set_default_meterreader")
        endpoint = f"kundennummer/{customer_id}/zaehlpunkt/default"
        data = {
            "zaehlpunktNummer": meter_reader
        }
        return await self._call_api(endpoint=endpoint, data=data, method="PUT")