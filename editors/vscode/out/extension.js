"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const explorer_1 = require("./explorer");
function activate(context) {
    console.log('Astra extension is now active!');
    // Register tree view provider
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    const astraExplorerProvider = new explorer_1.AstraExplorerProvider(workspaceRoot);
    vscode.window.registerTreeDataProvider('astraExplorer', astraExplorerProvider);
    // Register commands
    const runCommand = vscode.commands.registerCommand('astra.runFile', (uri) => runAstraFile(uri));
    const buildCommand = vscode.commands.registerCommand('astra.buildFile', (uri) => buildAstraFile(uri));
    const checkCommand = vscode.commands.registerCommand('astra.checkFile', (uri) => checkAstraFile(uri));
    const formatCommand = vscode.commands.registerCommand('astra.formatFile', (uri) => formatAstraFile(uri));
    const docsCommand = vscode.commands.registerCommand('astra.showDocumentation', showDocumentation);
    const playgroundCommand = vscode.commands.registerCommand('astra.openPlayground', openPlayground);
    const refreshCommand = vscode.commands.registerCommand('astra.refreshExplorer', () => astraExplorerProvider.refresh());
    context.subscriptions.push(runCommand, buildCommand, checkCommand, formatCommand, docsCommand, playgroundCommand, refreshCommand);
    // Start language server
    startLanguageServer(context);
    // Register status bar item
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.text = '$(gear) Astra';
    statusBarItem.tooltip = 'Astra Language Server';
    statusBarItem.command = 'astra.showDocumentation';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);
    // Register file watcher for build system
    const fileWatcher = vscode.workspace.createFileSystemWatcher('**/*.astra');
    fileWatcher.onDidChange((uri) => {
        if (vscode.workspace.getConfiguration('astra').get('formatting.onSave')) {
            formatDocument(uri);
        }
        astraExplorerProvider.refresh();
    });
    fileWatcher.onDidCreate(() => astraExplorerProvider.refresh());
    fileWatcher.onDidDelete(() => astraExplorerProvider.refresh());
    context.subscriptions.push(fileWatcher);
    // Register formatting provider
    const formatProvider = vscode.languages.registerDocumentFormattingEditProvider('astra', {
        provideDocumentFormattingEdits(document) {
            return [new vscode.TextEdit(new vscode.Range(0, 0, document.lineCount, 0), document.getText())];
        }
    });
    context.subscriptions.push(formatProvider);
}
async function startLanguageServer(context) {
    const config = vscode.workspace.getConfiguration('astra');
    const serverPath = config.get('languageServerPath', 'astlsp');
    try {
        const { LanguageClient } = await Promise.resolve().then(() => __importStar(require('vscode-languageclient/node')));
        const serverOptions = {
            command: serverPath,
            args: []
        };
        const clientOptions = {
            documentSelector: [{ scheme: 'file', language: 'astra' }],
            synchronize: {
                fileEvents: vscode.workspace.createFileSystemWatcher('**/*.astra')
            },
            outputChannel: vscode.window.createOutputChannel('Astra Language Server')
        };
        const client = new LanguageClient('astraLanguageServer', 'Astra Language Server', serverOptions, clientOptions);
        client.start();
        context.subscriptions.push(client);
    }
    catch (error) {
        vscode.window.showErrorMessage(`Failed to start language server: ${error}`);
    }
}
async function runAstraFile(uri) {
    const fileUri = uri || getActiveFile();
    if (!fileUri) {
        vscode.window.showErrorMessage('No Astra file selected');
        return;
    }
    const config = vscode.workspace.getConfiguration('astra');
    const target = config.get('build.target', 'py');
    const profile = config.get('build.profile', 'debug');
    const terminal = vscode.window.createTerminal({
        name: 'Astra Run',
        cwd: vscode.Uri.joinPath(fileUri, '..').fsPath
    });
    const command = `astra build "${fileUri.fsPath}" --target ${target} --profile ${profile} && python "${fileUri.fsPath.replace('.astra', '.py')}"`;
    terminal.sendText(command);
    terminal.show();
}
async function buildAstraFile(uri) {
    const fileUri = uri || getActiveFile();
    if (!fileUri) {
        vscode.window.showErrorMessage('No Astra file selected');
        return;
    }
    const config = vscode.workspace.getConfiguration('astra');
    const target = config.get('build.target', 'py');
    const profile = config.get('build.profile', 'debug');
    const terminal = vscode.window.createTerminal({
        name: 'Astra Build',
        cwd: vscode.Uri.joinPath(fileUri, '..').fsPath
    });
    const command = `astra build "${fileUri.fsPath}" --target ${target} --profile ${profile}`;
    terminal.sendText(command);
    terminal.show();
}
async function checkAstraFile(uri) {
    const fileUri = uri || getActiveFile();
    if (!fileUri) {
        vscode.window.showErrorMessage('No Astra file selected');
        return;
    }
    const terminal = vscode.window.createTerminal({
        name: 'Astra Check',
        cwd: vscode.Uri.joinPath(fileUri, '..').fsPath
    });
    const command = `astra check "${fileUri.fsPath}"`;
    terminal.sendText(command);
    terminal.show();
}
async function formatAstraFile(uri) {
    const fileUri = uri || getActiveFile();
    if (!fileUri) {
        vscode.window.showErrorMessage('No Astra file selected');
        return;
    }
    await formatDocument(fileUri);
}
async function formatDocument(uri) {
    const document = await vscode.workspace.openTextDocument(uri);
    const config = vscode.workspace.getConfiguration('astra');
    if (!config.get('formatting.enabled', true)) {
        return;
    }
    const terminal = vscode.window.createTerminal({
        name: 'Astra Format',
        cwd: vscode.Uri.joinPath(uri, '..').fsPath
    });
    const command = `astfmt "${uri.fsPath}"`;
    terminal.sendText(command);
    // Wait a moment for formatting to complete, then reload the document
    setTimeout(async () => {
        await document.save();
        terminal.dispose();
    }, 1000);
}
function showDocumentation() {
    const docsUrl = 'https://github.com/Pppp1116/ASTRA/blob/main/docs/TOUR.md';
    vscode.env.openExternal(vscode.Uri.parse(docsUrl));
}
function openPlayground() {
    const playgroundUrl = 'https://astra-lang.github.io/playground';
    vscode.env.openExternal(vscode.Uri.parse(playgroundUrl));
}
function getActiveFile() {
    const activeEditor = vscode.window.activeTextEditor;
    if (activeEditor && activeEditor.document.languageId === 'astra') {
        return activeEditor.document.uri;
    }
    return undefined;
}
function deactivate() {
    return undefined;
}
//# sourceMappingURL=extension.js.map