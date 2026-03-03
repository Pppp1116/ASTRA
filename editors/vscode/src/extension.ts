import * as vscode from 'vscode';
import * as path from 'path';
import { AstraExplorerProvider } from './explorer';

export function activate(context: vscode.ExtensionContext) {
    console.log('Astra extension is now active!');

    // Register tree view provider
    const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    const astraExplorerProvider = new AstraExplorerProvider(workspaceRoot);
    vscode.window.registerTreeDataProvider('astraExplorer', astraExplorerProvider);

    // Register commands
    const runCommand = vscode.commands.registerCommand('astra.runFile', (uri: vscode.Uri) => runAstraFile(uri));
    const buildCommand = vscode.commands.registerCommand('astra.buildFile', (uri: vscode.Uri) => buildAstraFile(uri));
    const checkCommand = vscode.commands.registerCommand('astra.checkFile', (uri: vscode.Uri) => checkAstraFile(uri));
    const formatCommand = vscode.commands.registerCommand('astra.formatFile', (uri: vscode.Uri) => formatAstraFile(uri));
    const docsCommand = vscode.commands.registerCommand('astra.showDocumentation', showDocumentation);
    const playgroundCommand = vscode.commands.registerCommand('astra.openPlayground', openPlayground);
    const refreshCommand = vscode.commands.registerCommand('astra.refreshExplorer', () => astraExplorerProvider.refresh());

    context.subscriptions.push(
        runCommand, 
        buildCommand, 
        checkCommand, 
        formatCommand, 
        docsCommand, 
        playgroundCommand,
        refreshCommand
    );

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
    fileWatcher.onDidChange((uri: vscode.Uri) => {
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
        provideDocumentFormattingEdits(document: vscode.TextDocument): vscode.TextEdit[] {
            return [new vscode.TextEdit(
                new vscode.Range(0, 0, document.lineCount, 0),
                document.getText()
            )];
        }
    });
    context.subscriptions.push(formatProvider);
}

async function startLanguageServer(context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('astra');
    const serverPath = config.get<string>('languageServerPath', 'astlsp');

    try {
        const { LanguageClient } = await import('vscode-languageclient/node');

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

        const client = new LanguageClient(
            'astraLanguageServer',
            'Astra Language Server',
            serverOptions,
            clientOptions
        );

        client.start();
        context.subscriptions.push(client);
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to start language server: ${error}`);
    }
}

async function runAstraFile(uri?: vscode.Uri) {
    const fileUri = uri || getActiveFile();
    if (!fileUri) {
        vscode.window.showErrorMessage('No Astra file selected');
        return;
    }

    const config = vscode.workspace.getConfiguration('astra');
    const target = config.get<string>('build.target', 'py');
    const profile = config.get<string>('build.profile', 'debug');

    const terminal = vscode.window.createTerminal({
        name: 'Astra Run',
        cwd: vscode.Uri.joinPath(fileUri, '..').fsPath
    });

    const command = `astra build "${fileUri.fsPath}" --target ${target} --profile ${profile} && python "${fileUri.fsPath.replace('.astra', '.py')}"`;
    terminal.sendText(command);
    terminal.show();
}

async function buildAstraFile(uri?: vscode.Uri) {
    const fileUri = uri || getActiveFile();
    if (!fileUri) {
        vscode.window.showErrorMessage('No Astra file selected');
        return;
    }

    const config = vscode.workspace.getConfiguration('astra');
    const target = config.get<string>('build.target', 'py');
    const profile = config.get<string>('build.profile', 'debug');

    const terminal = vscode.window.createTerminal({
        name: 'Astra Build',
        cwd: vscode.Uri.joinPath(fileUri, '..').fsPath
    });

    const command = `astra build "${fileUri.fsPath}" --target ${target} --profile ${profile}`;
    terminal.sendText(command);
    terminal.show();
}

async function checkAstraFile(uri?: vscode.Uri) {
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

async function formatAstraFile(uri?: vscode.Uri) {
    const fileUri = uri || getActiveFile();
    if (!fileUri) {
        vscode.window.showErrorMessage('No Astra file selected');
        return;
    }

    await formatDocument(fileUri);
}

async function formatDocument(uri: vscode.Uri) {
    const document = await vscode.workspace.openTextDocument(uri);
    const config = vscode.workspace.getConfiguration('astra');
    
    if (!config.get<boolean>('formatting.enabled', true)) {
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

function getActiveFile(): vscode.Uri | undefined {
    const activeEditor = vscode.window.activeTextEditor;
    if (activeEditor && activeEditor.document.languageId === 'astra') {
        return activeEditor.document.uri;
    }
    return undefined;
}

export function deactivate(): Promise<void> | undefined {
    return undefined;
}
