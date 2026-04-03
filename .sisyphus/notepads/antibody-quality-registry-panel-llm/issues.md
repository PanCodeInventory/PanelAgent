## [2026-04-02] Session Start
- No issues yet

- 2026-04-02 F2 review: UI species values use localized labels ("Mouse (小鼠)", "Human (人)") but backend inventory resolution only maps "Mouse"/"Human", so candidate lookup from the shipped UI will miss inventory files.
- 2026-04-02 F2 review: `candidate_confirm` and `resolve_review` accept arbitrary `EntityKey` payloads without checking species/marker/brand against the issue feedback key, which can corrupt registry identity/projections.
- 2026-04-02 F2 review: quality context is markdown-sanitized but not prompt-sanitized before prompt injection in `panel_generator.py`, so user issue text can steer the LLM.
- 2026-04-02 F2 review: candidate lookup swallows inventory load failures and returns `[]` with no logging, making operational issues indistinguishable from no matches.
