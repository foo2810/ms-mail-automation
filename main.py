import sys
import time
import pprint
import dataclasses
from typing import Self, List, Optional

import requests

from ms_auth_lib import get_access_token
from utils import info, error


def access_graph_api(
    auth_info: dict,
    api_uri: str,
    headers: Optional[dict] = {},
    params: Optional[dict] = {},
) -> Optional[dict]:
    access_token = auth_info["access_token"]
    headers.update({"Authorization": f"Bearer {access_token}"})

    response = requests.get(api_uri, headers=headers, params=params)
    if response.status_code != 200:
        # c.f. https://learn.microsoft.com/ja-jp/graph/errors
        if len(response.text) > 0:
            err_data = pprint.pformat(response.json())
        else:
            err_data = ""
        error(
            f"Failed to access Graph API {api_uri}: {response.status_code} {response.reason}\n{err_data}"
        )
        return None

    # info(f"Successfully accessed Graph API {api_uri}")

    data = response.json()

    return data


def usage():
    print(
        """
Usage: main.py <USERNAME> <TENANT> [<CLIENT_ID> <REDIRECT_URI>]

This tool acquires an access token for the Microsoft Graph API using
the provided username and tenant. The token is cached for future use.
If the token is expired or not found, the tool will prompt for authentication.

Default CLIENT_ID and REDIRECT_URI are Microsoft Office 365 App ID and OOB URI, respectively.

Example:
    python main.py john.doe@example.com aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
"""
    )


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
            return Args(
                username=args[0],
                tenant=args[1],
                client_id=args[2],
                redirect_uri=args[3],
            )
        else:
            raise ValueError(
                "redirect_uri and client_id should be both specified or both omitted"
            )


def main():
    args = None
    try:
        args = Args.parse(sys.argv)
    except ValueError as e:
        error(str(e))
        usage()
        sys.exit(1)

    auth_info = get_access_token(
        args.username, args.tenant, args.client_id, args.redirect_uri
    )
    if auth_info is None:
        sys.exit(1)

    res = access_graph_api(auth_info, "https://graph.microsoft.com/v1.0/me")
    if res is not None:
        print("Your account information:")
        pprint.pprint(res)
        print("-" * 80, flush=True)

    res = access_graph_api(auth_info, "https://graph.microsoft.com/v1.0/me/mailFolders")
    if res is None:
        error(f"Failed to access mail folders:\n{pprint.pformat(res)}")
        sys.exit(1)

    # Monitor new messages in the inbox
    inbox_metainfo = next(
        filter(
            lambda folder_metainfo: folder_metainfo["displayName"] == "受信トレイ",
            res["value"],
        )
    )
    next_link = f"https://graph.microsoft.com/v1.0/me/mailFolders/{inbox_metainfo['id']}/messages/delta?changeType=created"
    delta_link = None

    err = False
    while True:
        while True:
            res = access_graph_api(auth_info, next_link)
            if res is None:
                error(f"Failed to access inbox messages")

                # The access token may be expired, try to refresh it silently
                auth_info = get_access_token(
                    args.username,
                    args.tenant,
                    args.client_id,
                    args.redirect_uri,
                    silent=True,
                )
                if auth_info is None:
                    err = True
                    break
                else:
                    info("Retrying the previous access")
                    continue

            for message in res["value"]:
                print(
                    f"Subject: {message["subject"]} from {message["from"]["emailAddress"]["name"]} <{message["from"]["emailAddress"]["address"]}>"
                )
                print(f"{message['body']['content']}")
                print("-" * 80, flush=True)

            if "@odata.nextLink" in res:
                next_link = res["@odata.nextLink"]
            else:
                if "@odata.deltaLink" in res:
                    delta_link = res["@odata.deltaLink"]
                assert delta_link is not None
                break

            time.sleep(0.1)

        if err:
            break

        next_link = delta_link
        time.sleep(10)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
