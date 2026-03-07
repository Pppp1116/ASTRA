/**
 * Package Manager UI for ASTRA VS Code Extension
 * Provides a graphical interface for managing ASTRA packages
 */

const vscode = require('vscode');

class PackageManagerUI {
    constructor(context) {
        this.context = context;
        this.panel = null;
        this.disposables = [];
        this.packages = [];
        this.installedPackages = new Set();
        this.searchResults = [];
        this.currentFilter = 'all';
        this.sortBy = 'name';
    }

    /**
     * Show the package manager panel
     */
    showPackageManager() {
        if (this.panel) {
            this.panel.reveal();
            return;
        }

        this.panel = vscode.window.createWebviewPanel(
            'astraPackageManager',
            'ASTRA Package Manager',
            vscode.ViewColumn.One,
            {
                enableScripts: true,
                retainContextWhenHidden: true,
                localResourceRoots: [
                    vscode.Uri.joinPath(this.context.extensionUri, 'package-manager')
                ]
            }
        );

        this.panel.onDidDispose(() => {
            this.panel = null;
        });

        this.panel.webview.html = this.getPackageManagerWebviewContent();

        // Handle messages from webview
        this.panel.webview.onDidReceiveMessage(
            message => this.handleWebviewMessage(message),
            undefined,
            this.disposables
        );

        // Load initial data
        this.loadPackages();
    }

    /**
     * Handle webview messages
     */
    async handleWebviewMessage(message) {
        switch (message.type) {
            case 'searchPackages':
                await this.searchPackages(message.query);
                break;
            case 'installPackage':
                await this.installPackage(message.packageName);
                break;
            case 'uninstallPackage':
                await this.uninstallPackage(message.packageName);
                break;
            case 'updatePackage':
                await this.updatePackage(message.packageName);
                break;
            case 'getPackageInfo':
                await this.getPackageInfo(message.packageName);
                break;
            case 'publishPackage':
                await this.publishPackage(message.packagePath);
                break;
            case 'refreshPackages':
                await this.refreshPackages();
                break;
            case 'setFilter':
                this.setFilter(message.filter);
                break;
            case 'setSort':
                this.setSort(message.sortBy);
                break;
        }
    }

