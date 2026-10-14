import sys
import json
import dataclasses
import traceback
from pathlib import Path
from typing import List, Self
from ..lib.ms_auth_lib import AUTH_CACHE_FILE, MSAPIAuthenticator
from ..lib.utils import info, error


DEFAULT_CONFIG_FILE = Path.home() / ".config/ms-mail-automation/config.json"


@dataclasses.dataclass(frozen=True)
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


@dataclasses.dataclass(frozen=True)
class Args:
    config_file: Path = DEFAULT_CONFIG_FILE

    @staticmethod
    def parse(cmdline: List[str]) -> Self:
        # Remove command name
        args = cmdline[1:]

        nr_args = len(args)
        if nr_args >= 1:
            obj = Args(Path(args[0]))
            if not obj.config_file.exists():
                raise ValueError(f"{obj.config_file} not exist")

            return obj

        return Args()


def usage():
    print("Usage: ms-auth.py [<CONFIG FILE>]")


def main() -> bool:
    try:
        args = Args.parse(sys.argv)
    except ValueError as e:
        error(str(e))
        usage()
        return False

    if not args.config_file.exists():
        error(f"Config file '{args.config_file}' does not exist. Please create it.")
        return False

    info(f"Config file: {args.config_file}")

    try:
        config = Config.from_file(args.config_file)
    except ValueError as e:
        error(str(e))
        return False

    ms_authenticator = MSAPIAuthenticator(
        config.username,
        config.tenant,
        config.client_id,
        config.redirect_uri,
    )

    access_token = ms_authenticator.get_access_token()
    if access_token is not None:
        print(f"Access token and refresh token have been saved to {AUTH_CACHE_FILE}")
    else:
        error("Authenticate failed")

    return True


def cli_main() -> int:
    try:
        exit_status = 0
        if not main():
            exit_status = 1
    except KeyboardInterrupt:
        exit_status = 130    # 128 + SIGINT
    except Exception as e:
        error(f"{e}")
        error(f"{traceback.format_exc()}")
        exit_status = 1
    finally:
        return exit_status
