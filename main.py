import sys
import stat
import time
import json
import pprint
import datetime
import subprocess
import dataclasses
import requests
from pathlib import Path
from typing import Self, List, Optional
from lib.ms_auth_lib import get_access_token
from lib.utils import info, error


HOOK_SCRIPT_DIR = Path(__file__).parent / "hook-scripts"


@dataclasses.dataclass
class Message:
    subject: str = ""
    content_type: str = "text"
    content: str = ""
    sender: dict = dataclasses.field(default_factory=dict)
    to_recipients: List[List[str]] = dataclasses.field(default_factory=list)
    cc_recipients: List[List[str]] = dataclasses.field(default_factory=list)
    bcc_recipients: List[List[str]] = dataclasses.field(default_factory=list)
    created_date_time: datetime.datetime = datetime.datetime(1980, 1, 1)
    received_date_time: datetime.datetime = datetime.datetime(1980, 1, 1)
    sent_date_time: datetime.datetime = datetime.datetime(1980, 1, 1)

    def __str__(self):
        return f"{self.sender['name']} <{self.sender['address']}> {self.content_type} {len(self.content)} chars"

    def to_json(self) -> dict:
        return {
            "subject": self.subject,
            "content_type": self.content_type,
            "content": self.content,
            "sender": self.sender,
            "to_recipients": self.to_recipients,
            "cc_recipients": self.cc_recipients,
            "bcc_recipients": self.bcc_recipients,
            "created_date_time": str(self.created_date_time),
            "received_date_time": str(self.received_date_time),
            "sent_date_time": str(self.sent_date_time),
        }

    def to_json_str(self) -> str:
        return json.dumps(self.to_json())

    @staticmethod
    def from_json(ms_message: dict) -> Self:
        args = {}

        if "subject" in ms_message:
            args["subject"] = ms_message["subject"]

        if "body" in ms_message:
            if "contentType" in ms_message["body"]:
                args["content_type"] = ms_message["body"]["contentType"]
            if "content" in ms_message["body"]:
                args["content"] = ms_message["body"]["content"]

        sender = {
            "name": ms_message.get("sender", {}).get("emailAddress", {}).get("name"),
            "address": ms_message.get("sender", {})
            .get("emailAddress", {})
            .get("address"),
        }
        args["sender"] = sender

        to_recipients = []
        cc_recipients = []
        bcc_recipients = []

        for r in ms_message.get("toRecipients", []):
            ent = {
                "name": r.get("emailAddress", {}).get("name"),
                "address": r.get("emailAddress", {}).get("address"),
            }
            to_recipients.append(ent)

        for r in ms_message.get("ccRecipients", []):
            ent = {
                "name": r.get("emailAddress", {}).get("name"),
                "address": r.get("emailAddress", {}).get("address"),
            }
            cc_recipients.append(ent)

        for r in ms_message.get("bccRecipients", []):
            ent = {
                "name": r.get("emailAddress", {}).get("name"),
                "address": r.get("emailAddress", {}).get("address"),
            }
            bcc_recipients.append(ent)

        args["to_recipients"] = to_recipients
        args["cc_recipients"] = cc_recipients
        args["bcc_recipients"] = bcc_recipients

        if "createdDateTime" in ms_message:
            args["created_date_time"] = datetime.datetime.fromisoformat(
                ms_message["createdDateTime"]
            ).astimezone(datetime.timezone(datetime.timedelta(hours=9)))

        if "receivedDateTime" in ms_message:
            args["received_date_time"] = datetime.datetime.fromisoformat(
                ms_message["receivedDateTime"],
            ).astimezone(datetime.timezone(datetime.timedelta(hours=9)))

        if "sentDateTime" in ms_message:
            args["sent_date_time"] = datetime.datetime.fromisoformat(
                ms_message["sentDateTime"]
            ).astimezone(datetime.timezone(datetime.timedelta(hours=9)))

        return Message(**args)


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


