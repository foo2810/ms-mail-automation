import sys
import json
import msal
import urllib
from pathlib import Path
from typing import List, Optional
from utils import debug, error


AUTH_CACHE_FILE = Path.home() / ".ms-mail-automation-cache"


def authenticate(
    app: msal.ClientApplication, scopes: List[str], redirect_uri: str
) -> Optional[dict]:
    global AUTH_CACHE_FILE

    code = app.initiate_auth_code_flow(
        scopes, redirect_uri=redirect_uri, response_mode="query"
    )
    print("Authentication flow:")
    print(
        """1. Open a browser and open the Network tab in the developer tools.
2. From the current tab, access the authentication URL, then login and grant authorization to the resource.
3. In the Network tab, find the request to a URI that starts with "urn:" and copy everything after code= in the query parameters.
4. Return to the terminal and enter the copied authorization code.
"""
    )
    print(f"Authentication URL: {code['auth_uri']}")

    print("Input authorization code:", end="")
    sys.stdout.flush()
    auth_response_str = input()

    # Copied authorization code may be URL-encoded, so decode it
    auth_response_str = urllib.parse.unquote(auth_response_str)

    auth_response = dict(item.split("=") for item in auth_response_str.split("&"))
    auth_info: dict = app.acquire_token_by_auth_code_flow(code, auth_response, scopes)

    if "error" in auth_info:
        error(f"{auth_info['error_description']}")
        return None

    return auth_info


def get_access_token(
    username: str, tenant: str, client_id: str, redirect_uri: str, silent: bool = False
) -> Optional[dict]:
    """Acquire an access token for the Microsoft Graph API.

    Args:
        username (str): The username (email address) of the account to authenticate.
        tenant (str): The tenant ID: <your tenant ID> / common / organizations / consumers.
        client_id (str): The client ID of the application.
        redirect_uri (str): The redirect URI of the application.
        silent (bool): If True, do not try interactive authentication
                       (i.e. Only try to authenticate using refresh token)

    Returns:
        Optional[dict]: If authentication is successful, returns the dict
                        containing the access token and other information.
                        Otherwise, returns None.
    """
    authority = f"https://login.microsoftonline.com/{tenant}"

    # For Graph API (API Endpoint: https://graph.microsoft.com/v1.0)
    scopes = ["https://graph.microsoft.com/.default"]

    # For (Old) Outlook REST API (API Endpoint: https://outlook.office.com/api/v2.0)
    # scopes = ["https://outlook.office.com/.default"]

    cache = msal.SerializableTokenCache()

    if AUTH_CACHE_FILE.exists():
        debug("Loading token cache")
        with open(AUTH_CACHE_FILE, "r") as f:
            cache.deserialize(f.read())

    app = msal.PublicClientApplication(
        client_id, authority=authority, token_cache=cache
    )

    auth_info = None

    accounts = app.get_accounts(username=username)
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
        auth_info: dict = app.acquire_token_silent(
            scopes, account, authority, force_refresh=False
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
        auth_info: dict = authenticate(app, scopes, redirect_uri)

    if auth_info is not None:
        debug("Authentication succeeded")

        # Save token cache if authentication is successful
        AUTH_CACHE_FILE.touch(0o600)
        with AUTH_CACHE_FILE.open("w") as f:
            f.write(cache.serialize())

        auth_info_file = Path("auth-info.json")
        if auth_info_file.exists():
            auth_info_file.unlink()
        auth_info_file.touch(0o600)
        with auth_info_file.open("w") as f:
            json.dump(auth_info, f)
        debug("Authentication info is saved to auth-info.json")

        return auth_info
    else:
        debug("Authentication failed")
        return None
