/**
 * Profiler UI Components for VS Code
 * Provides visual interface for Astra performance profiling
 */

const vscode = require('vscode');
const path = require('path');

class ProfilerUI {
    constructor(context) {
        this.context = context;
        this.panel = null;
        this.currentProfile = null;
        this.disposables = [];
    }

    /**
     * Show profiler panel
     */
    showProfilerPanel() {
        if (this.panel) {
            this.panel.reveal();
            return;
        }

        this.panel = vscode.window.createWebviewPanel(
            'astraProfiler',
            'Astra Profiler',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(this.context.extensionUri, 'profiler')
                ]
            }
        );

        this.panel.onDidDispose(() => {
            this.panel = null;
        });

        this.panel.webview.html = this.getProfilerWebviewContent();

        // Handle messages from webview
        this.panel.webview.onDidReceiveMessage(
            message => this.handleWebviewMessage(message),
            undefined,
            this.disposables
        );
    }

    /**
     * Update profiler with new data
     */
    updateProfile(profileData) {
        this.currentProfile = profileData;
        
        if (this.panel) {
            this.panel.webview.postMessage({
                type: 'profileUpdate',
                data: profileData
            });
        }
    }

    /**
     * Handle webview messages
     */
    async handleWebviewMessage(message) {
        switch (message.type) {
            case 'startProfiling':
                await this.startProfiling(message.data);
                break;
            case 'stopProfiling':
                await this.stopProfiling();
                break;
            case 'exportProfile':
                await this.exportProfile(message.data);
                break;
            case 'showHotspot':
                await this.showHotspot(message.data);
                break;
            case 'applyOptimization':
                await this.applyOptimization(message.data);
                break;
        }
    }

    /**
     * Start profiling
     */
    async startProfiling(options) {
        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor found');
                return;
            }

            const filePath = editor.document.uri.fsPath;
            const target = options.target || 'native';

            // Send command to start profiling
            const result = await vscode.commands.executeCommand('astra.startProfiling', {
                file: filePath,
                target: target
            });

            if (result.success) {
                vscode.window.showInformationMessage('Profiling started');
                this.panel.webview.postMessage({
                    type: 'profilingStarted',
                    data: { file: filePath, target: target }
                });
            } else {
                vscode.window.showErrorMessage(`Failed to start profiling: ${result.error}`);
            }

        } catch (error) {
            vscode.window.showErrorMessage(`Profiling error: ${error.message}`);
        }
    }

    /**
     * Stop profiling
     */
    async stopProfiling() {
        try {
            const result = await vscode.commands.executeCommand('astra.stopProfiling');

            if (result.success) {
                this.updateProfile(result.profile);
                vscode.window.showInformationMessage('Profiling completed');
                this.panel.webview.postMessage({
                    type: 'profilingStopped',
                    data: result.profile
                });
            } else {
                vscode.window.showErrorMessage(`Failed to stop profiling: ${result.error}`);
            }

        } catch (error) {
            vscode.window.showErrorMessage(`Profiling error: ${error.message}`);
        }
    }

    /**
     * Export profile data
     */
    async exportProfile(format) {
        if (!this.currentProfile) {
            vscode.window.showErrorMessage('No profile data to export');
            return;
        }

        try {
            const uri = await vscode.window.showSaveDialog({
                defaultUri: vscode.Uri.file('astra-profile.json'),
                filters: {
                    'JSON Files': ['json'],
                    'Text Files': ['txt']
                }
            });

            if (uri) {
                const content = format === 'json' 
                    ? JSON.stringify(this.currentProfile, null, 2)
                    : this.formatProfileAsText(this.currentProfile);

                await vscode.workspace.fs.writeFile(uri, Buffer.from(content, 'utf8'));
                vscode.window.showInformationMessage(`Profile exported to ${uri.fsPath}`);
            }

        } catch (error) {
            vscode.window.showErrorMessage(`Export error: ${error.message}`);
        }
    }

    /**
     * Show hotspot in editor
     */
    async showHotspot(hotspot) {
        try {
            const uri = vscode.Uri.file(hotspot.file);
            const document = await vscode.workspace.openTextDocument(uri);
            const editor = await vscode.window.showTextDocument(document);

            const line = hotspot.line - 1; // VS Code uses 0-based indexing
            const range = new vscode.Range(line, 0, line, 100);
            
            editor.selection = new vscode.Selection(range.start, range.end);
            editor.revealRange(range, vscode.TextEditorRevealType.InCenter);

        } catch (error) {
            vscode.window.showErrorMessage(`Failed to show hotspot: ${error.message}`);
        }
    }

    /**
     * Apply optimization suggestion
     */
    async applyOptimization(suggestion) {
        try {
            // This would implement code modifications based on suggestions
            vscode.window.showInformationMessage(
                `Optimization suggestion: ${suggestion.title}`,
                'Apply'
            ).then(async (action) => {
                if (action === 'Apply') {
                    // Apply the optimization
                    await this.applyCodeOptimization(suggestion);
                }
            });

        } catch (error) {
            vscode.window.showErrorMessage(`Failed to apply optimization: ${error.message}`);
        }
    }

    /**
     * Apply code optimization
     */
    async applyCodeOptimization(suggestion) {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor');
            return;
        }

        // This would implement actual code modifications
        // For now, just show a placeholder
        const edit = new vscode.WorkspaceEdit();
        const position = editor.selection.active;
        
        edit.insert(
            editor.document.uri,
            position,
            `// Optimization: ${suggestion.title}\n`
        );

        await vscode.workspace.applyEdit(edit);
        vscode.window.showInformationMessage('Optimization applied');
    }

    /**
     * Format profile as text
     */
    formatProfileAsText(profile) {
        const summary = profile.summary || {};
        const metrics = profile.performance_metrics || {};
        const hotspots = profile.hotspots || [];
        const suggestions = profile.optimization_suggestions || [];

        let text = `=== Astra Profile Results ===\n`;
        text += `Total time: ${summary.total_time_seconds?.toFixed(2)}s\n`;
        text += `Target: ${summary.target}\n`;
        text += `Samples: ${summary.sample_count}\n\n`;

        const cpu = metrics.cpu || {};
        text += `CPU Usage:\n`;
        text += `  Average: ${cpu.average_percent?.toFixed(1)}%\n`;
        text += `  Maximum: ${cpu.max_percent?.toFixed(1)}%\n\n`;

        const memory = metrics.memory || {};
        text += `Memory Usage:\n`;
        text += `  Average: ${memory.average_mb?.toFixed(1)}MB\n`;
        text += `  Maximum: ${memory.max_mb?.toFixed(1)}MB\n\n`;

        if (hotspots.length > 0) {
            text += `Hotspots:\n`;
            hotspots.forEach(hotspot => {
                text += `  - ${hotspot.message}\n`;
            });
            text += `\n`;
        }

        if (suggestions.length > 0) {
            text += `Optimization Suggestions:\n`;
            suggestions.forEach(suggestion => {
                text += `  - ${suggestion.title}: ${suggestion.description}\n`;
            });
        }

        return text;
    }

    /**
     * Get webview HTML content
     */
    getProfilerWebviewContent() {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Astra Profiler</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
            margin: 0;
            padding: 20px;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--vscode-panel-border);
        }
        
        .controls {
            display: flex;
            gap: 10px;
        }
        
        button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: 1px solid var(--vscode-button-border);
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
        }
        
        button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        
        .panel {
            background-color: var(--vscode-editor-background);
            border: 1px solid var(--vscode-panel-border);
            border-radius: 4px;
            padding: 15px;
        }
        
        .panel h3 {
            margin-top: 0;
            color: var(--vscode-foreground);
        }
        
        .metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .metric {
            text-align: center;
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: var(--vscode-charts-blue);
        }
        
        .metric-label {
            font-size: 12px;
            color: var(--vscode-descriptionForeground);
        }
        
        .chart-container {
            height: 200px;
            margin-top: 10px;
        }
        
        .hotspot {
            padding: 10px;
            margin: 5px 0;
            background-color: var(--vscode-list-inactiveSelectionBackground);
            border-left: 4px solid var(--vscode-charts-orange);
            cursor: pointer;
        }
        
        .hotspot:hover {
            background-color: var(--vscode-list-hoverBackground);
        }
        
        .hotspot.high {
            border-left-color: var(--vscode-errorForeground);
        }
        
        .hotspot.medium {
            border-left-color: var(--vscode-charts-orange);
        }
        
        .suggestion {
            padding: 10px;
            margin: 5px 0;
            background-color: var(--vscode-list-inactiveSelectionBackground);
            border-left: 4px solid var(--vscode-charts-green);
        }
        
        .status {
            padding: 10px;
            background-color: var(--vscode-notifications-background);
            border-radius: 4px;
            margin-bottom: 10px;
        }
        
        .status.profiling {
            border-left: 4px solid var(--vscode-charts-blue);
        }
        
        canvas {
            max-width: 100%;
            height: auto;
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>Astra Performance Profiler</h2>
        <div class="controls">
            <button id="startBtn">Start Profiling</button>
            <button id="stopBtn" disabled>Stop Profiling</button>
            <button id="exportBtn" disabled>Export</button>
        </div>
    </div>

    <div id="status" class="status" style="display: none;"></div>

    <div class="content">
        <div class="panel">
            <h3>Performance Metrics</h3>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-value" id="cpuValue">-</div>
                    <div class="metric-label">CPU %</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="memoryValue">-</div>
                    <div class="metric-label">Memory MB</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="timeValue">-</div>
                    <div class="metric-label">Time (s)</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="samplesValue">-</div>
                    <div class="metric-label">Samples</div>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="timelineChart"></canvas>
            </div>
        </div>

        <div class="panel">
            <h3>Hotspots</h3>
            <div id="hotspotsList"></div>
        </div>

        <div class="panel">
            <h3>Function Performance</h3>
            <div class="chart-container">
                <canvas id="functionChart"></canvas>
            </div>
        </div>

        <div class="panel">
            <h3>Optimization Suggestions</h3>
            <div id="suggestionsList"></div>
        </div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        let isProfiling = false;
        let currentProfile = null;

        // Button event listeners
        document.getElementById('startBtn').addEventListener('click', () => {
            const target = 'native'; // Could be made configurable
            vscode.postMessage({
                type: 'startProfiling',
                data: { target }
            });
        });

        document.getElementById('stopBtn').addEventListener('click', () => {
            vscode.postMessage({
                type: 'stopProfiling'
            });
        });

        document.getElementById('exportBtn').addEventListener('click', () => {
            vscode.postMessage({
                type: 'exportProfile',
                data: { format: 'json' }
            });
        });

        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.type) {
                case 'profilingStarted':
                    handleProfilingStarted(message.data);
                    break;
                case 'profilingStopped':
                    handleProfilingStopped(message.data);
                    break;
                case 'profileUpdate':
                    handleProfileUpdate(message.data);
                    break;
            }
        });

        function handleProfilingStarted(data) {
            isProfiling = true;
            updateStatus('Profiling started...', 'profiling');
            updateButtons(true);
        }

        function handleProfilingStopped(profile) {
            isProfiling = false;
            currentProfile = profile;
            updateStatus('Profiling completed', '');
            updateButtons(false);
            displayProfile(profile);
        }

        function handleProfileUpdate(profile) {
            currentProfile = profile;
            displayProfile(profile);
        }

        function updateStatus(message, className) {
            const statusEl = document.getElementById('status');
            statusEl.textContent = message;
            statusEl.className = 'status ' + className;
            statusEl.style.display = 'block';
        }

        function updateButtons(profiling) {
            document.getElementById('startBtn').disabled = profiling;
            document.getElementById('stopBtn').disabled = !profiling;
            document.getElementById('exportBtn').disabled = !currentProfile;
        }

        function displayProfile(profile) {
            const summary = profile.summary || {};
            const metrics = profile.performance_metrics || {};
            
            // Update metrics
            document.getElementById('cpuValue').textContent = 
                metrics.cpu?.average_percent?.toFixed(1) || '-';
            document.getElementById('memoryValue').textContent = 
                metrics.memory?.average_mb?.toFixed(1) || '-';
            document.getElementById('timeValue').textContent = 
                summary.total_time_seconds?.toFixed(2) || '-';
            document.getElementById('samplesValue').textContent = 
                summary.sample_count || '-';
            
            // Display hotspots
            displayHotspots(profile.hotspots || []);
            
            // Display suggestions
            displaySuggestions(profile.optimization_suggestions || []);
            
            // Draw charts
            drawTimelineChart(metrics);
            drawFunctionChart(profile.functions || {});
        }

        function displayHotspots(hotspots) {
            const container = document.getElementById('hotspotsList');
            container.innerHTML = '';
            
            hotspots.forEach(hotspot => {
                const div = document.createElement('div');
                div.className = \`hotspot \${hotspot.severity}\`;
                div.innerHTML = \`
                    <strong>\${hotspot.type.toUpperCase()}</strong><br>
                    \${hotspot.message}<br>
                    <small>\${hotspot.suggestion}</small>
                \`;
                div.addEventListener('click', () => {
                    vscode.postMessage({
                        type: 'showHotspot',
                        data: hotspot
                    });
                });
                container.appendChild(div);
            });
        }

        function displaySuggestions(suggestions) {
            const container = document.getElementById('suggestionsList');
            container.innerHTML = '';
            
            suggestions.forEach(suggestion => {
                const div = document.createElement('div');
                div.className = 'suggestion';
                div.innerHTML = \`
                    <strong>\${suggestion.title}</strong><br>
                    \${suggestion.description}<br>
                    <small>Priority: \${suggestion.priority}</small>
                \`;
                div.addEventListener('click', () => {
                    vscode.postMessage({
                        type: 'applyOptimization',
                        data: suggestion
                    });
                });
                container.appendChild(div);
            });
        }

        function drawTimelineChart(metrics) {
            const canvas = document.getElementById('timelineChart');
            const ctx = canvas.getContext('2d');
            
            // Simple timeline chart implementation
            const cpuSamples = metrics.cpu?.samples || [];
            const memorySamples = metrics.memory?.samples || [];
            
            if (cpuSamples.length === 0) return;
            
            // Clear canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Draw CPU line
            ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--vscode-charts-blue');
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            cpuSamples.forEach((sample, i) => {
                const x = (i / cpuSamples.length) * canvas.width;
                const y = canvas.height - (sample / 100) * canvas.height;
                
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            
            ctx.stroke();
        }

        function drawFunctionChart(functions) {
            const canvas = document.getElementById('functionChart');
            const ctx = canvas.getContext('2d');
            
            const functionNames = Object.keys(functions);
            if (functionNames.length === 0) return;
            
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Draw simple bar chart
            const barWidth = canvas.width / functionNames.length;
            
            functionNames.forEach((name, i) => {
                const func = functions[name];
                const height = (func.total_time / Math.max(...Object.values(functions).map(f => f.total_time))) * canvas.height;
                
                ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--vscode-charts-green');
                ctx.fillRect(i * barWidth, canvas.height - height, barWidth - 2, height);
                
                // Draw label
                ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--vscode-foreground');
                ctx.font = '10px monospace';
                ctx.fillText(name, i * barWidth, canvas.height - 5);
            });
        }
    </script>
</body>
</html>`;
    }

    /**
     * Dispose of resources
     */
    dispose() {
        this.disposables.forEach(d => d.dispose());
        if (this.panel) {
            this.panel.dispose();
        }
    }
}

module.exports = ProfilerUI;
