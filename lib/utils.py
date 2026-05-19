import sys
import enum


def _log_primitive(stream, text: str):
    stream.write(text)
    stream.flush()


def _log_with_prefix(stream, prefix: str, msg: str):
    # In multi-line messages, the second and subsequent lines do not start
    # with the log-level prefix, so they are not recorded
    # under an unintended log level.
    #
    # Implementation note:
    # If msg is empty, msg[-1] will raise an IndexError. So use msg[-1:] instead.
    text = msg[:-1].replace("\n", f"\n{prefix}") + msg[-1:]
    text = f"{prefix}{text}"

    _log_primitive(stream, text)


class _LogLevel(enum.IntEnum):
    ERROR = 0
    WARN = 1
    INFO = 2
    DEBUG = 3


class _LoggingType(enum.StrEnum):
    NORMAL = "normal-logging"
    SYSTEMD = "systemd-logging"


LOGGING_TYPE = _LoggingType.NORMAL


PREFIX_TABLE = {
    _LoggingType.NORMAL: {
        _LogLevel.ERROR: "Error: ",
        _LogLevel.WARN: "Warn: ",
        _LogLevel.INFO: "Info: ",
        _LogLevel.DEBUG: "Debug: ",
    },
    _LoggingType.SYSTEMD: {
        _LogLevel.ERROR: "<3>",
        _LogLevel.WARN: "<4>",
        _LogLevel.INFO: "<6>",
        _LogLevel.DEBUG: "<7>",
    },
}


def enable_systemd_logging():
    global LOGGING_TYPE
    LOGGING_TYPE = _LoggingType.SYSTEMD


def info(msg, end="\n"):
    global LOGGING_TYPE
    prefix = PREFIX_TABLE[LOGGING_TYPE][_LogLevel.INFO]
    _log_with_prefix(sys.stdout, prefix, f"{msg}{end}")


def debug(msg, end="\n"):
    global LOGGING_TYPE
    prefix = PREFIX_TABLE[LOGGING_TYPE][_LogLevel.DEBUG]
    _log_with_prefix(sys.stdout, prefix, f"{msg}{end}")


def warn(msg, end="\n"):
    global LOGGING_TYPE
    prefix = PREFIX_TABLE[LOGGING_TYPE][_LogLevel.WARN]
    _log_with_prefix(sys.stdout, prefix, f"{msg}{end}")


def error(msg, end="\n"):
    global LOGGING_TYPE
    prefix = PREFIX_TABLE[LOGGING_TYPE][_LogLevel.ERROR]
    _log_with_prefix(sys.stderr, prefix, f"{msg}{end}")