def get_new_mail(
    tenant: str, client_id: str, redirect_uri: str, username: str, mail_folder_id: str
):
    auth_info = get_access_token(username, tenant, client_id, redirect_uri, silent=True)

    if auth_info is None:
        error("Failed to acquire access token (silet mode enabled)")
        return

    next_link = f"https://graph.microsoft.com/v1.0/me/mailFolders/{mail_folder_id}/messages/delta?changeType=created"
    delta_link = None

    err = False
    while True:
        while True:
            res = access_graph_api(auth_info, next_link)
            if res is None:
                error(f"Failed to access inbox messages")

                # The access token may be expired, try to refresh it silently
                auth_info = get_access_token(
                    username,
                    tenant,
                    client_id,
                    redirect_uri,
                    silent=True,
                )
                if auth_info is None:
                    error("Failed to refresh access token (silet mode enabled)")
                    err = True
                    break
                else:
                    info("Retrying the previous access")
                    continue

            for message in res["value"]:
                yield message

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


def usage():
    print(
        """Usage: main.py <USERNAME> <MAIL_FOLDER_ID> <TENANT> [<CLIENT_ID> <REDIRECT_URI>]

This utility monitors an Outlook/Exchange mailbox by polling the
Microsoft Graph API for new messages and runs hook scripts for each new message.

You must obtain a valid refresh token in advance by running ms-auth.py.

Default CLIENT_ID and REDIRECT_URI are the Office 365 application ID
(d3590ed6-52b3-4102-aeff-aad2292ab01c) and "urn:ietf:wg:oauth:2.0:oob"
respectively.

Example:
    python main.py john.doe@example.com MAIL_FOLDER_ID_TO_MONITOR aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
"""
    )


@dataclasses.dataclass
class Args:
    username: str
    mail_folder_id: str
    tenant: str
    client_id: str = r"d3590ed6-52b3-4102-aeff-aad2292ab01c"
    redirect_uri: str = r"urn:ietf:wg:oauth:2.0:oob"

    @staticmethod
    def parse(cmdline: List[str]) -> Self:
        # Remove command name
        args = cmdline[1:]

        nr_args = len(args)
        if nr_args < 3:
            raise ValueError("Not enough arguments")
        elif nr_args == 3:
            return Args(username=args[0], mail_folder_id=args[1], tenant=args[2])
        elif nr_args == 5:
            return Args(
                username=args[0],
                mail_folder_id=args[1],
                tenant=args[2],
                client_id=args[3],
                redirect_uri=args[4],
            )
        else:
            raise ValueError(
                "REDIRECT_URI and CLIENT_ID should be both specified or both omitted"
            )


def main():
    global HOOK_SCRIPT_DIR

    args = None
    try:
        args = Args.parse(sys.argv)
    except ValueError as e:
        error(str(e))
        usage()
        sys.exit(1)

    auth_info = get_access_token(
        args.username, args.tenant, args.client_id, args.redirect_uri, silent=True
    )
    if auth_info is None:
        error(
            "Failed to acquire access token (silet mode enabled). Please run ms-auth.py to acquire a valid token."
        )
        sys.exit(1)

    res = access_graph_api(auth_info, "https://graph.microsoft.com/v1.0/me")
    if res is not None:
        info("API access check succeeded (https://graph.microsoft.com/v1.0/me)")

    res = access_graph_api(
        auth_info,
        f"https://graph.microsoft.com/v1.0/me/mailFolders/{args.mail_folder_id}",
    )
    if res is None:
        error(f"Failed to access mail folders:\n{pprint.pformat(res)}")
        sys.exit(1)
    info(f"Mail folder information: displayName={res['displayName']}, id={res['id']}")

    new_mail_generator = get_new_mail(
        args.tenant,
        args.client_id,
        args.redirect_uri,
        args.username,
        args.mail_folder_id,
    )
    for ms_message in new_mail_generator:
        message = Message.from_json(ms_message)

        for hook in HOOK_SCRIPT_DIR.iterdir():
            if hook.is_file() and bool(hook.lstat().st_mode & stat.S_IXUSR):
                proc = subprocess.run(
                    str(hook.absolute()),
                    shell=False,
                    input=message.to_json_str(),
                    text=True,
                )

                if proc.returncode != 0:
                    error(f"{hook.absolute()} failed with {proc.returncode}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
