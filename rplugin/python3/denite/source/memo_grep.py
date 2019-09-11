# ============================================================================
# FILE: memo_grep.py
# AUTHOR: delphinus <delphinus@remora.cx>
# License: MIT license
# ============================================================================

import subprocess
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.resolve()))

from vim_denite_memo.command import Memo, CommandNotFoundError
from denite.source.grep import Source as Grep
from denite.util import Nvim, UserContext


class Source(Grep):
    def __init__(self, vim: Nvim):
        super().__init__(vim)

        self.name = "memo/grep"

    def on_init(self, context: UserContext) -> None:
        try:
            memo_dir = Memo().get_memo_dir()
        except CommandNotFoundError as err:
            self.error_message(context, str(err))
        except subprocess.CalledProcessError as err:
            self.error_message(
                context, "command returned invalid response: " + str(err)
            )
        context["args"].insert(0, memo_dir)
        super().on_init(context)
