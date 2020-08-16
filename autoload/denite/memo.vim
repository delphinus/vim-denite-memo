let g:denite_memo_executable = get(g:, 'denite_memo_executable', 'memo')

function denite#memo#executable() abort
  if executable(g:denite_memo_executable)
    return g:denite_memo_executable
  endif
  call denite#util#print_error('cannot find `memo` executable. See :h g:denite_memo_executable')
  return v:null
endfunction

function denite#memo#get_dir() abort
  let out = system(g:denite_memo_executable . ' config --cat')
  let dir = matchstr(out, '\_^memodir = "\zs.\{-1,}\ze"')
  if dir ==# ''
    call denite#util#print_error('cannot get memodir')
    return v:null
  endif
  return dir
endfunction
