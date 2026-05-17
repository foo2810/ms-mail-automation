import sys
import msal
import urllib
from pathlib import Path
from typing import Optional
from .utils import debug, error

AUTH_CACHE_FILE = Path.home() / ".ms-mail-automation-cache"


class MSAPIAuthenticator:
    def __init__(self, username: str, tenant: str, client_id: str, redirect_uri: str):
        self.username = username
        self.tenant = tenant
        self.client_id = client_id
        self.redirect_uri = redirect_uri

        self.authority = f"https://login.microsoftonline.com/{self.tenant}"

        # For Graph API (API Endpoint: https://graph.microsoft.com/v1.0)
        self.scopes = ["https://graph.microsoft.com/.default"]

        # For (Old) Outlook REST API (API Endpoint: https://outlook.office.com/api/v2.0)
        # self.scopes = ["https://outlook.office.com/.default"]

        self.cache = msal.SerializableTokenCache()

        if AUTH_CACHE_FILE.exists():
            debug("Loading token cache")
            with open(AUTH_CACHE_FILE, "r") as f:
                self.cache.deserialize(f.read())

        self.app = msal.PublicClientApplication(
            self.client_id, authority=self.authority, token_cache=self.cache
        )

    def get_access_token(self, silent: bool = False) -> Optional[dict]:
        auth_info = None

        accounts = self.app.get_accounts(username=self.username)
        assert (
            len(accounts) <= 1
        ), "Multiple accounts found for the given username. This should not happen."

        if len(accounts) == 0:
            debug("No cache")
            # If `silent` is True and no cache exists, just return None.
            if silent:
                return None
        else:
            account = accounts[0]
            debug("Refreshing access token")
            # `acquire_token_silent` tries to acquire access token using token cache,
            # which is saved in previous authentication.
            auth_info: dict = self.app.acquire_token_silent(
                self.scopes, account, self.authority, force_refresh=False
            )

        if auth_info is None:
            debug("Failed to refresh access token")

            # If `silent` is True, don't try interactive authentication,
            # just return None
            if silent:
                return None

        # Reauthenticate if refreshing access token fails.
        # (e.g. no cache or refresh token expired)
        if auth_info is None:
            debug("Cache not exists or refresh token expired. Reauthenticating...")
            auth_info: dict = self.authenticate()

        if auth_info is not None:
            debug("Authentication succeeded")

            # Save token cache if authentication is successful
            AUTH_CACHE_FILE.touch(0o600)
            with AUTH_CACHE_FILE.open("w") as f:
                f.write(self.cache.serialize())

            debug(f"Authorization cache is saved in {AUTH_CACHE_FILE}")

            return auth_info
        else:
            debug("Authentication failed")
            return None

    def authenticate(self) -> Optional[dict]:
        global AUTH_CACHE_FILE

        code = self.app.initiate_auth_code_flow(
            self.scopes, redirect_uri=self.redirect_uri, response_mode="query"
        )
        print("Authentication flow:")
        print("""1. Open a browser and open the Network tab in the developer tools.
    2. From the current tab, access the authentication URL, then login and grant authorization to the resource.
    3. In the Network tab, find the request to a URI that starts with "urn:" and copy everything after code= in the query parameters.
    4. Return to the terminal and enter the copied authorization code.
    """)
        print(f"Authentication URL: {code['auth_uri']}")

        print("Input authorization code:", end="")
        sys.stdout.flush()
        auth_response_str = input()

        # Copied authorization code may be URL-encoded, so decode it
        auth_response_str = urllib.parse.unquote(auth_response_str)

        auth_response = dict(item.split("=") for item in auth_response_str.split("&"))
        auth_info: dict = self.app.acquire_token_by_auth_code_flow(
            code, auth_response, self.scopes
        )

        if "error" in auth_info:
            error(f"{auth_info.get('error_description')}")
            return None

        return auth_info
