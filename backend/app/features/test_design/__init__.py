"""테스트 설계 평가 (test-design evaluation) feature package.

A candidate is shown a Python function with a hidden list of flaws and writes,
in natural language, the flaws/edge-cases they found. An LLM-as-a-judge
semantically matches each found flaw against the hidden ground truth; P/R and a
severity-weighted quality score are then computed deterministically.
"""
