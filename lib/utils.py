import sys
import time

def info(msg, end="\n"):
    ts = time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"{ts}: Info: {msg}", end=end)
    sys.stdout.flush()


def debug(msg, end="\n"):
    ts = time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"{ts}: Debug: {msg}", end=end)
    sys.stdout.flush()


def warn(msg, end="\n"):
    ts = time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"{ts}: Warn: {msg}", end=end)
    sys.stdout.flush()


def error(msg, end="\n"):
    ts = time.strftime(r"%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"{ts}: Error: {msg}", end=end)
    sys.stdout.flush()
