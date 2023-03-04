"""WienerNetze API that provides data from the SmartMeter API"""

from urllib import parse
import logging
import requests
from lxml import html
from datetime import datetime, timedelta
from .. import constants as const

LOGIN_ARGS = {
    "client_id": "wn-smartmeter",
    "redirect_uri": "https://smartmeter-web.wienernetze.at/",
    "response_mode": "fragment",
    "response_type": "code",
    "scope": "openid",
    "nonce": "",
}

_LOGGER = logging.getLogger(__name__)


class WienerNetzeAPI:
    """WienerNetze API Client."""

    def __init__(self, username, password) -> None:
        """Access the Smartmeter API.

        Args:
            username (str): Username used for API Login.
            password (str): Username used for API Login.
            login (bool, optional): If _login() should be called. Defaults to True.
        """
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._access_token = None
        self._refresh_token = None
        self._api_gateway_token = None

    def login(self):
        """login"""
        _LOGGER.debug("login")
        login_url = const.AUTH_URL + "auth?" + parse.urlencode(const.LOGIN_ARGS)
        try:
            result = self.session.get(login_url)
        except Exception as exception:
            raise ConnectionError(
                "Could not load login page: " + exception
            ) from Exception
        if result.status_code != 200:
            raise ConnectionError(
                f"Could not load login page. Error: {result.content}"
            ) from Exception

        tree = html.fromstring(result.content)
        action = tree.xpath("(//form/@action)")[0]

        try:
            result = self.session.post(
                action,
                data={
                    "username": self.username,
                    "password": self.password,
                },
                allow_redirects=False,
            )
        except Exception:
            raise ConnectionError("Could not load login page.") from Exception
        if "Location" not in result.headers:
            raise ConnectionError(
                "Login failed. Check username/password."
            ) from Exception
        location = result.headers["Location"]
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
            raise ConnectionError(
                "Login failed. Could not extract 'code' from 'Location'"
            ) from Exception
        try:
            result = self.session.post(
                const.AUTH_URL + "token",
                data=const.build_access_token_args(code=code),
            )
        except Exception:
            raise ConnectionError("Could not obtain access token") from Exception

        if result.status_code != 200:
            raise ConnectionError("Could not obtain access token") from Exception

        self._access_token = result.json()["access_token"]
        self._refresh_token = result.json()["refresh_token"]
        self._api_gateway_token = self._get_api_key(self._access_token)

    def _get_api_key(self, token):
        headers = {"Authorization": f"Bearer {token}"}
        try:
            result = self.session.get(const.PAGE_URL, headers=headers)
        except Exception:
            raise ConnectionError("Could not obtain API key") from Exception
        tree = html.fromstring(result.content)
        scripts = tree.xpath("(//script/@src)")
        for script in scripts:
            try:
                response = self.session.get(const.PAGE_URL + script)
            except Exception:
                raise ConnectionError(
                    "Could not obtain API key from scripts"
                ) from Exception
            for match in const.API_GATEWAY_TOKEN_REGEX.findall(response.text):
                return match
        _LOGGER.error("Could not obtain API key - no match")

    def _call_api(
        self,
        endpoint,
        base_url=None,
        method="GET",
        data=None,
        query=None,
        return_response=False,
        timeout=60.0,
    ):
        if base_url is None:
            base_url = const.API_URL
        url = f"{base_url}{endpoint}"

        if query:
            url += ("?" if "?" not in endpoint else "&") + parse.urlencode(query)
        _LOGGER.debug(url)
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "X-Gateway-APIKey": self._api_gateway_token,
        }

        if data:
            headers["Content-Type"] = "application/json"

        response = self.session.request(
            method, url, headers=headers, json=data, timeout=timeout
        )

        if return_response:
            return response

        return response.json()

    def _dt_string(self, datetime_string):
        return datetime_string.strftime(const.API_DATE_FORMAT)[:-3] + "Z"

    def get_zaehlerstand(self):
        """getting zaehlerstand from the smartmeter api"""
        _LOGGER.debug("get_zaehlerstand")
        return self._call_api("zaehlpunkt/meterReadings")

    def get_consumption(self, zaehlerpunkt: str):
        """getting verbrauchRaw data from the smartmeter api"""
        _LOGGER.debug("get_consumption")
        endpoint = f"messdaten/zaehlpunkt/{zaehlerpunkt}/verbrauchRaw"
        date_from = datetime.today() - timedelta(days=4)
        date_to = datetime.today() + timedelta(days=1)
        query = {
            "dateFrom": self._dt_string(
                date_from.replace(hour=23, minute=00, second=0, microsecond=0)
            ),
            "dateTo": self._dt_string(
                date_to.replace(hour=22, minute=59, second=59, microsecond=9)
            ).replace(".000Z", ".999Z"),
            "granularity": "DAY",
        }
        _LOGGER.debug(query)
        return self._call_api(endpoint, query=query)
