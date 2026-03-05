import sys

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
    sys.stderr.write(f"Error: {msg}{end}")
    sys.stdout.flush()
