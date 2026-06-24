"""Mock-exam (모의고사) results domain.

The mock exam weaves five of the practice features into one scenario
(test-design, dev-prompting, spec-design, rejection-eval, context-engineering).
This package owns the *cross-feature* record of a candidate's mock-exam attempt
and the admin-facing read API over it.

Practice runs never touch these tables, so the admin view is structurally
limited to mock-exam results only.
"""
