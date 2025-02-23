export enum ErrorSeverity {
    LOW = 'LOW',
    MEDIUM = 'MEDIUM',
    HIGH = 'HIGH',
    CRITICAL = 'CRITICAL'
}

export interface ErrorMetadata {
    timestamp: number;
    context?: any;
    stack?: string;
}

export class AstraLinkError extends Error {
    constructor(
        message: string,
        public readonly code: string,
        public readonly severity: ErrorSeverity,
        public readonly metadata: ErrorMetadata = {
            timestamp: Date.now()
        }
    ) {
        super(message);
        this.name = 'AstraLinkError';
        this.metadata.stack = this.stack;
    }
}

export class ErrorHandler {
    private static readonly errorCallbacks: ((error: AstraLinkError) => void)[] = [];

    static handle(error: Error): void {
        const astraError = error instanceof AstraLinkError ? error : 
            new AstraLinkError(error.message, 'UNKNOWN_ERROR', ErrorSeverity.HIGH);
        
        console.error(`[${astraError.code}] ${astraError.severity}: ${astraError.message}`);
        this.errorCallbacks.forEach(callback => callback(astraError));
        
        if (astraError.severity === ErrorSeverity.CRITICAL) {
            // Implement critical error recovery
            this.handleCriticalError(astraError);
        }
    }

    static onError(callback: (error: AstraLinkError) => void): void {
        this.errorCallbacks.push(callback);
    }

    private static handleCriticalError(error: AstraLinkError): void {
        // Implement system recovery and notification
    }
}
