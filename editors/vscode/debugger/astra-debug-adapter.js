/**
 * Astra Debug Adapter
 * Implements the Debug Adapter Protocol (DAP) for Astra language debugging
 */

const { EventEmitter } = require('events');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

class AstraDebugSession extends EventEmitter {
    constructor() {
        super();
        this.debuggee = null;
        this.breakpoints = new Map();
        this.variableHandles = new Map();
        this.nextVariableHandle = 1;
        this.stackFrames = [];
        this.currentLine = 0;
        this.currentFile = '';
        this.isRunning = false;
        this.isPaused = false;
    }

    /**
     * Initialize the debug session
     */
    initializeRequest(args, response) {
        // Send capabilities
        response.body = {
            supportsConfigurationDoneRequest: true,
            supportsFunctionBreakpoints: false,
            supportsConditionalBreakpoints: true,
            supportsEvaluateForHovers: true,
            supportsStepBack: false,
            supportsSetVariable: true,
            supportsRestartFrame: false,
            supportsGotoTargetsRequest: false,
            supportsStepInTargetsRequest: false,
            supportsCompletionsRequest: false,
            supportsModulesRequest: false,
            supportsRestartRequest: true,
            supportsExceptionInfoRequest: true,
            supportsTerminateDebuggee: true,
            supportsDelayedStackTraceLoading: false,
            supportsLoadedSourcesRequest: false,
            supportsLogPoints: false,
            supportsTerminateThreadsRequest: false,
            supportsSetExpression: true,
            supportsValueFormattingOptions: true,
            supportsExceptionFilterOptions: true,
            supportsExceptionOptions: true
        };

        this.sendResponse(response);
    }

    /**
     * Launch the debuggee
     */
    launchRequest(args, response) {
        const { program, args: programArgs, cwd, env, target } = args;
        
        try {
            // Determine the appropriate command based on target
            let command, commandArgs;
            
            switch (target) {
                case 'gpu':
                    command = 'python';
                    commandArgs = ['-m', 'astra', 'run', '--target', 'gpu', program, ...programArgs];
                    break;
                case 'llvm':
                    command = 'python';
                    commandArgs = ['-m', 'astra', 'run', '--target', 'llvm', program, ...programArgs];
                    break;
                case 'native':
                default:
                    command = 'python';
                    commandArgs = ['-m', 'astra', 'run', '--target', 'native', program, ...programArgs];
                    break;
            }

            // Add debug flags
            commandArgs.push('--debug');
            commandArgs.push('--debug-adapter');

            this.debuggee = spawn(command, commandArgs, {
                cwd: cwd || process.cwd(),
                env: { ...process.env, ...env },
                stdio: ['pipe', 'pipe', 'pipe']
            });

            this.debuggee.stdout.on('data', (data) => {
                const output = data.toString();
                this.handleDebuggeeOutput('stdout', output);
            });

            this.debuggee.stderr.on('data', (data) => {
                const output = data.toString();
                this.handleDebuggeeOutput('stderr', output);
            });

            this.debuggee.on('close', (code) => {
                this.handleDebuggeeExit(code);
            });

            this.debuggee.on('error', (error) => {
                this.sendErrorResponse(response, 1, `Failed to launch debuggee: ${error.message}`);
                return;
            });

            this.currentFile = program;
            this.isRunning = true;

            this.sendResponse(response);
            
            // Send initialized event
            this.sendEvent('initialized');

        } catch (error) {
            this.sendErrorResponse(response, 1, `Failed to launch: ${error.message}`);
        }
    }

    /**
     * Configuration done
     */
    configurationDoneRequest(args, response) {
        this.sendResponse(response);
        
        // Start execution
        this.continueRequest({ threadId: 1 }, {
            sendResponse: () => {},
            sendErrorResponse: () => {}
        });
    }

    /**
     * Continue execution
     */
    continueRequest(args, response) {
        if (this.debuggee && this.isPaused) {
            this.sendDebugCommand('continue');
            this.isPaused = false;
        }
        
        this.sendResponse(response);
    }

    /**
     * Next (step over)
     */
    nextRequest(args, response) {
        if (this.debuggee && this.isPaused) {
            this.sendDebugCommand('next');
        }
        
        this.sendResponse(response);
    }

    /**
     * Step in
     */
    stepInRequest(args, response) {
        if (this.debuggee && this.isPaused) {
            this.sendDebugCommand('step');
        }
        
        this.sendResponse(response);
    }

    /**
     * Step out
     */
    stepOutRequest(args, response) {
        if (this.debuggee && this.isPaused) {
            this.sendDebugCommand('step_out');
        }
        
        this.sendResponse(response);
    }

