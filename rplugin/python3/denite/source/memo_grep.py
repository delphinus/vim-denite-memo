# ============================================================================
# FILE: memo_grep.py
# AUTHOR: delphinus <delphinus@remora.cx>
# License: MIT license
# ============================================================================

import subprocess
import sys
from os.path import dirname
sys.path.append(dirname(dirname(__file__)))

from memo_cmd import Memo, CommandNotFoundError
from .grep import Source as Grep


class Source(Grep):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'memo/grep'

    def on_init(self, context):
        try:
            memo_dir = Memo().get_memo_dir()
        except CommandNotFoundError as err:
            self.error_message(context, str(err))
        except subprocess.CalledProcessError as err:
            self.error_message(
                context, 'command returned invalid response: ' + str(err))
        context['args'].insert(0, memo_dir)
        super().on_init(context)
