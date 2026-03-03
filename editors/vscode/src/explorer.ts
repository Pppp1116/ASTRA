import * as vscode from 'vscode';
import * as path from 'path';

export class AstraExplorerProvider implements vscode.TreeDataProvider<AstraTreeItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<AstraTreeItem | undefined | null | void> = new vscode.EventEmitter<AstraTreeItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<AstraTreeItem | undefined | null | void> = this._onDidChangeTreeData.event;

    private workspaceRoot: string | undefined;

    constructor(workspaceRoot?: string) {
        this.workspaceRoot = workspaceRoot;
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }

    getTreeItem(element: AstraTreeItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: AstraTreeItem): Thenable<AstraTreeItem[]> {
        if (!this.workspaceRoot) {
            return Promise.resolve([]);
        }

        if (!element) {
            // Root level - show workspace structure
            return this.getWorkspaceItems();
        }

        return Promise.resolve([]);
    }

    private async getWorkspaceItems(): Promise<AstraTreeItem[]> {
        const items: AstraTreeItem[] = [];
        
        if (!this.workspaceRoot) {
            return items;
        }

        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (workspaceFolder) {
                // Find all .astra files in the workspace
                const files = await vscode.workspace.findFiles('**/*.astra', '**/node_modules/**');
                
                // Group files by directory
                const directories = new Map<string, vscode.Uri[]>();
                
                for (const file of files) {
                    const dir = path.dirname(file.fsPath);
                    if (!directories.has(dir)) {
                        directories.set(dir, []);
                    }
                    directories.get(dir)!.push(file);
                }

                // Create tree items
                for (const [dir, dirFiles] of directories) {
                    const relativeDir = path.relative(workspaceFolder.uri.fsPath, dir);
                    const label = relativeDir === '' ? 'Root' : relativeDir;
                    
                    const dirItem = new AstraTreeItem(
                        label,
                        vscode.TreeItemCollapsibleState.Expanded,
                        undefined,
                        'folder'
                    );
                    
                    items.push(dirItem);
                    
                    // Add files in this directory
                    for (const file of dirFiles) {
                        const fileName = path.basename(file.fsPath);
                        const fileItem = new AstraTreeItem(
                            fileName,
                            vscode.TreeItemCollapsibleState.None,
                            file,
                            'file'
                        );
                        fileItem.command = {
                            command: 'vscode.open',
                            title: 'Open File',
                            arguments: [file]
                        };
                        items.push(fileItem);
                    }
                }
            }
        } catch (error) {
            console.error('Error loading workspace items:', error);
        }

        return items;
    }
}

class AstraTreeItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly resourceUri?: vscode.Uri,
        public readonly itemType?: string
    ) {
        super(label, collapsibleState);
        
        if (this.resourceUri) {
            this.resourceUri = this.resourceUri;
        }
        
        this.tooltip = `${this.label} (${this.itemType})`;
        
        if (this.itemType === 'file') {
            this.contextValue = 'astraFile';
            this.iconPath = new vscode.ThemeIcon('file-code');
        } else if (this.itemType === 'folder') {
            this.contextValue = 'astraFolder';
            this.iconPath = new vscode.ThemeIcon('folder');
        }
    }
}
