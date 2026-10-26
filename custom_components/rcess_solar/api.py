"""API client for the RC-C Solar (rc-ess) cloud backend.

This talks to the same ``app.rc-ess.com`` jowoiot backend used by the official
RC-C mobile app. The contract was reverse-engineered from the app's traffic:

* ``POST /project/rc/auth/login``        -> access token
* ``POST /project/rc/station/overview/searchStation`` -> stations
* ``GET  /project/rc/station/item/getList?stationId=`` -> devices
* ``GET  /project/rc/device/data/{id}``  -> live inverter data
"""
from __future__ import annotations

import logging

import aiohttp

from .const import BASE_URL, TENANT_HEADERS

_LOGGER = logging.getLogger(__name__)


class RcEssAuthError(Exception):
    """Raised when authentication fails."""


class RcEssApiError(Exception):
    """Raised on a generic API error."""


class RcEssClient:
    """Minimal async client for the jowoiot RC backend used by the RC-C app."""

    def __init__(
        self, session: aiohttp.ClientSession, email: str, password: str
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._token: str | None = None

    def _headers(self, auth: bool = True) -> dict[str, str]:
        headers = {"Content-Type": "application/json;charset=utf-8", **TENANT_HEADERS}
        if auth and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def login(self) -> None:
        """Authenticate and store the access token."""
        payload = {
            "channelType": 2,
            "content": self._email,
            "password": self._password,
            "type": "2",
        }
        async with self._session.post(
            f"{BASE_URL}/project/rc/auth/login",
            json=payload,
            headers=self._headers(auth=False),
        ) as resp:
            data = await resp.json(content_type=None)
        if data.get("code") != 200:
            raise RcEssAuthError(data.get("message") or "Login failed")
        try:
            self._token = data["data"]["response"]["accessToken"]
        except (KeyError, TypeError) as err:
            raise RcEssAuthError("No access token in login response") from err

    async def _get(self, path: str, retry: bool = True):
        if self._token is None:
            await self.login()
        async with self._session.get(
            f"{BASE_URL}{path}", headers=self._headers()
        ) as resp:
            if resp.status == 401 and retry:
                self._token = None
                return await self._get(path, retry=False)
            data = await resp.json(content_type=None)
        return data

    async def _post(self, path: str, body: dict, retry: bool = True):
        if self._token is None:
            await self.login()
        async with self._session.post(
            f"{BASE_URL}{path}", json=body, headers=self._headers()
        ) as resp:
            if resp.status == 401 and retry:
                self._token = None
                return await self._post(path, body, retry=False)
            data = await resp.json(content_type=None)
        return data

    async def async_get_stations(self) -> list[dict]:
        data = await self._post(
            "/project/rc/station/overview/searchStation", {"page": 1, "row": 100}
        )
        if data.get("code") != 200:
            raise RcEssApiError("Failed to list stations")
        return data["data"]["content"]

    async def async_get_devices(self, station_id: str) -> list[dict]:
        data = await self._get(
            f"/project/rc/station/item/getList?stationId={station_id}"
        )
        if data.get("code") != 200:
            raise RcEssApiError("Failed to list devices")
        return data["data"]

    async def async_get_device_data(self, device_id: str) -> dict:
        data = await self._get(f"/project/rc/device/data/{device_id}")
        if data.get("code") != 200:
            raise RcEssApiError("Failed to get device data")
        return data["data"]

    async def async_discover(self) -> list[dict]:
        """Return a flat list of devices with their station names."""
        devices: list[dict] = []
        for station in await self.async_get_stations():
            for device in await self.async_get_devices(station["id"]):
                device["_station_name"] = station.get("name")
                devices.append(device)
        return devices
