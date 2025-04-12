/**
 * AstraLink - Error Handling Module
 * ===============================
 *
 * This module provides centralized error handling with severity levels,
 * error tracking, and critical error recovery mechanisms.
 *
 * Developer: Reece Dixon
 * Copyright © 2025 AstraLink. All rights reserved.
 * See LICENSE file for licensing information.
 */

export enum ErrorSeverity {
    LOW = 'LOW',
    MEDIUM = 'MEDIUM',
    HIGH = 'HIGH',
    CRITICAL = 'CRITICAL'
}

export interface ErrorMetadata {
    timestamp: number;
    correlationId?: string;
    context?: any;
    stack?: string;
}

export interface MetricsClient {
    incrementErrorCount(errorType: string, severity: ErrorSeverity): void;
    observeErrorDuration(errorType: string, duration: number): void;
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

    toJSON() {
        return {
            code: this.code,
            message: this.message,
            severity: this.severity,
            metadata: this.metadata
        };
    }
}

export class ErrorHandler {
    private static readonly errorCallbacks: ((error: AstraLinkError) => void)[] = [];
    private static metricsClient: MetricsClient;
    private static reloadAttempts = 0;
    private static readonly MAX_RELOAD_ATTEMPTS = 3;

    static initialize(metricsClient: MetricsClient): void {
        this.metricsClient = metricsClient;
        this.reloadAttempts = 0;
    }

    static handle(error: Error, correlationId?: string): void {
        const startTime = Date.now();
        const astraError = error instanceof AstraLinkError ? error :
            new AstraLinkError(error.message, 'UNKNOWN_ERROR', ErrorSeverity.HIGH);
        
        if (correlationId) {
            astraError.metadata.correlationId = correlationId;
        }
        
        // Track error metrics
        if (this.metricsClient) {
            this.metricsClient.incrementErrorCount(astraError.code, astraError.severity);
            this.metricsClient.observeErrorDuration(astraError.code, Date.now() - startTime);
        }

        // Notify error subscribers
        this.errorCallbacks.forEach(callback => callback(astraError));
        
        if (astraError.severity === ErrorSeverity.CRITICAL) {
            this.handleCriticalError(astraError);
        }
    }

    static onError(callback: (error: AstraLinkError) => void): void {
        this.errorCallbacks.push(callback);
    }

    private static handleCriticalError(error: AstraLinkError): void {
        // Persist error for post-mortem analysis
        try {
            localStorage.setItem(`critical_error_${Date.now()}`, JSON.stringify(error.toJSON()));
        } catch (e) {
            // Ignore storage errors
        }
        
        // Attempt graceful shutdown of critical systems
        this.errorCallbacks
            .filter(callback => callback.name === 'criticalSystemHandler')
            .forEach(callback => callback(error));
            
        // Force reload if critical systems are unresponsive, with retry limit
        if (error.code.startsWith('SYSTEM_') && this.reloadAttempts < this.MAX_RELOAD_ATTEMPTS) {
            this.reloadAttempts++;
            setTimeout(() => {
                if (document.visibilityState === 'visible') {
                    window.location.reload();
                }
            }, 5000);
        } else if (this.reloadAttempts >= this.MAX_RELOAD_ATTEMPTS) {
            // Log system as critically failed and notify monitoring
            if (this.metricsClient) {
                this.metricsClient.incrementErrorCount('SYSTEM_CRITICAL_FAILURE', ErrorSeverity.CRITICAL);
            }
        }
    }
}
