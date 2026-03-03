# Astra VS Code Extension

A comprehensive VS Code extension for the Astra programming language, providing syntax highlighting, IntelliSense, debugging, and build integration.

## Features

### 🎨 Syntax Highlighting
- Full syntax highlighting for Astra language constructs
- Support for keywords, types, strings, numbers, and operators
- Bracket matching and auto-closing pairs

### 🔧 Language Server Integration
- **Code Completion**: Intelligent auto-completion for keywords, functions, and variables
- **Hover Information**: Type information and documentation on hover
- **Go to Definition**: Navigate to function and variable definitions
- **Error Diagnostics**: Real-time error checking and highlighting
- **Code Actions**: Quick fixes and refactoring suggestions

### 🛠️ Build Integration
- **Run File**: Execute Astra files with Ctrl+F5
- **Build File**: Compile Astra files with Ctrl+Shift+B
- **Check File**: Validate syntax and semantics with Ctrl+Shift+C
- **Format File**: Format code with Ctrl+Shift+I
- **Multiple Targets**: Support for Python, LLVM, and Native compilation

### 🐛 Debugging Support
- **Breakpoints**: Set and manage breakpoints
- **Variable Inspection**: View and modify variables during debugging
- **Call Stack**: Navigate the call stack
- **Step Execution**: Step over, into, and out of code
- **Expression Evaluation**: Evaluate expressions in the debug console

### 📁 Project Explorer
- **File Tree**: Navigate Astra files in your workspace
- **Quick Actions**: Right-click context menu for common operations
- **Auto-refresh**: Explorer updates when files change

### ⚙️ Configuration Options

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

## Installation

### From Marketplace
1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "Astra Language"
4. Click Install

### From Source
1. Clone this repository
2. Install dependencies: `npm install`
3. Compile TypeScript: `npm run compile`
4. Install the extension in VS Code

## Development

### Prerequisites
- Node.js 18+
- TypeScript 5.3+
- VS Code 1.85+

### Building
```bash
# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Watch for changes
npm run watch

# Run tests
npm test

# Lint code
npm run lint
```

### Debugging
1. Open the extension in VS Code
2. Press F5 to launch a new Extension Development Host
3. Test the extension in the new window

## Architecture

### Extension Structure
```
src/
├── extension.ts      # Main extension entry point
├── explorer.ts       # Project tree view provider
├── debugAdapter.ts   # Debug adapter implementation
└── test/           # Extension tests
```

### Key Components

#### Language Client
- Communicates with the Astra Language Server (`astlsp`)
- Provides IntelliSense features
- Handles diagnostics and code actions

#### Debug Adapter
- Implements VS Code Debug Protocol
- Manages debugging sessions
- Handles breakpoints and variable inspection

#### Tree View Provider
- Shows Astra files in workspace
- Provides quick access to common operations
- Updates automatically with file changes

## Language Server Features

The extension integrates with the existing Astra Language Server (`astra/lsp.py`) which provides:

- **Parsing**: Full AST parsing for Astra files
- **Semantic Analysis**: Type checking and validation
- **Symbol Resolution**: Function and variable lookup
- **Error Reporting**: Detailed error messages with locations
- **Completion**: Context-aware suggestions

## Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| `astra.runFile` | Ctrl+F5 | Run current Astra file |
| `astra.buildFile` | Ctrl+Shift+B | Build current Astra file |
| `astra.checkFile` | Ctrl+Shift+C | Check current Astra file |
| `astra.formatFile` | Ctrl+Shift+I | Format current Astra file |
| `astra.showDocumentation` | - | Open Astra documentation |
| `astra.openPlayground` | - | Open online playground |
| `astra.refreshExplorer` | - | Refresh file explorer |

## Configuration

### Language Server Path
Set the path to the Astra Language Server executable:
```json
"astra.languageServerPath": "/path/to/astlsp"
```

### Build Configuration
Configure default build settings:
```json
"astra.build.target": "py",        // "py", "llvm", or "native"
"astra.build.profile": "debug"      // "debug" or "release"
```

### Formatting
Enable automatic formatting:
```json
"astra.formatting.enabled": true,
"astra.formatting.onSave": false
```

## Troubleshooting

### Language Server Not Starting
1. Check that `astlsp` is installed and in your PATH
2. Verify the language server path in settings
3. Check the output panel for error messages

### Debugging Issues
1. Ensure the Astra compiler is installed
2. Check that build targets are properly configured
3. Verify file permissions for output directories

### Performance Issues
1. Disable advanced diagnostics if not needed
2. Exclude large directories from workspace
3. Use file watchers selectively

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
