from distutils.spawn import find_executable
import re
import subprocess
from denite import process

MEMO_DIR = re.compile(r'^memodir = "(.*?)"$', re.M)


class CommandNotFoundError(Exception):
    pass


class Memo:

    def __init__(self):
        command = find_executable('memo')
        if not command:
            raise CommandNotFoundError
        self.command = command

    def run(self, *args):
        command = [self.command, *args]
        cmd = subprocess.run(command, stdout=subprocess.PIPE, check=True)
        return cmd.stdout.decode('utf-8')

    def proc(self, context, *args):
        command = [self.command, *args]
        return process.Process(command, context, context['path'])

    def get_memo_dir(self):
        txt = self.run('config', '--cat')
        match = MEMO_DIR.search(txt)
        return match.group(1) if match else ''