    /**
     * Pause execution
     */
    pauseRequest(args, response) {
        if (this.debuggee && this.isRunning && !this.isPaused) {
            this.sendDebugCommand('pause');
            this.isPaused = true;
        }
        
        this.sendResponse(response);
    }

    /**
     * Get stack trace with enhanced ASTRA support
     */
    stackTraceRequest(args, response) {
        const { startFrame, levels } = args;
        
        // Try to get actual stack trace from debuggee
        if (this.debuggee && this.isPaused) {
            this.sendDebugCommand(`stacktrace:${startFrame || 0}:${levels || 20}`);
            
            // For now, return current frame info
            // In a real implementation, this would parse the response from debuggee
            const stackFrames = [
                {
                    id: 1,
                    name: this.currentFunction || 'main',
                    source: { 
                        name: path.basename(this.currentFile), 
                        path: this.currentFile 
                    },
                    line: this.currentLine,
                    column: this.currentColumn || 0,
                    presentationHint: 'normal'
                }
            ];
            
            response.body = {
                stackFrames: stackFrames,
                totalFrames: stackFrames.length
            };
        } else {
            response.body = {
                stackFrames: [],
                totalFrames: 0
            };
        }
        
        this.sendResponse(response);
    }

    /**
     * Enhanced set breakpoints with ASTRA line mapping
     */
    setBreakpointsRequest(args, response) {
        const { source, breakpoints } = args;
        const sourcePath = source.path;
        
        const clientBreakpoints = [];
        
        // Clear existing breakpoints for this file
        this.breakpoints.delete(sourcePath);
        
        for (const bp of breakpoints || []) {
            // Verify breakpoint with ASTRA source mapping
            const verified = this.verifyAstraBreakpoint(sourcePath, bp.line, bp.column);
            
            clientBreakpoints.push({
                id: bp.id,
                verified: verified.verified,
                message: verified.message,
                source: source,
                line: verified.actualLine || bp.line,
                column: verified.actualColumn || bp.column,
                endLine: bp.endLine,
                endColumn: bp.endColumn
            });
            
            if (verified.verified) {
                this.breakpoints.set(sourcePath, this.breakpoints.get(sourcePath) || []);
                this.breakpoints.get(sourcePath).push({
                    line: verified.actualLine || bp.line,
                    column: verified.actualColumn || bp.column,
                    condition: bp.condition,
                    hitCondition: bp.hitCondition,
                    logMessage: bp.logMessage
                });
                
                // Send breakpoint to debuggee
                this.sendDebugCommand(`breakpoint:${sourcePath}:${verified.actualLine || bp.line}:${bp.column || 0}:${bp.condition || ''}`);
            }
        }
        
        response.body = { breakpoints: clientBreakpoints };
        this.sendResponse(response);
    }

    /**
     * Verify ASTRA breakpoint with source mapping
     */
    verifyAstraBreakpoint(sourcePath, line, column = 0) {
        try {
            if (fs.existsSync(sourcePath)) {
                const content = fs.readFileSync(sourcePath, 'utf8');
                const lines = content.split('\n');
                
                if (line > 0 && line <= lines.length) {
                    const lineContent = lines[line - 1];
                    
                    // Check if line contains executable code
                    if (this.isExecutableLine(lineContent)) {
                        return { 
                            verified: true, 
                            actualLine: line,
                            actualColumn: column
                        };
                    } else {
                        // Find next executable line
                        for (let i = line; i <= Math.min(line + 5, lines.length); i++) {
                            if (this.isExecutableLine(lines[i - 1])) {
                                return { 
                                    verified: true, 
                                    actualLine: i,
                                    message: `Moved to line ${i} (next executable line)`
                                };
                            }
                        }
                        return { 
                            verified: false, 
                            message: `No executable code found near line ${line}` 
                        };
                    }
                } else {
                    return { verified: false, message: `Line ${line} is outside file bounds (1-${lines.length})` };
                }
            } else {
                return { verified: false, message: `Source file not found: ${sourcePath}` };
            }
        } catch (error) {
            return { verified: false, message: `Error verifying breakpoint: ${error.message}` };
        }
    }

    /**
     * Check if a line contains executable code
     */
    isExecutableLine(lineContent) {
        const trimmed = lineContent.trim();
        
        // Skip empty lines, comments, and braces
        if (!trimmed || 
            trimmed.startsWith('//') || 
            trimmed.startsWith('/*') || 
            trimmed === '{' || 
            trimmed === '}' ||
            trimmed.startsWith('fn ') && trimmed.includes('{') && !trimmed.includes('}')) {
            return false;
        }
        
        return true;
    }

