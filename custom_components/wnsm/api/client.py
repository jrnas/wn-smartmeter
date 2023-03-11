"""WienerNetze API that provides data from the SmartMeter API"""
from ..const import (
    AUTH_URL,
    LOGIN_ARGS,
    PAGE_URL,
    API_GATEWAY_TOKEN_REGEX,
    API_DATE_FORMAT,
    API_URL,
    API_TIMEOUT,
    build_access_token_args,
)
from urllib import parse
import logging
import aiohttp
from aiohttp import hdrs
from lxml import html
from datetime import datetime
from homeassistant.helpers.aiohttp_client import (
    async_create_clientsession,
)
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)
timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)


class WienerNetzeAPI:
    """WienerNetze API Client."""

    def __init__(
        self,
        hass: HomeAssistant,
        username: str,
        password: str,
        zaehlerpunkt: str,
    ) -> None:
        """Access the Smartmeter API."""
        self.hass = hass
        self.username = username
        self.password = password
        self.zaehlerpunkt = zaehlerpunkt
        self.session = None
        self.lastlogin = None
        self._access_token = None
        self._refresh_token = None
        self._api_gateway_token = None

    async def _get_login_url(self) -> str:
        """get login url"""
        _LOGGER.debug("_get_login_url()")
        login_url = AUTH_URL + "auth?" + parse.urlencode(LOGIN_ARGS)
        _LOGGER.debug(login_url)
        _LOGGER.debug("request cookies:")
        for cookie in self.session.cookie_jar:
            _LOGGER.debug("%s=%s", cookie.key, cookie["domain"])

        async with self.session.get(url=login_url, timeout=timeout) as resp:
            status_code = int(resp.status)
            headers = resp.headers
            body = await resp.text()
            _LOGGER.debug("response status: %s", resp.status)
            _LOGGER.debug("response headers:")
            _LOGGER.debug(headers)
            _LOGGER.debug("response cookies:")
            for cookie in self.session.cookie_jar:
                _LOGGER.debug("%s=%s", cookie.key, cookie["domain"])

            if status_code != 200:
                raise ConnectionError(
                    f"Could not load login page. Error: status:{status_code} body:{body}"
                ) from Exception

            tree = html.fromstring(body)
            loginurl = tree.xpath("(//form/@action)")

            return loginurl[0]

    async def _set_tokens(self, code: str):
        """get tokens"""
        _LOGGER.debug("_set_tokens()")
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
        """login"""
        _LOGGER.debug("login()")
        self.session = async_create_clientsession(self.hass, verify_ssl=False)
        self.lastlogin = datetime.now()
        login_url = await self._get_login_url()

        if login_url is not None:
            _LOGGER.debug("login_url: %s", login_url)
            _LOGGER.debug("request cookies:")
            for cookie in self.session.cookie_jar:
                _LOGGER.debug("%s=%s", cookie.key, cookie["domain"])

            data = {
                "username": self.username,
                "password": self.password,
            }
            async with self.session.post(
                url=login_url, data=data, allow_redirects=False, timeout=timeout
            ) as resp:
                headers = resp.headers
                _LOGGER.debug("response status: %s", resp.status)
                _LOGGER.debug("response headers:")
                _LOGGER.debug(headers)
                _LOGGER.debug("response cookies:")
                for cookie in self.session.cookie_jar:
                    _LOGGER.debug("%s=%s", cookie.key, cookie["domain"])

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
        """get api key"""
        _LOGGER.debug("_get_api_key()")
        headers = {"Authorization": f"Bearer {token}"}
        async with self.session.post(
            url=PAGE_URL, headers=headers, allow_redirects=False, timeout=timeout
        ) as resp:
            body = await resp.text()

        tree = html.fromstring(body)
        scripts = tree.xpath("(//script/@src)")
        for script in scripts:
            try:
                async with self.session.get(url=PAGE_URL + script) as resp:
                    body = await resp.text()
            except Exception:
                raise ConnectionError(
                    "Could not obtain API key from scripts"
                ) from Exception
            for match in API_GATEWAY_TOKEN_REGEX.findall(body):
                _LOGGER.debug("found api key: %s", match)
                return match

    async def _call_api(
        self,
        endpoint,
        base_url=None,
        query=None,
    ):
        """call api"""
        _LOGGER.debug("_call_api()")
        await self.login()

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

        async with self.session.get(url, headers=headers) as resp:
            json = await resp.json()
            return json

    def _dt_string(self, datetime_string):
        return datetime_string.strftime(API_DATE_FORMAT)[:-3] + "Z"

    async def get_zaehlerstand(self):
        """getting zaehlerstand from the smartmeter api"""
        _LOGGER.debug("get_zaehlerstand")
        return await self._call_api("zaehlpunkt/meterReadings")

    async def get_consumption(self):
        """getting zaehlpunkt consumptions data from the smartmeter api"""
        _LOGGER.debug("get_consumption")
        endpoint = "zaehlpunkt/consumptions"
        return await self._call_api(endpoint=endpoint)