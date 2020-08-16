# ============================================================================
# FILE: memo_grep.py
# AUTHOR: delphinus <delphinus@remora.cx>
# License: MIT license
# ============================================================================

from denite.source.grep import Source as Grep
from denite.util import Nvim, UserContext


class Source(Grep):
    def __init__(self, vim: Nvim):
        super().__init__(vim)

        self.name = "memo/grep"

    def on_init(self, context: UserContext):
        if "memo_dir" not in self.vars or not self.vars["memo_dir"]:
            self.vars["memo_dir"] = self.vim.call("denite#memo#get_dir")
        context["args"].insert(0, self.vars["memo_dir"])
        return super().on_init(context)

    def gather_candidates(self, context: UserContext):
        if not self.vim.call("denite#memo#executable"):
            return []
        return super().gather_candidates(context)
