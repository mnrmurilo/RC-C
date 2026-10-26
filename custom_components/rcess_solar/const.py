"""Constants for the RC-C Solar (rc-ess) integration."""

DOMAIN = "rcess_solar"

CONF_UPDATE_INTERVAL = "update_interval"
DEFAULT_UPDATE_INTERVAL = 60

BASE_URL = "https://app.rc-ess.com/jowoiot-proxy/api"

# Tenant headers sent by the official RC-C app. Required for all requests.
TENANT_HEADERS = {
    "scope": "yx_test",
    "OwnerId": "1",
    "oem": "rc",
}
