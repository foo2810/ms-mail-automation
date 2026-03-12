import sys
import json
import dataclasses
from pathlib import Path
from typing import List, Self
from lib.ms_auth_lib import AUTH_CACHE_FILE, get_access_token
from lib.utils import error


@dataclasses.dataclass
class Config:
    username: str
    mail_folder_id: str
    tenant: str
    client_id: str = r"d3590ed6-52b3-4102-aeff-aad2292ab01c"
    redirect_uri: str = r"urn:ietf:wg:oauth:2.0:oob"

    @staticmethod
    def from_file(config_file: Path) -> Self:
        jdict = None
        with config_file.open("r") as f:
            jdict: dict = json.load(f)

        assert jdict is not None

        if "username" not in jdict:
            raise ValueError('"username" is required, but not found')
        username = jdict["username"]

        if "mail_folder_id" not in jdict:
            raise ValueError('"mail_folder_id" is required, but not found')
        mail_folder_id = jdict["mail_folder_id"]

        if "tenant" not in jdict:
            raise ValueError('"tenant" is required, but not found')
        tenant = jdict["tenant"]

        client_id = jdict.get("client_id", None)
        redirect_uri = jdict.get("redirect_uri", None)

        if (client_id is None and redirect_uri is not None) or (
            client_id is None and redirect_uri is not None
        ):
            raise ValueError(
                '"redirect_uri" and "client_id" should be both specified or both omitted'
            )
        elif client_id is None and redirect_uri is None:
            return Config(
                username=username, mail_folder_id=mail_folder_id, tenant=tenant
            )
        else:
            return Config(
                username=username,
                mail_folder_id=mail_folder_id,
                tenant=tenant,
                client_id=client_id,
                redirect_uri=redirect_uri,
            )


@dataclasses.dataclass
class Args:
    config_file: Path

    @staticmethod
    def parse(cmdline: List[str]) -> Self:
        # Remove command name
        args = cmdline[1:]

        nr_args = len(args)
        if nr_args < 1:
            raise ValueError("Not enough arguments")
        else:
            obj = Args(Path(args[0]))
            if not obj.config_file.exists():
                raise ValueError(f"{obj.config_file} not exist")

            return obj


def usage():
    print("Usage: ms-auth.py <CONFIG FILE>")


def main():
    try:
        args = Args.parse(sys.argv)
    except ValueError as e:
        error(str(e))
        usage()
        sys.exit(1)

    try:
        config = Config.from_file(args.config_file)
    except ValueError as e:
        error(str(e))
        sys.exit(1)

    access_token = get_access_token(
        config.username, config.tenant, config.client_id, config.redirect_uri
    )
    if access_token is not None:
        print(f"Access token and refresh token have been saved to {AUTH_CACHE_FILE}")
    else:
        error("Authenticate failed")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
