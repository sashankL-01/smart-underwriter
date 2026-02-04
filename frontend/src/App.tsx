/// <reference types="vite/client" />

import { useEffect, useState } from "react";
import InsightsPanel from "./components/InsightsPanel.tsx";
import PolicyList from "./components/PolicyList";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
const DEBUG = import.meta.env.VITE_DEBUG === "true";

const logDebug = (message: string, data?: unknown) => {
    if (!DEBUG) {
        return;
    }
    if (data !== undefined) {
        console.debug(`[Smart Underwriter] ${message}`, data);
    } else {
        console.debug(`[Smart Underwriter] ${message}`);
    }
};

export default function App() {
    const [claimText, setClaimText] = useState("");
    const [selectedQuote, setSelectedQuote] = useState<string | null>(null);
    const [statusMessage, setStatusMessage] = useState<string>(
        "Upload policies to begin."
    );
    const [notification, setNotification] = useState<string | null>(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analysis, setAnalysis] = useState<{
        decision: string;
        rationale: string;
        risk_level: string;
        citations: Array<{ quote: string; page_number: number; source_filename: string; policy_id: string; text: string }>;
    } | null>(null);
    const [policies, setPolicies] = useState<
        Array<{
            policy_id: string;
            source_filename?: string | null;
            chunks_indexed?: number | null;
        }>
    >([]);

    const refreshPolicies = async () => {
        try {
            logDebug("Fetching policies");
            const response = await fetch(`${API_BASE}/policies`);
            if (!response.ok) {
                logDebug("Policies fetch failed", { status: response.status });
                return;
            }
            const data = await response.json();
            logDebug("Policies fetched", { count: data?.length ?? 0 });
            setPolicies(data);
        } catch (error) {
            logDebug("Policies fetch error", error);
        }
    };

    useEffect(() => {
        refreshPolicies();
    }, []);

    const handleUpload = async (file: File) => {
        setIsUploading(true);
        try {
            const formData = new FormData();
            formData.append("file", file);

            const policyId = `policy-${Date.now()}`;
            const searchParams = new URLSearchParams({ policy_id: policyId });

            logDebug("Uploading policy", { policyId, filename: file.name });
            setStatusMessage(`Uploading ${file.name}...`);

            const response = await fetch(`${API_BASE}/ingest?${searchParams.toString()}`, {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                logDebug("Policy ingest failed", { status: response.status });
                setStatusMessage("Failed to ingest policy.");
                return;
            }

            const data = await response.json();
            logDebug("Policy ingested", data);
            setStatusMessage(`Ingested ${data.chunks_indexed} chunks from ${file.name}.`);
            setNotification(`✓ Successfully ingested ${data.chunks_indexed} chunks from ${file.name}`);
            setTimeout(() => setNotification(null), 4000);
            setAnalysis(null);
            setSelectedQuote(null);
            refreshPolicies();
        } catch (error) {
            logDebug("Policy ingest error", error);
            setStatusMessage("Failed to ingest policy.");
        } finally {
            setIsUploading(false);
        }
    };

    const handleAnalyze = async () => {
        if (!claimText.trim()) {
            setStatusMessage("Enter a claim description.");
            return;
        }

        setIsAnalyzing(true);
        try {
            logDebug("Analyzing claim");
            setStatusMessage("Analyzing claim...");

            const response = await fetch(`${API_BASE}/analyze`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    policy_id: "global",
                    claim_text: claimText
                })
            });

            if (!response.ok) {
                logDebug("Analyze failed", { status: response.status });
                setStatusMessage("Failed to analyze claim.");
                return;
            }

            const data = await response.json();
            logDebug("Analysis response", data);
            setAnalysis(data);
            setStatusMessage("Analysis complete.");
            setSelectedQuote(null);
        } catch (error) {
            logDebug("Analyze error", error);
            setStatusMessage("Failed to analyze claim.");
        } finally {
            setIsAnalyzing(false);
        }
    };

    return (
        <div className="app">
            {notification && (
                <div className="toast-notification">
                    {notification}
                </div>
            )}
            <header className="header">
                <div className="title-section">
                    <h1 className="app-title">
                        <span className="title-icon">🛡️</span>
                        Smart Underwriter
                    </h1>
                    <p className="tagline">AI-Powered Insurance Policy Analysis</p>
                </div>
                <div className="controls">
                    <label className="upload">
                        {isUploading ? "Uploading..." : "Upload Policy PDF"}
                        <input
                            type="file"
                            accept="application/pdf"
                            disabled={isUploading}
                            onChange={(event) => {
                                const file = event.target.files?.[0];
                                if (file) {
                                    handleUpload(file);
                                }
                            }}
                        />
                    </label>
                    {isUploading && <div className="spinner"></div>}
                </div>
            </header>

            <main className="main-single">
                <section className="panel-full">
                    <InsightsPanel
                        claimText={claimText}
                        onClaimChange={setClaimText}
                        onAnalyze={handleAnalyze}
                        statusMessage={statusMessage}
                        decision={analysis?.decision ?? null}
                        rationale={analysis?.rationale ?? null}
                        riskLevel={analysis?.risk_level ?? null}
                        citations={analysis?.citations ?? []}
                        selectedQuote={selectedQuote}
                        onQuoteSelect={setSelectedQuote}
                        isAnalyzing={isAnalyzing}
                    />
                    <PolicyList
                        policies={policies}
                        selectedPolicyId=""
                        onSelect={() => { }}
                    />
                </section>
            </main>
        </div>
    );
}
