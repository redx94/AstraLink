/**
 * AstraLink - Configuration Module
 * ============================
 *
 * This module defines the configuration interface and default settings for
 * AI models, quantum systems, and material discovery parameters.
 *
 * Developer: Reece Dixon
 * Copyright © 2025 AstraLink. All rights reserved.
 * See LICENSE file for licensing information.
 */

export interface AstraLinkConfig {
    aiSettings: {
        modelEndpoint: string;
        apiKey: string;
    };
    quantumSettings: {
        errorCorrectionEnabled: boolean;
        qubitCount: number;
    };
    materialDiscovery: {
        searchParameters: {
            temperature: number;
            pressure: number;
        };
    };
}

export const defaultConfig: AstraLinkConfig = {
    aiSettings: {
        modelEndpoint: 'http://localhost:8080',
        apiKey: process.env.AI_API_KEY || '',
    },
    quantumSettings: {
        errorCorrectionEnabled: true,
        qubitCount: 5,
    },
    materialDiscovery: {
        searchParameters: {
            temperature: 298,
            pressure: 1,
        },
    },
};
