import abc
import time
from typing import Self


class MainLoopBase(abc.ABC):
    def __init__(self) -> Self:
        self.is_succeeded: bool = True

    @abc.abstractmethod
    def pre_step(self):
        pass

    @abc.abstractmethod
    def main_step(self):
        pass

    @abc.abstractmethod
    def post_step(self):
        pass

    @abc.abstractmethod
    def is_finished(self) -> bool:
        pass

    def wait(self) -> None:
        time.sleep(1)

    def set_exit_status(self, status: bool):
        self.is_succeeded = status


def run_mainloop(mainloop: MainLoopBase) -> bool:
    mainloop.pre_step()

    while not mainloop.is_finished():
        mainloop.main_step()

        # TODO: signal check

        mainloop.wait()

    mainloop.post_step()

    return mainloop.is_succeeded
