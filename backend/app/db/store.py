"""Store facade — routes to Supabase or in-memory backend based on config.

All API/agent code imports from here:  ``from app.db import store``

Set STORE_BACKEND=memory in .env (or environment) to use the in-memory
store for local development without a Supabase connection.
"""

from app.config import settings

if settings.store_backend == "memory":
    from app.db.memory_store import *  # noqa: F401, F403
else:
    from app.db.supabase_store import *  # noqa: F401, F403
