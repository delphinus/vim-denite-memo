# ============================================================================
# FILE: memo.py
# AUTHOR: delphinus <delphinus@remora.cx>
# License: MIT license
# ============================================================================

from distutils.spawn import find_executable
import re
import subprocess
from unicodedata import east_asian_width, normalize
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
            'ambiwidth': vim.options['ambiwidth'],
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
        to_double = 'FW' if self.vars['ambiwidth'] == 'single' else 'FWA'
        cache = {}

        def east_asian_width_count(char):
            '''
            this func returns 2 if it is Zenkaku string, 1 if other.  Each
            type, 'F', 'W', 'A', means below.

            * F -- Fullwidth
            * W -- Wide
            * A -- Ambiguous
            '''
            if char not in cache:
                cache[char] = 2 if east_asian_width(char) in to_double else 1
            return cache[char]

        # normalize string for filenames in macOS
        norm = normalize('NFC', string)
        slen = sum(east_asian_width_count(x) for x in norm)
        if slen < col:
            return norm + ' ' * (col - slen)
        result = ''
        result_len = 0
        for char in norm:
            next_result = result + char
            next_len = result_len + east_asian_width_count(char)
            if next_len > col - 3:
                return result + ('....' if result_len < col - 3 else '...')
            elif next_len == col - 3:
                return next_result + '...'
            result = next_result
            result_len = next_len

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