    /**
     * Get scopes for a stack frame
     */
    scopesRequest(args, response) {
        const { frameId } = args;
        
        const scopes = [
            {
                name: 'Locals',
                variablesReference: this.createVariableHandle('locals', {}),
                expensive: false
            },
            {
                name: 'Globals',
                variablesReference: this.createVariableHandle('globals', {}),
                expensive: false
            }
        ];
        
        response.body = { scopes };
        this.sendResponse(response);
    }

    /**
     * Get variables for a scope
     */
    variablesRequest(args, response) {
        const { variablesReference, filter } = args;
        
        const variableData = this.getVariableData(variablesReference);
        const variables = [];
        
        if (variableData) {
            switch (variableData.type) {
                case 'locals':
                    variables.push(...this.getLocalVariables(variableData.data));
                    break;
                case 'globals':
                    variables.push(...this.getGlobalVariables(variableData.data));
                    break;
                case 'object':
                    variables.push(...this.getObjectProperties(variableData.data));
                    break;
            }
        }
        
        response.body = { variables };
        this.sendResponse(response);
    }

    /**
     * Evaluate expression
     */
    evaluateRequest(args, response) {
        const { expression, frameId, context } = args;
        
        try {
            // Simple expression evaluation
            // In a real implementation, this would use the debuggee's expression evaluator
            let result;
            let variablesReference = 0;
            
            if (context === 'hover') {
                // For hover, just return the expression as a string
                result = expression;
            } else if (context === 'repl') {
                // For REPL, try to evaluate the expression
                if (expression.match(/^\d+$/)) {
                    result = parseInt(expression);
                } else if (expression === 'true' || expression === 'false') {
                    result = expression === 'true';
                } else if (expression.startsWith('"') && expression.endsWith('"')) {
                    result = expression.slice(1, -1);
                } else {
                    result = `<${expression}>`;
                    variablesReference = this.createVariableHandle('object', { name: expression });
                }
            }
            
            response.body = {
                result: String(result),
                type: typeof result,
                variablesReference: variablesReference,
                presentationHint: context === 'repl' ? 1 : 0
            };
            
        } catch (error) {
            response.body = {
                result: `Error: ${error.message}`,
                type: 'error',
                variablesReference: 0
            };
        }
        
        this.sendResponse(response);
    }

    /**
     * Set variable value
     */
    setVariableRequest(args, response) {
        const { variablesReference, name, value } = args;
        
        try {
            // In a real implementation, this would set the variable in the debuggee
            const success = true;
            
            response.body = { success };
            this.sendResponse(response);
            
            if (success) {
                // Send variable changed event
                this.sendEvent('output', {
                    category: 'console',
                    output: `${name} = ${value}\n`
                });
            }
            
        } catch (error) {
            this.sendErrorResponse(response, 1, `Failed to set variable: ${error.message}`);
        }
    }

    /**
     * Restart debugging
     */
    restartRequest(args, response) {
        // Kill current debuggee
        if (this.debuggee) {
            this.debuggee.kill();
        }
        
        // Restart with same arguments
        // This would need to store the original launch arguments
        this.sendResponse(response);
    }

    /**
     * Terminate debugging
     */
    terminateRequest(args, response) {
        if (this.debuggee) {
            this.debuggee.kill();
        }
        
        this.sendResponse(response);
        this.sendEvent('exited', { exitCode: 0 });
        this.sendEvent('terminated');
    }

    /**
     * Disconnect from debuggee
     */
    disconnectRequest(args, response) {
        if (this.debuggee) {
            this.debuggee.kill();
        }
        
        this.sendResponse(response);
    }

    /**
     * Handle debuggee output
     */
    handleDebuggeeOutput(type, output) {
        // Parse debug commands from output
        const lines = output.split('\n');
        
        for (const line of lines) {
            if (line.startsWith('DEBUG:')) {
                this.handleDebugCommand(line.substring(6));
            } else {
                // Send regular output
                this.sendEvent('output', {
                    category: type === 'stderr' ? 'stderr' : 'stdout',
                    output: line + '\n'
                });
            }
        }
    }

    /**
     * Handle debug commands from debuggee
     */
    handleDebugCommand(command) {
        const parts = command.split(':');
        const cmd = parts[0];
        const data = parts.slice(1).join(':');
        
        switch (cmd) {
            case 'breakpoint':
                this.handleBreakpointHit(data);
                break;
            case 'exception':
                this.handleException(data);
                break;
            case 'thread':
                this.handleThreadEvent(data);
                break;
            case 'module':
                this.handleModuleEvent(data);
                break;
        }
    }

