import { DebugSession, InitializedEvent, TerminatedEvent, StoppedEvent, BreakpointEvent, OutputEvent, Thread, StackFrame, Scope, Source, Breakpoint } from '@vscode/debugadapter';
import { DebugProtocol } from '@vscode/debugprotocol';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';

interface AstraLaunchRequestArguments extends DebugProtocol.LaunchRequestArguments {
    program: string;
    args?: string[];
    cwd?: string;
    target?: 'py' | 'llvm' | 'native';
    stopOnEntry?: boolean;
}

class AstraDebugSession extends DebugSession {
    private process?: ChildProcess;
    private breakpoints = new Map<string, Breakpoint[]>();
    private variableHandles = new Map<number, any>();
    private nextHandle = 1;

    public constructor() {
        super();
        this.setDebuggerLinesStartAt1(true);
        this.setDebuggerColumnsStartAt1(true);
    }

    protected initializeRequest(response: DebugProtocol.InitializeResponse, args: DebugProtocol.InitializeRequestArguments): void {
        response.body = response.body || {};
        response.body.supportsConfigurationDoneRequest = true;
        response.body.supportsConditionalBreakpoints = true;
        response.body.supportsHitConditionalBreakpoints = true;
        response.body.supportsEvaluateForHovers = true;
        response.body.supportsStepBack = false;
        response.body.supportsSetVariable = true;
        this.sendResponse(response);
    }

    protected configurationDoneRequest(response: DebugProtocol.ConfigurationDoneResponse, args: DebugProtocol.ConfigurationDoneArguments): void {
        this.sendResponse(response);
    }

    protected launchRequest(response: DebugProtocol.LaunchResponse, args: AstraLaunchRequestArguments): void {
        const config = args;
        
        // Build the Astra file first
        const buildArgs = ['build', config.program, '--target', config.target || 'py'];
        
        const buildProcess = spawn('astra', buildArgs, {
            cwd: config.cwd || path.dirname(config.program)
        });

        buildProcess.on('exit', (code) => {
            if (code !== 0) {
                this.sendErrorResponse(response, 3000, `Build failed with exit code ${code}`);
                return;
            }

            // Run the compiled file
            let runCommand: string;
            let runArgs: string[] = [];

            if (config.target === 'py') {
                runCommand = 'python';
                runArgs = [config.program.replace('.astra', '.py'), ...(config.args || [])];
            } else if (config.target === 'native') {
                runCommand = config.program.replace('.astra', '');
                runArgs = config.args || [];
            } else {
                this.sendErrorResponse(response, 3001, 'Debugging for LLVM target not yet supported');
                return;
            }

            this.process = spawn(runCommand, runArgs, {
                cwd: config.cwd || path.dirname(config.program),
                stdio: ['pipe', 'pipe', 'pipe']
            });

            this.process.stdout?.on('data', (data) => {
                this.sendEvent(new OutputEvent(data.toString(), 'stdout'));
            });

            this.process.stderr?.on('data', (data) => {
                this.sendEvent(new OutputEvent(data.toString(), 'stderr'));
            });

            this.process.on('exit', (code) => {
                this.sendEvent(new TerminatedEvent());
            });

            this.process.on('error', (error) => {
                this.sendErrorResponse(response, 3002, `Process error: ${error.message}`);
            });

            this.sendResponse(response);

            if (config.stopOnEntry) {
                this.sendEvent(new StoppedEvent('entry', 1));
            }
        });

        buildProcess.on('error', (error) => {
            this.sendErrorResponse(response, 3003, `Build process error: ${error.message}`);
        });
    }

    protected setBreakPointsRequest(response: DebugProtocol.SetBreakpointsResponse, args: DebugProtocol.SetBreakpointsArguments): void {
        const path = args.source.path as string;
        const clientBreakpoints = args.breakpoints || [];
        const actualBreakpoints: Breakpoint[] = [];

        for (const bp of clientBreakpoints) {
            const verified = true; // In a real implementation, verify the breakpoint
            const actualBreakpoint = new Breakpoint(verified, bp.line, bp.column, bp.source);
            actualBreakpoints.push(actualBreakpoint);
        }

        this.breakpoints.set(path, actualBreakpoints);
        response.body = { breakpoints: actualBreakpoints };
        this.sendResponse(response);
    }

    protected threadsRequest(response: DebugProtocol.ThreadsResponse): void {
        response.body = {
            threads: [
                new Thread(1, 'Main Thread')
            ]
        };
        this.sendResponse(response);
    }

    protected stackTraceRequest(response: DebugProtocol.StackTraceResponse, args: DebugProtocol.StackTraceArguments): void {
        // In a real implementation, this would get the actual stack trace
        const stackFrames: StackFrame[] = [
            new StackFrame(1, 'main', new Source(path.basename(args.arguments[0]?.program || 'main.astra')), 1, 0)
        ];

        response.body = {
            stackFrames: stackFrames,
            totalFrames: stackFrames.length
        };
        this.sendResponse(response);
    }

    protected scopesRequest(response: DebugProtocol.ScopesResponse, args: DebugProtocol.ScopesArguments): void {
        const scopes: Scope[] = [
            new Scope('Locals', this.nextHandle++, false),
            new Scope('Globals', this.nextHandle++, false)
        ];

        response.body = { scopes };
        this.sendResponse(response);
    }

    protected variablesRequest(response: DebugProtocol.VariablesResponse, args: DebugProtocol.VariablesArguments): void {
        const variables: DebugProtocol.Variable[] = [];

        // In a real implementation, this would get actual variables
        variables.push({
            name: 'example',
            value: '42',
            variablesReference: 0
        });

        response.body = { variables };
        this.sendResponse(response);
    }

    protected continueRequest(response: DebugProtocol.ContinueResponse, args: DebugProtocol.ContinueArguments): void {
        this.sendResponse(response);
    }

    protected nextRequest(response: DebugProtocol.NextResponse, args: DebugProtocol.NextArguments): void {
        this.sendResponse(response);
    }

    protected stepInRequest(response: DebugProtocol.StepInResponse, args: DebugProtocol.StepInArguments): void {
        this.sendResponse(response);
    }

    protected stepOutRequest(response: DebugProtocol.StepOutResponse, args: DebugProtocol.StepOutArguments): void {
        this.sendResponse(response);
    }

    protected evaluateRequest(response: DebugProtocol.EvaluateResponse, args: DebugProtocol.EvaluateArguments): void {
        let result: string;
        let variablesReference = 0;

        // Simple evaluation - in a real implementation, this would be more sophisticated
        try {
            // eslint-disable-next-line no-eval
            result = String(eval(args.expression));
        } catch (e) {
            result = `Error: ${e}`;
        }

        response.body = {
            result: result,
            variablesReference: variablesReference
        };
        this.sendResponse(response);
    }

    protected disconnectRequest(response: DebugProtocol.DisconnectResponse, args: DebugProtocol.DisconnectArguments): void {
        if (this.process) {
            this.process.kill();
        }
        this.sendResponse(response);
    }
}

DebugSession.run(AstraDebugSession);
