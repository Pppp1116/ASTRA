# IDE and Code Editor Integration for ASTRA

This directory contains editor integrations for the Astra programming language, providing syntax highlighting, IntelliSense, debugging, and build integration across multiple development environments.

## 📁 Directory Structure

```
editors/
├── vscode/          # VS Code extension
│   ├── src/         # TypeScript source files
│   ├── syntaxes/    # TextMate grammar files
│   ├── snippets/     # Code snippets
│   └── package.json # Extension manifest
├── vim/             # Vim integration
│   ├── syntax/       # Syntax highlighting
│   └── ftdetect/    # File type detection
└── emacs/           # Emacs integration
    └── astra-mode.el # Major mode
```

## 🚀 Quick Start

### VS Code
1. Install the Astra extension from the VS Code Marketplace
2. Open any `.astra` file to start using the extension
3. Use `Ctrl+F5` to run files, `Ctrl+Shift+B` to build

### Vim
1. Copy the `vim/` directory to your `~/.vim/` directory:
   ```bash
   cp -r editors/vim/* ~/.vim/
   ```
2. Restart Vim or run `:syntax on`
3. Open `.astra` files for syntax highlighting

### Emacs
1. Add the Emacs mode to your load path:
   ```elisp
   (add-to-list 'load-path "/path/to/editors/emacs")
   ```
2. Load the mode:
   ```elisp
   (require 'astra-mode)
   ```
3. Open `.astra` files to use Astra mode

## ✨ Features

### VS Code Extension
- **Syntax Highlighting**: Full TextMate grammar with comprehensive language support
- **Language Server**: Integration with `astlsp` for IntelliSense features
- **Code Completion**: Context-aware suggestions for keywords, functions, and variables
- **Error Diagnostics**: Real-time error checking and highlighting
- **Debugging**: Full debugging support with breakpoints and variable inspection
- **Build Integration**: Run, build, check, and format commands
- **Project Explorer**: Tree view for navigating Astra files
- **Snippets**: Common code patterns and templates

### Vim Integration
- **Syntax Highlighting**: Comprehensive syntax definitions
- **File Detection**: Automatic `.astra` file recognition
- **Keyword Highlighting**: Language keywords, types, and operators
- **Comment Support**: Single-line and multi-line comment highlighting

### Emacs Integration
- **Major Mode**: Dedicated `astra-mode` for Astra files
- **Font Lock**: Syntax highlighting for all language constructs
- **Indentation**: Smart indentation for code blocks
- **Auto-detection**: Automatic mode activation for `.astra` files

## 🔧 Configuration

### VS Code Settings
```json
{
  "astra.languageServerPath": "astlsp",
  "astra.enableAdvancedDiagnostics": true,
  "astra.formatting.enabled": true,
  "astra.formatting.onSave": false,
  "astra.build.target": "py",
  "astra.build.profile": "debug",
  "astra.debug.enabled": true
}
```

### Vim Configuration
Add to your `.vimrc`:
```vim
" Enable Astra syntax highlighting
syntax on
filetype plugin indent on

" Optional: Custom highlighting colors
highlight astraKeyword ctermfg=blue guifg=blue
highlight astraType ctermfg=green guifg=green
```

### Emacs Configuration
Add to your `init.el`:
```elisp
;; Enable Astra mode
(require 'astra-mode)

;; Optional: Custom keybindings
(add-hook 'astra-mode-hook
          (lambda ()
            (local-set-key (kbd "C-c C-c") 'compile)
            (local-set-key (kbd "C-c C-r") 'recompile)))
```

## 🎯 Language Server Protocol (LSP)

The ASTRA language server (`astlsp`) provides:

### Core Features
- **Parsing**: Full AST parsing for Astra files
- **Semantic Analysis**: Type checking and validation
- **Symbol Resolution**: Function and variable lookup
- **Error Reporting**: Detailed error messages with locations

### LSP Capabilities
- **Text Document Sync**: Real-time file synchronization
- **Hover**: Type information and documentation on hover
- **Completion**: Context-aware code completion
- **Definition**: Go to definition functionality
- **Diagnostics**: Real-time error checking

### Supported Editors
- VS Code (via extension)
- Vim/Neovim (via `coc.nvim` or `nvim-lspconfig`)
- Emacs (via `lsp-mode`)
- Sublime Text (via LSP package)
- Atom (via `ide-astra` package)

## 🐛 Debugging Support

### VS Code Debugger
- **Breakpoints**: Set and manage breakpoints
- **Variable Inspection**: View and modify variables
- **Call Stack**: Navigate the call stack
- **Step Execution**: Step over, into, and out of code
- **Expression Evaluation**: Evaluate expressions in debug console

### Debug Configuration
```json
{
  "type": "astra",
  "request": "launch",
  "name": "Debug Astra File",
  "program": "${workspaceFolder}/${input:fileName}",
  "target": "py",
  "stopOnEntry": false
}
```

## 🛠️ Build Integration

### Supported Targets
- **Python**: Compile to Python bytecode
- **LLVM**: Generate LLVM IR
- **Native**: Compile to native executables

### Build Commands
- `astra build <file> --target py`: Build to Python
- `astra build <file> --target llvm`: Build to LLVM IR
- `astra build <file> --target native`: Build to native
- `astra check <file>`: Check syntax and semantics
- `astfmt <file>`: Format source code

## 📝 Development

### VS Code Extension Development
```bash
cd editors/vscode
npm install
npm run compile
npm run watch  # Development mode
npm test        # Run tests
npm run lint    # Lint code
```

### Testing Language Server
```bash
# Start language server
astlsp

# Test with VS Code
code --extensionDevelopmentPath=editors/vscode
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📚 Additional Resources

- **Language Specification**: `docs/SPEC.md`
- **Language Tour**: `docs/TOUR.md`
- **Diagnostics Reference**: `docs/DIAGNOSTICS.md`
- **Standard Library**: `stdlib/`
- **Runtime**: `runtime/`

## 🤝 Community

- **Issues**: Report bugs and request features
- **Discussions**: Community discussions and Q&A
- **Contributing**: See `CONTRIBUTING.md` for guidelines

## 📄 License

All editor integrations are licensed under the MIT License. See the LICENSE file for details.
