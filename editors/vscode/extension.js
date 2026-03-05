const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const vscode = require('vscode');
const { LanguageClient, State, Trace } = require('vscode-languageclient/node');

/** @type {LanguageClient | undefined} */
let client;
/** @type {vscode.OutputChannel | undefined} */
let output;
/** @type {vscode.StatusBarItem | undefined} */
let statusBar;
/** @type {{mode: string, command: string, args: string[]} | undefined} */
let currentServer;

function getConfig() {
  return vscode.workspace.getConfiguration('astra');
}

function ensureOutput(context) {
  if (!output) {
    output = vscode.window.createOutputChannel('Astra');
    context.subscriptions.push(output);
  }
  return output;
}

function ensureStatusBar(context) {
  if (!statusBar) {
    statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 40);
    statusBar.name = 'Astra Language Server';
    statusBar.command = 'astra.showLanguageServerStatus';
    statusBar.text = '$(sync~spin) Astra: starting';
    statusBar.tooltip = 'Astra language server';
    statusBar.show();
    context.subscriptions.push(statusBar);
  }
  return statusBar;
}

function setStatus(text, tooltip) {
  if (!statusBar) {
    return;
  }
  statusBar.text = text;
  statusBar.tooltip = tooltip;
}

function mapTrace(value) {
  if (value === 'verbose') {
    return Trace.Verbose;
  }
  if (value === 'messages') {
    return Trace.Messages;
  }
  return Trace.Off;
}

function checkCommand(command, args) {
  const probe = spawnSync(command, [...args, '--version'], { encoding: 'utf8' });
  return probe.status === 0;
}

function findPython(overridePath) {
  if (overridePath) {
    return { command: overridePath, prefixArgs: [] };
  }

  const candidates = process.platform === 'win32'
    ? [
        { command: 'py', prefixArgs: ['-3'] },
        { command: 'python', prefixArgs: [] },
        { command: 'python3', prefixArgs: [] }
      ]
    : [
        { command: 'python3', prefixArgs: [] },
        { command: 'python', prefixArgs: [] }
      ];

  for (const candidate of candidates) {
    if (checkCommand(candidate.command, candidate.prefixArgs)) {
      return candidate;
    }
  }
  return undefined;
}

function bundledServer(context) {
  const config = getConfig();
  const override = config.get('languageServer.pythonPath', '').trim();
  const python = findPython(override);
  if (!python) {
    return undefined;
  }

  const script = path.join(context.extensionPath, 'server', 'run_lsp.py');
  const stdlibPath = path.join(context.extensionPath, 'server', 'astra', 'stdlib');
  if (!fs.existsSync(script) || !fs.existsSync(stdlibPath)) {
    return undefined;
  }

  return {
    command: python.command,
    args: [...python.prefixArgs, script],
    options: {
      env: {
        ...process.env,
        ASTRA_STDLIB_PATH: stdlibPath
      }
    }
  };
}

function externalServer() {
  const config = getConfig();
  const command = config.get('languageServer.command', '').trim();
  const args = config.get('languageServer.args', []);
  if (!command) {
    return undefined;
  }
  return { command, args };
}

function resolveServer(context) {
  const config = getConfig();
  const mode = config.get('languageServer.mode', 'bundled');

  if (mode === 'external') {
    const external = externalServer();
    if (external) {
      currentServer = { mode: 'external', command: external.command, args: external.args || [] };
      return external;
    }
    throw new Error('Astra is configured for external server mode, but astra.languageServer.command is empty.');
  }

  const bundled = bundledServer(context);
  if (bundled) {
    currentServer = { mode: 'bundled', command: bundled.command, args: bundled.args || [] };
    return bundled;
  }

  const external = externalServer();
  if (external) {
    currentServer = { mode: 'external-fallback', command: external.command, args: external.args || [] };
    return external;
  }

  throw new Error('Could not start bundled Astra server. Install Python 3.11+ or set astra.languageServer.command.');
}