    /**
     * Handle breakpoint hit
     */
    handleBreakpointHit(data) {
        const [file, line] = data.split(',');
        this.currentFile = file;
        this.currentLine = parseInt(line);
        this.isPaused = true;
        
        this.sendEvent('stopped', {
            reason: 'breakpoint',
            threadId: 1,
            preserveFocusHint: false,
            text: `Breakpoint hit at ${path.basename(file)}:${line}`,
            allThreadsStopped: false
        });
    }

    /**
     * Handle exception
     */
    handleException(data) {
        const [type, message, file, line] = data.split(',');
        
        this.sendEvent('stopped', {
            reason: 'exception',
            threadId: 1,
            preserveFocusHint: false,
            text: `${type}: ${message}`,
            allThreadsStopped: false,
            exceptionDetails: {
                exceptionId: type,
                description: message,
                stackTrace: `at ${file}:${line}`
            }
        });
    }

    /**
     * Handle thread events
     */
    handleThreadEvent(data) {
        const [event, threadId] = data.split(',');
        
        switch (event) {
            case 'started':
                this.sendEvent('thread', { reason: 'started', threadId: parseInt(threadId) });
                break;
            case 'exited':
                this.sendEvent('thread', { reason: 'exited', threadId: parseInt(threadId) });
                break;
        }
    }

    /**
     * Handle module events
     */
    handleModuleEvent(data) {
        const [event, modulePath] = data.split(',');
        
        switch (event) {
            case 'loaded':
                this.sendEvent('module', { reason: 'new', module: { id: modulePath, name: path.basename(modulePath) } });
                break;
        }
    }

    /**
     * Handle debuggee exit
     */
    handleDebuggeeExit(code) {
        this.isRunning = false;
        this.isPaused = false;
        
        this.sendEvent('exited', { exitCode: code });
        this.sendEvent('terminated');
    }

    /**
     * Send command to debuggee
     */
    sendDebugCommand(command) {
        if (this.debuggee && this.debuggee.stdin) {
            this.debuggee.stdin.write(`DEBUG:${command}\n`);
        }
    }

    /**
     * Create variable handle
     */
    createVariableHandle(type, data) {
        const handle = this.nextVariableHandle++;
        this.variableHandles.set(handle, { type, data });
        return handle;
    }

    /**
     * Get variable data from handle
     */
    getVariableData(handle) {
        return this.variableHandles.get(handle);
    }

    /**
     * Get local variables
     */
    getLocalVariables(data) {
        // Mock implementation - would get actual variables from debuggee
        return [
            {
                name: 'x',
                value: '42',
                type: 'Int',
                variablesReference: 0
            },
            {
                name: 'name',
                value: '"test"',
                type: 'String',
                variablesReference: 0
            }
        ];
    }

    /**
     * Get global variables
     */
    getGlobalVariables(data) {
        // Mock implementation
        return [
            {
                name: 'STDOUT',
                value: '<file>',
                type: 'File',
                variablesReference: this.createVariableHandle('object', { name: 'STDOUT' })
            }
        ];
    }

    /**
     * Get object properties
     */
    getObjectProperties(data) {
        // Mock implementation
        return [
            {
                name: 'length',
                value: '10',
                type: 'Int',
                variablesReference: 0
            }
        ];
    }

    /**
     * Send response to client
     */
    sendResponse(response) {
        this.send('response', response);
    }

    /**
     * Send error response to client
     */
    sendErrorResponse(response, code, message) {
        response.success = false;
        response.message = message;
        this.send('response', response);
    }

    /**
     * Send event to client
     */
    sendEvent(event, body) {
        this.send('event', { event, body });
    }

    /**
     * Send message to client
     */
    send(type, body) {
        const content = JSON.stringify(body);
        const header = `Content-Length: ${content.length}\r\n\r\n`;
        
        if (process.stdout) {
            process.stdout.write(header + content);
        }
    }
}

// Start the debug session
const session = new AstraDebugSession();

// Handle incoming messages
process.stdin.on('data', (data) => {
    const message = data.toString();
    const lines = message.split('\n');
    
    for (const line of lines) {
        if (line.trim()) {
            try {
                const json = JSON.parse(line);
                session.handleRequest(json);
            } catch (error) {
                console.error('Error parsing message:', error.message);
            }
        }
    }
});

// Handle requests
AstraDebugSession.prototype.handleRequest = function(request) {
    const { command, arguments: args, seq } = request;
    
    const response = {
        type: 'response',
        request_seq: seq,
        command: command,
        success: true,
        body: null
    };
    
    const methodName = `${command}Request`;
    if (typeof this[methodName] === 'function') {
        this[methodName](args, response);
    } else {
        this.sendErrorResponse(response, 1, `Unknown command: ${command}`);
    }
};

module.exports = AstraDebugSession;
