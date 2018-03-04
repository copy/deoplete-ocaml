deoplete-ocaml
=

Asynchronous completion for OCaml in vim or neovim using merlin and deoplete.

Status: Experimental, but working well in practice.

Requirements
-

- [merlin](https://github.com/ocaml/merlin)
- [deoplete](https://github.com/Shougo/deoplete.nvim) (see
  [requirements](https://github.com/Shougo/deoplete.nvim#requirements))

Configuration
-

```vim
" enable deoplete
let g:deoplete#enable_at_startup = 1

" this is the default, make sure it is not set to "omnifunc" somewhere else in your vimrc
let g:deoplete#complete_method = "complete"

" other completion sources suggested to disable
let g:deoplete#ignore_sources = {}
let g:deoplete#ignore_sources.ocaml = ['buffer', 'around']

" no delay before completion
let g:deoplete#auto_complete_delay = 0
```
