# Step01 optional dependency and IP inventory

These packages support offline Step01 research audits only. They are not core
runtime dependencies, are not required for edge inference, and are not evidence
of physical validation.

| Package | Pinned version | Step01 purpose | Runtime status | License family |
|---|---:|---|---|---|
| Pint | 0.25.3 | Parse declared units and check dimensional compatibility | Optional, offline audit only | BSD |
| SymPy | 1.14.0 | Check explicitly coded symbolic identities without evaluating equation text | Optional, offline audit only | BSD |
| pydoe | 1.5.0 | Build deterministic DOE matrices from explicitly supplied factor levels | Optional, offline research planning only | BSD-3-Clause |

The installed distribution metadata identifies Pint and SymPy with the OSI BSD
license classifier and pydoe with the BSD-3-Clause license expression. Review
upstream license texts before redistribution; this inventory is not legal advice.

