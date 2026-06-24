"""명세 설계 (spec-design) evaluation.

Measures **instruction specificity / technical understanding** by running the
candidate's single instruction N times at extreme temperature and scoring how
*consistent* the outputs are. A concrete instruction constrains the solution space, so
the samples agree (high consistency); a vague one lets the model fill gaps differently
each run, so they diverge (low consistency).
"""
