# vim-denite-memo

The denite source for mattn/memo

![vim-denite-memo](https://raw.githubusercontent.com/delphinus/vim-denite-memo/master/screencast.gif)

## Requirements

This is a denite source for [mattn/memo].  Install and config `memo` before using this source.

[mattn/memo]: https://github.com/mattn/memo

```sh
go get github.com/mattn/memo
# or download binary from the release page.
```

## Install

Put this repo in your `&rtp`s.  You may like to use some package managers such as [Shougo/dein.vim][].

[Shougo/dein.vim]: https://github.com/Shougo/dein.vim

```vim
" in .vimrc
call dein#add('delphinus/vim-denite-memo')
```

## Usage

```vim
" List up all memos
:Denite memo

" List up all memos or create a new one
:Denite memo memo:new

" Search memo
:Denite memo/grep

" Search memo interactively
:Denite memo/grep::!
```
