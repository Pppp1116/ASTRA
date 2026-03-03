;;; astra-mode.el --- Major mode for Astra programming language

;; Author: Astra Language Team
;; License: MIT
;; Keywords: languages, astra

;;; Commentary:

;; This package provides a major mode for editing Astra source files.

;;; Code:

(defvar astra-mode-hook nil)

(defvar astra-mode-map
  (let ((map (make-keymap)))
    (define-key map "\C-j" 'newline-and-indent)
    map)
  "Keymap for Astra major mode.")

(defconst astra-font-lock-keywords
  (list
   ;; Keywords - updated with all keywords from lexer
   '("\\<\\(fn\\|let\\|fixed\\|mut\\|return\\|if\\|else\\|while\\|for\\|break\\|continue\\|struct\\|enum\\|type\\|import\\|pub\\|extern\\|async\\|await\\|unsafe\\|impl\\|match\\|defer\\|drop\\|comptime\\|none\\|in\\|as\\|sizeof\\|alignof\\)\\>" . font-lock-keyword-face)
   
   ;; Types
   '("\\<\\(Void\\|Never\\|Bool\\|Int\\|isize\\|usize\\|Float\\|String\\|str\\|Any\\|Vec\\|Option\\)\\>" . font-lock-type-face)
   
   ;; Operators and builtins
   '("\\<\\(as\\|sizeof\\|alignof\\|size_of\\|align_of\\|bitSizeOf\\|maxVal\\|minVal\\)\\>" . font-lock-operator-face)
   
   ;; Boolean literals
   '("\\<\\(true\\|false\\)\\>" . font-lock-constant-face)
   
   ;; None literal
   '("\\<none\\>" . font-lock-constant-face)
   
   ;; Numbers - updated with all formats
   '("\\b\\d+\\b" . font-lock-constant-face)
   '("\\b\\d+\\.\\d+\\b" . font-lock-constant-face)
   '("\\b0x[0-9a-fA-F]+\\b" . font-lock-constant-face)
   '("\\b0b[01]+\\b" . font-lock-constant-face)
   '("\\b\\d+\\(u?\\d+\\|i\\d+\\)\\b" . font-lock-constant-face)
   
   ;; Strings - updated with triple quotes
   '("\"[^\"]*\"" . font-lock-string-face)
   '("'[^']*'" . font-lock-string-face)
   '("\"\"\"[^\"]*\"\"\"" . font-lock-string-face)
   
   ;; Comments - updated with doc comments
   '("//.*" . font-lock-comment-face)
   '("///.*" . font-lock-doc-comment-face)
   '("/\\*.*?\\*/" . font-lock-comment-face)
   
   ;; Attributes
   '("@[a-zA-Z_][a-zA-Z0-9_]*" . font-lock-preprocessor-face)
   
   ;; Multi-character operators
   '("&&=\\||=\\|\\.\\.\\.\\|::\\|=>\\|->\\|==\\|!=\\|<=\\|>=\\|&&\\|||\\|??\\|+=\\|-=" . font-lock-operator-face)
   '("\\*=\\|/=\\|%=\\|<<=\\|>>=\\|&=\\||=\\|^=\\|<<\\|>>\\|\\.\\." . font-lock-operator-face)
   
   ;; Functions
   '("\\<[a-z_][a-zA-Z0-9_]*\\s*\\ze(" . font-lock-function-name-face)
   
   ;; Variables
   '("\\<[a-z_][a-zA-Z0-9_]*\\>" . font-lock-variable-name-face)
   
   ;; Generic types
   '("<\\|>" . font-lock-special))
  "Font lock keywords for Astra mode.")

(defvar astra-mode-syntax-table
  (let ((st (make-syntax-table)))
    ;; Comments
    (modify-syntax-entry ?/ ". 124b" st)
    (modify-syntax-entry ?* ". 23" st)
    (modify-syntax-entry ?\n "> b" st)
    
    ;; Strings
    (modify-syntax-entry ?\" "\"" st)
    (modify-syntax-entry ?\\ "\\" st)
    
    ;; Delimiters
    (modify-syntax-entry ?\( "()" st)
    (modify-syntax-entry ?\) ")(" st)
    (modify-syntax-entry ?\[ "(]" st)
    (modify-syntax-entry ?\] ")[" st)
    (modify-syntax-entry ?\{ "(}" st)
    (modify-syntax-entry ?\} "){" st)
    
    st)
  "Syntax table for Astra mode.")

(defun astra-indent-line ()
  "Indent current line as Astra code."
  (interactive)
  (let ((save-pos (point)))
    (beginning-of-line)
    (if (bobp)
        (indent-line-to 0)
      (let ((indent (calculate-astra-indent)))
        (indent-line-to indent)))
    (if (< (point) save-pos)
        (goto-char save-pos))))

(defun calculate-astra-indent ()
  "Calculate appropriate indentation for current line."
  (let ((current-indent 0)
        (cur-pos (point))
        (in-brace 0)
        (in-paren 0))
    (save-excursion
      (beginning-of-line)
      (while (> (point) 1)
        (backward-char 1)
        (cond
         ((looking-at "{") (setq in-brace (1+ in-brace)))
         ((looking-at "}") (setq in-brace (1- in-brace)))
         ((looking-at "(") (setq in-paren (1+ in-paren)))
         ((looking-at ")") (setq in-paren (1- in-paren)))))
      
      (goto-char cur-pos)
      (beginning-of-line)
      (back-to-indentation)
      (setq current-indent (* (max in-brace in-paren) tab-width)))
    current-indent))

;;;###autoload
(define-derived-mode astra-mode prog-mode "Astra"
  "Major mode for editing Astra programming language files."
  (set-syntax-table astra-mode-syntax-table)
  (set (make-local-variable 'font-lock-defaults) '(astra-font-lock-keywords))
  (set (make-local-variable 'indent-line-function) 'astra-indent-line)
  (setq mode-name "Astra")
  (run-hooks 'astra-mode-hook))

;;;###autoload
(add-to-list 'auto-mode-alist '("\\.astra\\'" . astra-mode))

(provide 'astra-mode)

;;; astra-mode.el ends here
