"""Central LLM seam for the backend (config + client).

All LLM calls go through `LLMClient.complete`, the single patchable seam unit tests
mock. Provider/model selection is centralized in `llm.config` — never hardcode model
IDs or secrets at a call site.
"""
