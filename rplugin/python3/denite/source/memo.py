# ============================================================================
# FILE: memo.py
# AUTHOR: delphinus <delphinus@remora.cx>
# License: MIT license
# ============================================================================

from subprocess import CalledProcessError
import sys
from pathlib import Path
from typing import Optional, cast

sys.path.append(str(Path(__file__).parent.parent.resolve()))

from vim_denite_memo.command import Memo
from vim_denite_memo.string import stdwidthpart
from denite import process
from denite.source.base import Base
from denite.util import Candidate, Candidates, UserContext, Nvim

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
        self.__set_memo(context, Memo())

    def gather_candidates(self, context: UserContext) -> Candidates:
        if context["args"] and context["args"][0] == "new":
            return self._is_new(context)

        if self.__proc(context):
            return self.__async_gather_candidates(context, context["async_timeout"])

        proc = self.__memo(context).proc(
            context, "list", "--format", "{{.Fullpath}}\t{{.File}}\t{{.Title}}"
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
            cut = stdwidthpart(filename, self.vars["column"], self.vars["ambiwidth"])
            return {
                "word": filename,
                "abbr": f"{cut} : {title}",
                "action__path": fullpath,
            }

        return list(map(make_candidates, outs))

    def _is_new(self, context: UserContext) -> Candidates:
        if "memo_dir" not in self.vars or not self.vars["memo_dir"]:
            try:
                self.vars["memo_dir"] = self.__memo(context).get_memo_dir()
            except CalledProcessError as err:
                self.error_message(
                    context, "command returned invalid response: " + str(err)
                )
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

    def __memo(self, context: UserContext) -> Memo:
        return cast(Memo, context["__memo"])

    def __set_memo(self, context: UserContext, memo: Memo) -> None:
        context["__memo"] = memo

    def __proc(self, context: UserContext) -> Optional[process.Process]:
        return cast(process.Process, context["__proc"]) if context["__proc"] else None

    def __set_proc(self, context: UserContext, proc: Optional[process.Process]) -> None:
        context["__proc"] = proc
