import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()  # <-- this loads .env file

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is missing. Check your .env file.")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_SERVICE_KEY is missing. Check your .env file.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)