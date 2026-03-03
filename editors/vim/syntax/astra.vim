" Vim syntax highlighting for Astra language
" Author: Astra Language Team
" License: MIT

if exists("b:current_syntax")
    finish
endif

syn case match

" Keywords
syn keyword astraKeyword fn let fixed mut return if else while for break continue
syn keyword astraKeyword struct enum type import pub extern async await unsafe match drop defer
syn keyword astraKeyword comptime none in as sizeof alignof impl

" Types
syn keyword astraType Void Never Bool Int isize usize Float String str Any
syn keyword astraType Vec Option

" Operators
syn keyword astraOperator as sizeof alignof

" Literals
syn keyword astraBoolean true false
syn keyword astraNone none

" Numbers
syn match astraNumber "\v<\d+>"
syn match astraNumber "\v<\d+\.\d+>"
syn match astraNumber "\v<0x[0-9a-fA-F]+>"
syn match astraNumber "\v<0b[01]+>"
syn match astraNumber "\v<\d+(u?\d+|i\d+)>"

" Strings
syn region astraString start=+"+ skip=+\\\\|\\\"+ end=+"+
syn region astraString start=+'+ skip=+\\\\|\\\'+ end=+'+
syn region astraString start=+\"\"\"+ skip=+\\\\|\\\"+ end=+\"\"\"+

" Comments
syn keyword astraTodo TODO FIXME NOTE XXX contained
syn match astraComment "//.*" contains=astraTodo
syn region astraComment start="/\\*" end="\\*/" contains=astraTodo
syn match astraDocComment "///.*" contains=astraTodo

" Attributes
syn match astraAttribute "@\\w+"

" Punctuation
syn match astraDelimiter "[,;:]"
syn match astraBrace "[{}\\[\\]]"
syn match astraParen "[()]"

" Multi-character operators
syn match astraOperator "&&=\||=\|\.\.\.\|::\|=>\|->\|==\|!=\|<=\|>=\|&&\|||\|??\|+=\|-="
syn match astraOperator "\*=\|/=\|%=\|<<=\|>>=\|&=\||=\|^=\|<<\|>>\|\.\."

" Functions
syn match astraFunction "\v<[a-z_][a-zA-Z0-9_]*\\s*\\ze("

" Variables
syn match astraIdentifier "\v<[a-z_][a-zA-Z0-9_]*>"

" Generic types
syn match astraGeneric "<\|>"

" Layout queries
syn match astraBuiltin "\\v<(sizeof|alignof|size_of|align_of|bitSizeOf|maxVal|minVal)>"

" Define the default highlighting
hi def link astraKeyword Keyword
hi def link astraType Type
hi def link astraOperator Operator
hi def link astraBoolean Boolean
hi def link astraNone Constant
hi def link astraNumber Number
hi def link astraString String
hi def link astraComment Comment
hi def link astraDocComment SpecialComment
hi def link astraTodo Todo
hi def link astraAttribute PreProc
hi def link astraDelimiter Delimiter
hi def link astraBrace Delimiter
hi def link astraParen Delimiter
hi def link astraFunction Function
hi def link astraIdentifier Identifier
hi def link astraGeneric Special
hi def link astraBuiltin Special

let b:current_syntax = "astra"
