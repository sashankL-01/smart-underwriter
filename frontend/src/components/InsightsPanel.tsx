import { } from "react";

type InsightsPanelProps = {
    claimText: string;
    onClaimChange: (value: string) => void;
    onAnalyze: () => void;
    statusMessage: string;
    decision: string | null;
    rationale: string | null;
    riskLevel: string | null;
    citations: Array<{ quote: string; page_number: number; source_filename: string; policy_id: string; text: string }>;
    selectedQuote: string | null;
    onQuoteSelect: (quote: string) => void;
    isAnalyzing: boolean;
};

export default function InsightsPanel({
    claimText,
    onClaimChange,
    onAnalyze,
    statusMessage,
    decision,
    rationale,
    riskLevel,
    citations,
    selectedQuote,
    onQuoteSelect,
    isAnalyzing
}: InsightsPanelProps) {
    const highlightQuote = (text: string, quote: string) => {
        if (!quote) return text;
        const regex = new RegExp(`(${quote.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<mark class="chunk-highlight">$1</mark>');
    };

    return (
        <div className="insights">
            <label>
                Claim description
                <textarea
                    value={claimText}
                    onChange={(event) => onClaimChange(event.target.value)}
                    placeholder="Describe the claim..."
                    rows={8}
                />
            </label>
            <button onClick={onAnalyze} disabled={isAnalyzing}>
                {isAnalyzing ? (
                    <>
                        <div className="spinner-small"></div>
                        Analyzing...
                    </>
                ) : (
                    "Analyze claim"
                )}
            </button>
            <div className="insights-output">
                <p className="status">{statusMessage}</p>
                {decision ? (
                    <div className="analysis">
                        <h3>Status</h3>
                        <p className="decision-badge">{decision.replace(/-/g, ' ').toUpperCase()}</p>
                        <h3>Risk Level</h3>
                        <p className={`risk-level risk-${riskLevel}`}>{riskLevel?.toUpperCase()}</p>
                        <h3>Rationale</h3>
                        <p>{rationale}</p>
                        <h3>Evidence</h3>
                        <div className="chunks-list">
                            {citations.map((citation, index) => (
                                <div
                                    key={index}
                                    className={`chunk-card ${selectedQuote === citation.quote ? 'active' : ''}`}
                                    onClick={() => onQuoteSelect(citation.quote)}
                                >
                                    <div className="chunk-meta">
                                        <span className="chunk-badge">Page {citation.page_number}</span>
                                        <span className="chunk-badge">{citation.source_filename}</span>
                                        <span className="chunk-badge">ID: {citation.policy_id}</span>
                                    </div>
                                    <div
                                        className="chunk-text"
                                        dangerouslySetInnerHTML={{
                                            __html: highlightQuote(citation.text || citation.quote, citation.quote)
                                        }}
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                ) : null}
            </div>
        </div>
    );
}
