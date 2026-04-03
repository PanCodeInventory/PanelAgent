## [2026-04-02] Architecture Decisions
- Dual-key identity: feedback_key (species+marker+fluorochrome+brand, clone optional) + entity_key (species+marker+clone+brand+catalog)
- Lot number tracked as metadata, not part of identity key
- Three-layer storage: raw_issue_record, audit_event (immutable), organized_projection
- Context-only LLM injection (no hard filtering)
- Auto-trigger candidate lookup with single-select confirmation modal
- No-match -> manual review queue with pending_review status
