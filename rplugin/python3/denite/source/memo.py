# ============================================================================
# FILE: memo.py
# AUTHOR: delphinus <delphinus@remora.cx>
# License: MIT license
# ============================================================================

from distutils.spawn import find_executable
import re
import subprocess
from denite import process
from .base import Base

SEPARATOR = '{0}:{0}'.format(chr(0xa0))
MEMO_DIR = re.compile(r'^memodir = "(.*?)"$', re.M)

class Source(Base):

    def __init__(self, vim):
        super().__init__(vim)

        self.name = 'memo'
        self.kind = 'memo'
        self.vars = {
            'column': 20,
        }

    def on_init(self, context):
        context['__proc'] = None
        context['__memo'] = Memo()

    def gather_candidates(self, context):
        if context['args'] and context['args'][0] == 'new':
            return self._is_new(context)

        if context['__proc']:
            return self.__async_gather_candidates(
                context, context['async_timeout'])

        context['__proc'] = context['__memo'].proc(
            context,
            'list', '--format', '{{.Fullpath}}\t{{.File}}\t{{.Title}}')
        return self.__async_gather_candidates(
            context, context['async_timeout'])

    def __async_gather_candidates(self, context, timeout):
        outs, errs = context['__proc'].communicate(timeout=timeout)
        if errs:
            self.error_message(context, errs)
        context['is_async'] = not context['__proc'].eof()
        if context['__proc'].eof():
            context['__proc'] = None

        def make_candidates(row):
            fullpath, filename, title = row.split('\t', 2)
            cut = self._stdwidthpart(filename, self.vars['column'])
            return {
                'word': filename,
                'abbr': '{0}{1}{2}'.format(cut, SEPARATOR, title),
                'action__path': fullpath,
                }
        return list(map(make_candidates, outs))

    def _is_new(self, context):
        if 'memo_dir' not in self.vars or not self.vars['memo_dir']:
            try:
                self.vars['memo_dir'] = context['__memo'].get_memo_dir()
            except subprocess.CalledProcessError as err:
                self.error_message(
                    context, 'command returned invalid response: ' + str(err))
                return []

        context['is_interactive'] = True
        title = context['input']
        if not title:
            return []
        return [{
            'word': title,
            'abbr': '[new title] ' + title,
            'action__memo_dir': self.vars['memo_dir'],
            'action__title': title,
            'action__is_new': True,
            }]

    def _stdwidthpart(self, string, col):
        slen = self.vim.funcs.strwidth(string)
        if slen < col:
            return string + ' ' * (col - slen)
        result = ''
        i = 0
        while True:
            char = string[i:i+1]
            next_r = result + char
            nlen = self.vim.funcs.strwidth(next_r)
            if nlen > col - 3:
                rlen = self.vim.funcs.strwidth(result)
                return result + ('....' if rlen < col - 3 else '...')
            elif nlen == col - 3:
                return next_r + '...'
            result = next_r
            i += 1

    def highlight(self):
        self.vim.command(
            'syntax match {0}_Prefix /{1}/ contained containedin={0}'
            .format(self.syntax_name, r'\[new title\]'))
        self.vim.command('highlight default link {0}_Prefix String'
                         .format(self.syntax_name))

        self.vim.command(
            'syntax match {0}_File /{1}/ contained containedin={0}'
            .format(self.syntax_name, r'\v.*({0})@='.format(SEPARATOR)))
        self.vim.command('highlight default link {0}_File String'
                         .format(self.syntax_name))
        self.vim.command(
            'syntax match {0}_Title /{1}/ contained containedin={0}'
            .format(self.syntax_name, r'\v({0})@<=.*'.format(SEPARATOR)))
        self.vim.command('highlight default link {0}_Title Function'
                         .format(self.syntax_name))


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
