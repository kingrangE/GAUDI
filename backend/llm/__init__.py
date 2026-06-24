"""Shared LLM infrastructure (provider/model config + client seam) for the backend.

All LLM / LLM-as-judge calls go through `llm.client.LLMClient.complete`, which unit tests
patch with a fake so they never hit the network or need a key.
"""
