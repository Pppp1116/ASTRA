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
const debugadapter_1 = require("@vscode/debugadapter");
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
class AstraDebugSession extends debugadapter_1.DebugSession {
    constructor() {
        super();
        this.breakpoints = new Map();
        this.variableHandles = new Map();
        this.nextHandle = 1;
        this.setDebuggerLinesStartAt1(true);
        this.setDebuggerColumnsStartAt1(true);
    }
    initializeRequest(response, args) {
        response.body = response.body || {};
        response.body.supportsConfigurationDoneRequest = true;
        response.body.supportsConditionalBreakpoints = true;
        response.body.supportsHitConditionalBreakpoints = true;
        response.body.supportsEvaluateForHovers = true;
        response.body.supportsStepBack = false;
        response.body.supportsSetVariable = true;
        this.sendResponse(response);
    }
    configurationDoneRequest(response, args) {
        this.sendResponse(response);
    }
    launchRequest(response, args) {
        const config = args;
        // Build the Astra file first
        const buildArgs = ['build', config.program, '--target', config.target || 'py'];
        const buildProcess = (0, child_process_1.spawn)('astra', buildArgs, {
            cwd: config.cwd || path.dirname(config.program)
        });
        buildProcess.on('exit', (code) => {
            if (code !== 0) {
                this.sendErrorResponse(response, 3000, `Build failed with exit code ${code}`);
                return;
            }
            // Run the compiled file
            let runCommand;
            let runArgs = [];
            if (config.target === 'py') {
                runCommand = 'python';
                runArgs = [config.program.replace('.astra', '.py'), ...(config.args || [])];
            }
            else if (config.target === 'native') {
                runCommand = config.program.replace('.astra', '');
                runArgs = config.args || [];
            }
            else {
                this.sendErrorResponse(response, 3001, 'Debugging for LLVM target not yet supported');
                return;
            }
            this.process = (0, child_process_1.spawn)(runCommand, runArgs, {
                cwd: config.cwd || path.dirname(config.program),
                stdio: ['pipe', 'pipe', 'pipe']
            });
            this.process.stdout?.on('data', (data) => {
                this.sendEvent(new debugadapter_1.OutputEvent(data.toString(), 'stdout'));
            });
            this.process.stderr?.on('data', (data) => {
                this.sendEvent(new debugadapter_1.OutputEvent(data.toString(), 'stderr'));
            });
            this.process.on('exit', (code) => {
                this.sendEvent(new debugadapter_1.TerminatedEvent());
            });
            this.process.on('error', (error) => {
                this.sendErrorResponse(response, 3002, `Process error: ${error.message}`);
            });
            this.sendResponse(response);
            if (config.stopOnEntry) {
                this.sendEvent(new debugadapter_1.StoppedEvent('entry', 1));
            }
        });
        buildProcess.on('error', (error) => {
            this.sendErrorResponse(response, 3003, `Build process error: ${error.message}`);
        });
    }
    setBreakPointsRequest(response, args) {
        const path = args.source.path;
        const clientBreakpoints = args.breakpoints || [];
        const actualBreakpoints = [];
        for (const bp of clientBreakpoints) {
            const verified = true; // In a real implementation, verify the breakpoint
            const actualBreakpoint = new debugadapter_1.Breakpoint(verified, bp.line, bp.column, bp.source);
            actualBreakpoints.push(actualBreakpoint);
        }
        this.breakpoints.set(path, actualBreakpoints);
        response.body = { breakpoints: actualBreakpoints };
        this.sendResponse(response);
    }
    threadsRequest(response) {
        response.body = {
            threads: [
                new debugadapter_1.Thread(1, 'Main Thread')
            ]
        };
        this.sendResponse(response);
    }
    stackTraceRequest(response, args) {
        // In a real implementation, this would get the actual stack trace
        const stackFrames = [
            new debugadapter_1.StackFrame(1, 'main', new debugadapter_1.Source(path.basename(args.arguments[0]?.program || 'main.astra')), 1, 0)
        ];
        response.body = {
            stackFrames: stackFrames,
            totalFrames: stackFrames.length
        };
        this.sendResponse(response);
    }
    scopesRequest(response, args) {
        const scopes = [
            new debugadapter_1.Scope('Locals', this.nextHandle++, false),
            new debugadapter_1.Scope('Globals', this.nextHandle++, false)
        ];
        response.body = { scopes };
        this.sendResponse(response);
    }
    variablesRequest(response, args) {
        const variables = [];
        // In a real implementation, this would get actual variables
        variables.push({
            name: 'example',
            value: '42',
            variablesReference: 0
        });
        response.body = { variables };
        this.sendResponse(response);
    }
    continueRequest(response, args) {
        this.sendResponse(response);
    }
    nextRequest(response, args) {
        this.sendResponse(response);
    }
    stepInRequest(response, args) {
        this.sendResponse(response);
    }
    stepOutRequest(response, args) {
        this.sendResponse(response);
    }
    evaluateRequest(response, args) {
        let result;
        let variablesReference = 0;
        // Simple evaluation - in a real implementation, this would be more sophisticated
        try {
            // eslint-disable-next-line no-eval
            result = String(eval(args.expression));
        }
        catch (e) {
            result = `Error: ${e}`;
        }
        response.body = {
            result: result,
            variablesReference: variablesReference
        };
        this.sendResponse(response);
    }
    disconnectRequest(response, args) {
        if (this.process) {
            this.process.kill();
        }
        this.sendResponse(response);
    }
}
debugadapter_1.DebugSession.run(AstraDebugSession);
//# sourceMappingURL=debugAdapter.js.map