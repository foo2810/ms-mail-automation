import sys

SYSTEMD_LOGGING = False
def enable_systemd_logging():
    global SYSTEMD_LOGGING
    SYSTEMD_LOGGING = True

def info(msg, end="\n"):
    global SYSTEMD_LOGGING
    
    prefix = "Info: "
    if SYSTEMD_LOGGING:
        prefix = "<6>"

    print(f"{prefix}{msg}", end=end)
    sys.stdout.flush()


def debug(msg, end="\n"):
    global SYSTEMD_LOGGING

    prefix = "Debug: "
    if SYSTEMD_LOGGING:
        prefix = "<7>"

    print(f"{prefix}{msg}", end=end)
    sys.stdout.flush()


def warn(msg, end="\n"):
    global SYSTEMD_LOGGING

    prefix = "Warn: "
    if SYSTEMD_LOGGING:
        prefix = "<4>"

    print(f"{prefix}{msg}", end=end)
    sys.stdout.flush()


def error(msg, end="\n"):
    global SYSTEMD_LOGGING

    prefix = "Error: "
    if SYSTEMD_LOGGING:
        prefix = "<3>"

    print(f"{prefix}{msg}", end=end, file=sys.stderr)
    sys.stderr.flush()
