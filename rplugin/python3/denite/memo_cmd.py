from distutils.spawn import find_executable
import re
import subprocess
from denite import process
from denite.util import UserContext

MEMO_DIR = re.compile(r'^memodir = "(.*?)"$', re.M)


class CommandNotFoundError(Exception):
    pass


class Memo:
    def __init__(self) -> None:
        command = find_executable("memo")
        if not command:
            raise CommandNotFoundError
        self.command = command

    def run(self, *args: str) -> str:
        command = [self.command, *args]
        cmd = subprocess.run(command, stdout=subprocess.PIPE, check=True)
        out: bytes = cmd.stdout
        return out.decode("utf-8")

    def proc(self, context: UserContext, *args: str) -> process.Process:
        command = [self.command, *args]
        return process.Process(command, context, context["path"])

    def get_memo_dir(self) -> str:
        txt = self.run("config", "--cat")
        match = MEMO_DIR.search(txt)
        return match.group(1) if match else ""
