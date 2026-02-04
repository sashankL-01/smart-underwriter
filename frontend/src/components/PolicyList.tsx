type PolicyListProps = {
    policies: Array<{
        policy_id: string;
        source_filename?: string | null;
        jurisdiction?: string | null;
        claim_type?: string | null;
        chunks_indexed?: number | null;
    }>;
    selectedPolicyId: string;
    onSelect: (policyId: string) => void;
};

export default function PolicyList({
    policies,
    selectedPolicyId,
    onSelect
}: PolicyListProps) {
    return (
        <div className="policy-list">
            <h3>Ingested policies</h3>
            {policies.length === 0 ? (
                <p className="muted">No policies ingested yet.</p>
            ) : (
                <ul>
                    {policies.map((policy) => (
                        <li key={policy.policy_id}>
                            <button
                                className={
                                    policy.policy_id === selectedPolicyId
                                        ? "policy-button active"
                                        : "policy-button"
                                }
                                onClick={() => onSelect(policy.policy_id)}
                            >
                                {policy.policy_id}
                            </button>
                            <span className="policy-meta">
                                {policy.source_filename ?? "Unknown file"}
                            </span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
