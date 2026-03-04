import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# NOTE: read env vars inside `get_supabase()` to avoid stale module-level values
# when the .env file is created or modified after the process imported this module.

# Cache for the client
_client = None

def get_supabase() -> Client:
    """
    Lazy-loads and returns a Supabase client using the service role key 
    to bypass Row Level Security (RLS) for backend operations.
    This defers initialization until first use, allowing the server to start
    even with invalid/dummy credentials.
    """
    global _client
    
    if _client is not None:
        return _client
    
    # Refresh environment variables at call time
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        # don't crash; allow offline/dummy mode
        print("⚠ Supabase credentials not found, operating in offline mode.")
        return None
    
    try:
        _client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        print("✓ Supabase client initialized successfully")
        return _client
    except Exception as e:
        print(f"⚠ Supabase initialization failed: {e}")
        print("  (Using dummy database mode - app will function but DB operations will fail)")
        # Don't raise; allow the server to continue running
        return None
