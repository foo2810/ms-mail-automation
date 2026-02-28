import sys
import time
import json
import pprint
import dataclasses
from pathlib import Path
from typing import Self, List, Optional

import msal
import requests
import urllib


AUTH_CACHE_FILE = Path.home() / ".ms-mail-automation-cache"


def info(msg, end="\n"):
    print(f"Info: {msg}", end=end)
    sys.stdout.flush()

def debug(msg, end="\n"):
    print(f"Debug: {msg}", end=end)
    sys.stdout.flush()

def warn(msg, end="\n"):
    print(f"Warn: {msg}", end=end)
    sys.stdout.flush()

def error(msg, end="\n"):
    print(f"Error: {msg}", end=end)
    sys.stdout.flush()


def authenticate(app: msal.ClientApplication, scopes: List[str], redirect_uri: str) -> Optional[dict]:
    global AUTH_CACHE_FILE

    code = app.initiate_auth_code_flow(scopes, redirect_uri=redirect_uri, response_mode="query")
    print("Authentication flow:\n")
    print("""
1. Open a browser and open the Network tab in the developer tools.
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
    auth_info: dict = app.acquire_token_by_auth_code_flow(code, auth_response, scopes)

    if "error" in auth_info:
        error(f"{auth_info['error_description']}")
        return None

    return auth_info

def get_access_token(username: str, tenant: str, client_id: str, redirect_uri: str) -> Optional[dict]:
    authority = f"https://login.microsoftonline.com/{tenant}"

    # For Graph API (API Endpoint: https://graph.microsoft.com/v1.0)
    scopes = ["https://graph.microsoft.com/.default"]

    # For (Old) Outlook REST API (API Endpoint: https://outlook.office.com/api/v2.0)
    # scopes = ["https://outlook.office.com/.default"]

    cache = msal.SerializableTokenCache()

    if AUTH_CACHE_FILE.exists():
        info("Loading token cache")
        with open(AUTH_CACHE_FILE, "r") as f:
            cache.deserialize(f.read())

    app = msal.PublicClientApplication(
        client_id, authority=authority, token_cache=cache)

    auth_info = None
    accounts = app.get_accounts(username=username)
    assert len(accounts) <= 1, "Multiple accounts found for the given username. This should not happen."
    if len(accounts) == 1:
        account = accounts[0]
        info("Acquire access token from cache")

        # `acquire_token_silent` tries to acquire access token using token cache,
        # which is saved in previous authentication.
        auth_info: dict = app.acquire_token_silent(
            scopes, account, authority, force_refresh=False)

    # Reauthenticate if acquire_token_silent fails
    # (e.g. no token in cache or token expired)
    if auth_info is None:
        info("Cache not exists or refresh token expired. Reauthenticating...")
        auth_info: dict = authenticate(app, scopes, redirect_uri)

    if auth_info is not None:
        info("Authentication successful")

        # Save token cache if authentication is successful
        AUTH_CACHE_FILE.touch(0o600)
        with AUTH_CACHE_FILE.open("w") as f:
            f.write(cache.serialize())

        info("Authentication info is saved to auth-info.json")
        with open("auth-info.json", "w") as f:
            json.dump(auth_info, f)

        return auth_info
    else:
        error("Authentication failed")
        return None

def access_graph_api(auth_info: dict, api_uri: str, headers: Optional[dict] = {}, params: Optional[dict] = {}) -> Optional[dict]:
    access_token = auth_info["access_token"]
    headers.update({"Authorization": f"Bearer {access_token}"})

    response = requests.get(api_uri, headers=headers, params=params)
    if response.status_code != 200:
        # c.f. https://learn.microsoft.com/ja-jp/graph/errors
        if len(response.text) > 0:
            err_data = pprint.pformat(response.json())
        else:
            err_data = ""
        error(f"Failed to access Graph API {api_uri}: {response.status_code} {response.reason}\n{err_data}")
        return None

    # info(f"Successfully accessed Graph API {api_uri}")

    data = response.json()

    return data

def usage():
    print("""
Usage: main.py <USERNAME> <TENANT> [<CLIENT_ID> <REDIRECT_URI>]

This tool acquires an access token for the Microsoft Graph API using
the provided username and tenant. The token is cached for future use.
If the token is expired or not found, the tool will prompt for authentication.
          
Default CLIENT_ID and REDIRECT_URI are Microsoft Office 365 App ID and OOB URI, respectively.

Example:
    python main.py john.doe@example.com aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
""")

@dataclasses.dataclass
class Args:
    username: str
    tenant: str
    client_id: str = r"d3590ed6-52b3-4102-aeff-aad2292ab01c"
    redirect_uri: str = r"urn:ietf:wg:oauth:2.0:oob"

    @staticmethod
    def parse(cmdline: List[str]) -> Self:
        # Remove command name
        args = cmdline[1:]

        nr_args = len(args)
        if nr_args < 2:
            raise ValueError("Not enough arguments")
        elif nr_args == 2:
            return Args(username=args[0], tenant=args[1])
        elif nr_args == 4:
            return Args(username=args[0], tenant=args[1], client_id=args[2], redirect_uri=args[3])
        else:
            raise ValueError("redirect_uri and client_id should be both specified or both omitted")

def main():
    args = None
    try:
        args = Args.parse(sys.argv)
    except ValueError as e:
        error(str(e))
        usage()
        sys.exit(1)

    auth_info = get_access_token(args.username, args.tenant, args.client_id, args.redirect_uri)
    if auth_info is None:
        sys.exit(1)

    res = access_graph_api(auth_info, "https://graph.microsoft.com/v1.0/me")
    if res is not None:
        print("Your account information:")
        pprint.pprint(res)

    res = access_graph_api(auth_info, "https://graph.microsoft.com/v1.0/me/mailFolders")
    if res is None:
        error(f"Failed to access mail folders:\n{pprint.pformat(res)}")
        sys.exit(1)

    # Monitor new messages in the inbox
    inbox_metainfo = next(filter(lambda folder_metainfo: folder_metainfo["displayName"] == "受信トレイ", res["value"]))
    next_link = f"https://graph.microsoft.com/v1.0/me/mailFolders/{inbox_metainfo['id']}/messages/delta?changeType=created"
    delta_link = None

    while True:
        while True:
            res = access_graph_api(auth_info, next_link)
            if res is None:
                error(f"Failed to access inbox messages:\n{pprint.pformat(res)}")
                break
            
            for message in res["value"]:
                print(f"{message["subject"]} from {message["from"]["emailAddress"]["name"]} <{message["from"]["emailAddress"]["address"]}>")

            if "@odata.nextLink" in res:
                next_link = res["@odata.nextLink"]
            else:
                if "@odata.deltaLink" in res:
                    delta_link = res["@odata.deltaLink"]
                assert delta_link is not None
                break

            time.sleep(0.1)

        next_link = delta_link
        time.sleep(10)

if __name__ == "__main__":
    main()
