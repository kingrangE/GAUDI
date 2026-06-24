"""and-you backend application package.

Re-export the assembled FastAPI `app` so both `from app.main import app` (foundation
convention) and `from app import app` (minsu's feature tests) resolve to the same
single unified application.
"""

from app.main import app  # noqa: F401  (re-export; see docstring)