    /**
     * Load all packages
     */
    async loadPackages() {
        try {
            // Get installed packages
            const installedResult = await vscode.commands.executeCommand('astra.getInstalledPackages');
            this.installedPackages = new Set(installedResult.packages || []);

            // Get available packages
            const availableResult = await vscode.commands.executeCommand('astra.searchPackages', '');
            this.packages = availableResult.packages || [];

            this.updatePackageList();
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to load packages: ${error.message}`);
        }
    }

    /**
     * Search for packages
     */
    async searchPackages(query) {
        try {
            const result = await vscode.commands.executeCommand('astra.searchPackages', query);
            this.searchResults = result.packages || [];
            this.updatePackageList();
        } catch (error) {
            vscode.window.showErrorMessage(`Search failed: ${error.message}`);
        }
    }

    /**
     * Install a package
     */
    async installPackage(packageName) {
        try {
            vscode.window.showInformationMessage(`Installing ${packageName}...`);
            
            const result = await vscode.commands.executeCommand('astra.installPackage', packageName);
            
            if (result.success) {
                vscode.window.showInformationMessage(`Successfully installed ${packageName}`);
                this.installedPackages.add(packageName);
                this.updatePackageList();
            } else {
                vscode.window.showErrorMessage(`Failed to install ${packageName}: ${result.error}`);
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Installation failed: ${error.message}`);
        }
    }

    /**
     * Uninstall a package
     */
    async uninstallPackage(packageName) {
        try {
            const confirm = await vscode.window.showWarningMessage(
                `Are you sure you want to uninstall ${packageName}?`,
                'Yes', 'No'
            );
            
            if (confirm === 'Yes') {
                vscode.window.showInformationMessage(`Uninstalling ${packageName}...`);
                
                const result = await vscode.commands.executeCommand('astra.uninstallPackage', packageName);
                
                if (result.success) {
                    vscode.window.showInformationMessage(`Successfully uninstalled ${packageName}`);
                    this.installedPackages.delete(packageName);
                    this.updatePackageList();
                } else {
                    vscode.window.showErrorMessage(`Failed to uninstall ${packageName}: ${result.error}`);
                }
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Uninstallation failed: ${error.message}`);
        }
    }

    /**
     * Update a package
     */
    async updatePackage(packageName) {
        try {
            vscode.window.showInformationMessage(`Updating ${packageName}...`);
            
            const result = await vscode.commands.executeCommand('astra.updatePackage', packageName);
            
            if (result.success) {
                vscode.window.showInformationMessage(`Successfully updated ${packageName}`);
            } else {
                vscode.window.showErrorMessage(`Failed to update ${packageName}: ${result.error}`);
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Update failed: ${error.message}`);
        }
    }

    /**
     * Get package information
     */
    async getPackageInfo(packageName) {
        try {
            const result = await vscode.commands.executeCommand('astra.getPackageInfo', packageName);
            
            if (this.panel) {
                this.panel.webview.postMessage({
                    type: 'packageInfo',
                    data: result
                });
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to get package info: ${error.message}`);
        }
    }

    /**
     * Publish a package
     */
    async publishPackage(packagePath) {
        try {
            vscode.window.showInformationMessage('Publishing package...');
            
            const result = await vscode.commands.executeCommand('astra.publishPackage', packagePath);
            
            if (result.success) {
                vscode.window.showInformationMessage('Package published successfully!');
            } else {
                vscode.window.showErrorMessage(`Failed to publish package: ${result.error}`);
            }
        } catch (error) {
            vscode.window.showErrorMessage(`Publishing failed: ${error.message}`);
        }
    }

    /**
     * Refresh package list
     */
    async refreshPackages() {
        await this.loadPackages();
    }

    /**
     * Set filter for package list
     */
    setFilter(filter) {
        this.currentFilter = filter;
        this.updatePackageList();
    }

    /**
     * Set sort order for package list
     */
    setSort(sortBy) {
        this.sortBy = sortBy;
        this.updatePackageList();
    }

    /**
     * Update package list in webview
     */
    updatePackageList() {
        if (!this.panel) return;

        let packages = this.searchResults.length > 0 ? this.searchResults : this.packages;

        // Apply filter
        if (this.currentFilter === 'installed') {
            packages = packages.filter(pkg => this.installedPackages.has(pkg.name));
        } else if (this.currentFilter === 'available') {
            packages = packages.filter(pkg => !this.installedPackages.has(pkg.name));
        }

        // Apply sort
        packages.sort((a, b) => {
            switch (this.sortBy) {
                case 'name':
                    return a.name.localeCompare(b.name);
                case 'downloads':
                    return (b.downloads || 0) - (a.downloads || 0);
                case 'updated':
                    return new Date(b.updated || 0) - new Date(a.updated || 0);
                default:
                    return 0;
            }
        });

        // Add installation status
        packages = packages.map(pkg => ({
            ...pkg,
            installed: this.installedPackages.has(pkg.name)
        }));

        this.panel.webview.postMessage({
            type: 'packageList',
            data: packages
        });
    }

    /**
     * Get webview HTML content
     */
    getPackageManagerWebviewContent() {
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASTRA Package Manager</title>
    <style>
        body {
            font-family: var(--vscode-font-family);
            color: var(--vscode-foreground);
            background: var(--vscode-editor-background);
            margin: 0;
            padding: 20px;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--vscode-panel-border);
            padding-bottom: 10px;
        }
        
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .search-box input {
            flex: 1;
            padding: 8px;
            border: 1px solid var(--vscode-input-border);
            background: var(--vscode-input-background);
            color: var(--vscode-input-foreground);
            border-radius: 4px;
        }
        
        .search-box button {
            padding: 8px 16px;
            border: 1px solid var(--vscode-button-border);
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border-radius: 4px;
            cursor: pointer;
        }
        
        .search-box button:hover {
            background: var(--vscode-button-hoverBackground);
        }
        
        .filters {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .filters select {
            padding: 6px;
            border: 1px solid var(--vscode-dropdown-border);
            background: var(--vscode-dropdown-background);
            color: var(--vscode-dropdown-foreground);
            border-radius: 4px;
        }
        
        .package-list {
            display: grid;
            gap: 15px;
        }
        
        .package-item {
            border: 1px solid var(--vscode-panel-border);
            border-radius: 6px;
            padding: 15px;
            background: var(--vscode-editor-background);
        }
        
        .package-item.installed {
            border-color: var(--vscode-charts-green);
        }
        
        .package-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 10px;
        }
        
        .package-name {
            font-weight: bold;
            font-size: 1.1em;
            color: var(--vscode-foreground);
        }
        
        .package-version {
            color: var(--vscode-descriptionForeground);
            font-size: 0.9em;
        }
        
        .package-description {
            color: var(--vscode-descriptionForeground);
            margin-bottom: 10px;
            line-height: 1.4;
        }
        
        .package-meta {
            display: flex;
            gap: 15px;
            font-size: 0.85em;
            color: var(--vscode-descriptionForeground);
            margin-bottom: 10px;
        }
        
        .package-actions {
            display: flex;
            gap: 8px;
        }
        
        .package-actions button {
            padding: 6px 12px;
            border: 1px solid var(--vscode-button-border);
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85em;
        }
        
        .package-actions button:hover {
            background: var(--vscode-button-hoverBackground);
        }
        
        .package-actions button.primary {
            background: var(--vscode-button-secondaryBackground);
            color: var(--vscode-button-secondaryForeground);
        }
        
        .package-actions button.danger {
            background: var(--vscode-errorBackground);
            color: var(--vscode-button-foreground);
            border-color: var(--vscode-errorBorder);
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: var(--vscode-descriptionForeground);
        }
        
        .error {
            color: var(--vscode-errorForeground);
            background: var(--vscode-inputValidation-errorBackground);
            border: 1px solid var(--vscode-inputValidation-errorBorder);
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>ASTRA Package Manager</h1>
        <div>
            <button onclick="refreshPackages()">Refresh</button>
            <button onclick="publishPackage()">Publish Package</button>
        </div>
    </div>

    <div class="search-box">
        <input type="text" id="searchInput" placeholder="Search packages..." />
        <button onclick="searchPackages()">Search</button>
    </div>

    <div class="filters">
        <select id="filterSelect" onchange="setFilter(this.value)">
            <option value="all">All Packages</option>
            <option value="installed">Installed</option>
            <option value="available">Available</option>
        </select>
        
        <select id="sortSelect" onchange="setSort(this.value)">
            <option value="name">Sort by Name</option>
            <option value="downloads">Sort by Downloads</option>
            <option value="updated">Sort by Updated</option>
        </select>
    </div>

    <div id="packageList" class="package-list">
        <div class="loading">Loading packages...</div>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        
        function searchPackages() {
            const query = document.getElementById('searchInput').value;
            vscode.postMessage({ type: 'searchPackages', query });
        }
        
        function installPackage(packageName) {
            vscode.postMessage({ type: 'installPackage', packageName });
        }
        
        function uninstallPackage(packageName) {
            vscode.postMessage({ type: 'uninstallPackage', packageName });
        }
        
        function updatePackage(packageName) {
            vscode.postMessage({ type: 'updatePackage', packageName });
        }
        
        function showPackageInfo(packageName) {
            vscode.postMessage({ type: 'getPackageInfo', packageName });
        }
        
        function publishPackage() {
            vscode.postMessage({ type: 'publishPackage' });
        }
        
        function refreshPackages() {
            vscode.postMessage({ type: 'refreshPackages' });
        }
        
        function setFilter(filter) {
            vscode.postMessage({ type: 'setFilter', filter });
        }
        
        function setSort(sortBy) {
            vscode.postMessage({ type: 'setSort', sortBy });
        }
        
        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.type) {
                case 'packageList':
                    renderPackageList(message.data);
                    break;
                case 'packageInfo':
                    showPackageInfoDialog(message.data);
                    break;
            }
        });
        
        function renderPackageList(packages) {
            const container = document.getElementById('packageList');
            
            if (packages.length === 0) {
                container.innerHTML = '<div class="loading">No packages found</div>';
                return;
            }
            
            container.innerHTML = packages.map(pkg => \`
                <div class="package-item \${pkg.installed ? 'installed' : ''}">
                    <div class="package-header">
                        <div>
                            <div class="package-name">\${pkg.name}</div>
                            <div class="package-version">v\${pkg.version || 'latest'}</div>
                        </div>
                        <div class="package-actions">
                            \${pkg.installed ? 
                                \`<button onclick="updatePackage('\${pkg.name}')">Update</button>
                                 <button class="danger" onclick="uninstallPackage('\${pkg.name}')">Uninstall</button>\` :
                                \`<button class="primary" onclick="installPackage('\${pkg.name}')">Install</button>\`
                            }
                            <button onclick="showPackageInfo('\${pkg.name}')">Info</button>
                        </div>
                    </div>
                    <div class="package-description">\${pkg.description || 'No description available'}</div>
                    <div class="package-meta">
                        <span>📦 \${pkg.author || 'Unknown'}</span>
                        <span>⬇️ \${pkg.downloads || 0} downloads</span>
                        <span>📅 \${pkg.updated ? new Date(pkg.updated).toLocaleDateString() : 'Unknown'}</span>
                    </div>
                </div>
            \`).join('');
        }
        
        function showPackageInfoDialog(packageInfo) {
            // Create a simple info dialog
            const message = \`
Package: \${packageInfo.name}
Version: \${packageInfo.version}
Author: \${packageInfo.author || 'Unknown'}
Description: \${packageInfo.description || 'No description'}
License: \${packageInfo.license || 'Unknown'}
Repository: \${packageInfo.repository || 'Unknown'}
            \`.trim();
            
            alert(message);
        }
        
        // Search on Enter key
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchPackages();
            }
        });
    </script>
</body>
</html>`;
    }

    /**
     * Dispose resources
     */
    dispose() {
        this.disposables.forEach(d => d.dispose());
        if (this.panel) {
            this.panel.dispose();
        }
    }
}

module.exports = PackageManagerUI;
