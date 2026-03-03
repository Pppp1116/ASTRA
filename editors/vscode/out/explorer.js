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
exports.AstraExplorerProvider = void 0;
const vscode = __importStar(require("vscode"));
const path = __importStar(require("path"));
class AstraExplorerProvider {
    constructor(workspaceRoot) {
        this._onDidChangeTreeData = new vscode.EventEmitter();
        this.onDidChangeTreeData = this._onDidChangeTreeData.event;
        this.workspaceRoot = workspaceRoot;
    }
    refresh() {
        this._onDidChangeTreeData.fire();
    }
    getTreeItem(element) {
        return element;
    }
    getChildren(element) {
        if (!this.workspaceRoot) {
            return Promise.resolve([]);
        }
        if (!element) {
            // Root level - show workspace structure
            return this.getWorkspaceItems();
        }
        return Promise.resolve([]);
    }
    async getWorkspaceItems() {
        const items = [];
        if (!this.workspaceRoot) {
            return items;
        }
        try {
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (workspaceFolder) {
                // Find all .astra files in the workspace
                const files = await vscode.workspace.findFiles('**/*.astra', '**/node_modules/**');
                // Group files by directory
                const directories = new Map();
                for (const file of files) {
                    const dir = path.dirname(file.fsPath);
                    if (!directories.has(dir)) {
                        directories.set(dir, []);
                    }
                    directories.get(dir).push(file);
                }
                // Create tree items
                for (const [dir, dirFiles] of directories) {
                    const relativeDir = path.relative(workspaceFolder.uri.fsPath, dir);
                    const label = relativeDir === '' ? 'Root' : relativeDir;
                    const dirItem = new AstraTreeItem(label, vscode.TreeItemCollapsibleState.Expanded, undefined, 'folder');
                    items.push(dirItem);
                    // Add files in this directory
                    for (const file of dirFiles) {
                        const fileName = path.basename(file.fsPath);
                        const fileItem = new AstraTreeItem(fileName, vscode.TreeItemCollapsibleState.None, file, 'file');
                        fileItem.command = {
                            command: 'vscode.open',
                            title: 'Open File',
                            arguments: [file]
                        };
                        items.push(fileItem);
                    }
                }
            }
        }
        catch (error) {
            console.error('Error loading workspace items:', error);
        }
        return items;
    }
}
exports.AstraExplorerProvider = AstraExplorerProvider;
class AstraTreeItem extends vscode.TreeItem {
    constructor(label, collapsibleState, resourceUri, itemType) {
        super(label, collapsibleState);
        this.label = label;
        this.collapsibleState = collapsibleState;
        this.resourceUri = resourceUri;
        this.itemType = itemType;
        if (this.resourceUri) {
            this.resourceUri = this.resourceUri;
        }
        this.tooltip = `${this.label} (${this.itemType})`;
        if (this.itemType === 'file') {
            this.contextValue = 'astraFile';
            this.iconPath = new vscode.ThemeIcon('file-code');
        }
        else if (this.itemType === 'folder') {
            this.contextValue = 'astraFolder';
            this.iconPath = new vscode.ThemeIcon('folder');
        }
    }
}
//# sourceMappingURL=explorer.js.map