function attachClientStateLogging() {
  if (!client || !output) {
    return;
  }
  client.onDidChangeState((event) => {
    output.appendLine(`state: ${event.oldState} -> ${event.newState}`);
    if (event.newState === State.Running) {
      setStatus('$(check) Astra: ready', 'Astra language server is running');
    } else {
      setStatus('$(warning) Astra: stopped', 'Astra language server is not running');
    }
  });
}

async function startClient(context) {
  const channel = ensureOutput(context);
  ensureStatusBar(context);
  setStatus('$(sync~spin) Astra: starting', 'Starting Astra language server');

  const executable = resolveServer(context);
  channel.appendLine(`starting server (${currentServer.mode}): ${executable.command} ${(executable.args || []).join(' ')}`);

  const serverOptions = {
    run: executable,
    debug: executable
  };

  const clientOptions = {
    documentSelector: [
      { scheme: 'file', language: 'astra' },
      { scheme: 'untitled', language: 'astra' }
    ],
    outputChannel: channel,
    synchronize: {
      fileEvents: vscode.workspace.createFileSystemWatcher('**/*.astra')
    }
  };

  client = new LanguageClient('astra-lsp', 'Astra Language Server', serverOptions, clientOptions);
  client.setTrace(mapTrace(getConfig().get('trace.server', 'off')));
  attachClientStateLogging();
  context.subscriptions.push(client.start());
}

async function stopClient() {
  if (!client) {
    return;
  }
  const current = client;
  client = undefined;
  await current.stop();
}

async function restartClient(context) {
  await stopClient();
  await startClient(context);
  void vscode.window.showInformationMessage('Astra language server restarted.');
}

function formatServerStatus() {
  if (!currentServer) {
    return 'Astra server: not started yet';
  }
  return [
    `Mode: ${currentServer.mode}`,
    `Command: ${currentServer.command}`,
    `Args: ${currentServer.args.join(' ') || '(none)'}`
  ].join('\n');
}

async function activate(context) {
  ensureOutput(context);
  ensureStatusBar(context);

  const restartDisposable = vscode.commands.registerCommand('astra.restartLanguageServer', async () => {
    try {
      await restartClient(context);
    } catch (error) {
      setStatus('$(error) Astra: failed', 'Astra language server failed to start');
      void vscode.window.showErrorMessage(`Astra restart failed: ${String(error)}`);
    }
  });
  context.subscriptions.push(restartDisposable);

  const statusDisposable = vscode.commands.registerCommand('astra.showLanguageServerStatus', async () => {
    const choice = await vscode.window.showInformationMessage(formatServerStatus(), 'Restart', 'Open Log');
    if (choice === 'Restart') {
      await vscode.commands.executeCommand('astra.restartLanguageServer');
      return;
    }
    if (choice === 'Open Log' && output) {
      output.show(true);
    }
  });
  context.subscriptions.push(statusDisposable);

  const openLogDisposable = vscode.commands.registerCommand('astra.openExtensionLog', async () => {
    if (output) {
      output.show(true);
    }
  });
  context.subscriptions.push(openLogDisposable);

  const configDisposable = vscode.workspace.onDidChangeConfiguration(async (event) => {
    if (
      event.affectsConfiguration('astra.languageServer.mode') ||
      event.affectsConfiguration('astra.languageServer.command') ||
      event.affectsConfiguration('astra.languageServer.pythonPath') ||
      event.affectsConfiguration('astra.languageServer.args') ||
      event.affectsConfiguration('astra.trace.server')
    ) {
      try {
        await restartClient(context);
      } catch (error) {
        setStatus('$(error) Astra: failed', 'Astra language server failed to start');
        void vscode.window.showErrorMessage(`Astra configuration update failed: ${String(error)}`);
      }
    }
  });
  context.subscriptions.push(configDisposable);

  try {
    await startClient(context);
  } catch (error) {
    setStatus('$(error) Astra: failed', 'Astra language server failed to start');
    void vscode.window.showErrorMessage(`Astra language server failed to start: ${String(error)}`);
  }
}

async function deactivate() {
  await stopClient();
}

module.exports = {
  activate,
  deactivate
};
