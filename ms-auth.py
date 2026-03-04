import sys
import dataclasses
from typing import List, Self
from ms_auth_lib import AUTH_CACHE_FILE, get_access_token
from utils import error


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


def usage():
    print("Usage: ms-auth.py <username> <tenant> [client_id redirect_uri]")


def main():
    args = None
    try:
        args = Args.parse(sys.argv)
    except ValueError as e:
        error(str(e))
        usage()
        sys.exit(1)

    access_token = get_access_token(
        args.username, args.tenant, args.client_id, args.redirect_uri
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
