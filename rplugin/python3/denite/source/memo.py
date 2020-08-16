# ============================================================================
# FILE: memo.py
# AUTHOR: delphinus <delphinus@remora.cx>
# License: MIT license
# ============================================================================

from platform import system
from typing import Dict, Optional, cast
from unicodedata import east_asian_width, normalize

from denite import process
from denite.source.base import Base
from denite.util import Candidate, Candidates, UserContext, Nvim

EAST_ASIAN_WIDTH: Dict[str, str] = {}
HIGHLIGHT_SYNTAX = [
    {"name": "Prefix", "link": "String", "re": r"\[new title\]"},
    {"name": "File", "link": "String", "re": r"\v.*( : )@="},
    {"name": "Title", "link": "Function", "re": r"\v( : )@<=.*"},
]


class Source(Base):
    def __init__(self, vim: Nvim):
        super().__init__(vim)

        self.name = "memo"
        self.kind = "memo"
        self.vars = {"column": 20, "ambiwidth": vim.options["ambiwidth"]}

    def on_init(self, context: UserContext) -> None:
        self.__set_proc(context, None)

    def gather_candidates(self, context: UserContext) -> Candidates:
        exe = self.vim.call("denite#memo#executable")
        if not exe:
            return []

        if context["args"] and context["args"][0] == "new":
            return self._is_new(context)

        if self.__proc(context):
            return self.__async_gather_candidates(context, context["async_timeout"])

        proc = process.Process(
            [exe, "list", "--format", "{{.Fullpath}}\t{{.File}}\t{{.Title}}"],
            context,
            context["path"],
        )
        self.__set_proc(context, proc)
        return self.__async_gather_candidates(context, context["async_timeout"])

    def __async_gather_candidates(
        self, context: UserContext, timeout: int
    ) -> Candidates:
        proc = self.__proc(context)
        if not proc:
            context["is_async"] = False
            return []
        outs, errs = proc.communicate(timeout=timeout)
        if errs:
            self.error_message(context, errs)
        context["is_async"] = not proc.eof()
        if proc.eof():
            self.__set_proc(context, None)

        def make_candidates(row: str) -> Candidate:
            fullpath, filename, title = row.split("\t", 2)
            cut = self.__stdwidthpart(
                filename, self.vars["column"], self.vars["ambiwidth"]
            )
            return {
                "word": filename,
                "abbr": f"{cut} : {title}",
                "action__path": fullpath,
            }

        return list(map(make_candidates, outs))

    def _is_new(self, context: UserContext) -> Candidates:
        if "memo_dir" not in self.vars or not self.vars["memo_dir"]:
            self.vars["memo_dir"] = self.vim.call("denite#memo#get_dir")
            if not self.vars["memo_dir"]:
                return []

        context["is_interactive"] = True
        title = context["input"]
        if not title:
            return []
        return [
            {
                "word": title,
                "abbr": "[new title] " + title,
                "action__memo_dir": self.vars["memo_dir"],
                "action__title": title,
                "action__is_new": True,
            }
        ]

    def highlight(self) -> None:
        for syn in HIGHLIGHT_SYNTAX:
            self.vim.command(
                "syntax match {0}_{1} /{2}/ contained containedin={0}".format(
                    self.syntax_name, syn["name"], syn["re"]
                )
            )
            self.vim.command(
                "highlight default link {0}_{1} {2}".format(
                    self.syntax_name, syn["name"], syn["link"]
                )
            )

    def __proc(self, context: UserContext) -> Optional[process.Process]:
        return cast(process.Process, context["__proc"]) if context["__proc"] else None

    def __set_proc(self, context: UserContext, proc: Optional[process.Process]) -> None:
        context["__proc"] = proc

    def __stdwidthpart(self, string: str, col: int, ambiwidth: str) -> str:
        # normalize string for filenames in macOS
        target = normalize("NFC", string) if system() == "Darwin" else string
        char_lengths = [(x, self.__char_width(x, ambiwidth)) for x in target]
        sum_len = sum(x for (_, x) in char_lengths)
        if sum_len < col:
            return target + " " * (col - sum_len)
        result = ""
        result_len = 0
        for (char, length) in char_lengths:
            next_result = result + char
            next_len = result_len + length
            if next_len > col - 3:
                return result + ("...." if result_len < col - 3 else "...")
            elif next_len == col - 3:
                return next_result + "..."
            result = next_result
            result_len = next_len
        return ""

    def __char_width(self, char: str, ambiwidth: str) -> int:
        """
        this func returns 2 if it is Zenkaku string, 1 if other.  Each type, 'F',
        'W', 'A', means below.

        * F -- Fullwidth
        * W -- Wide
        * A -- Ambiguous
        """
        if char not in EAST_ASIAN_WIDTH:
            EAST_ASIAN_WIDTH[char] = east_asian_width(char)
        to_double = "FW" if ambiwidth == "single" else "FWA"
        return 2 if EAST_ASIAN_WIDTH[char] in to_double else 1
