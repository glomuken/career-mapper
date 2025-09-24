import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://vcurrwcmfkfwpvihgzls.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZjdXJyd2NtZmtmd3B2aWhnemxzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc5MzI5NzksImV4cCI6MjA3MzUwODk3OX0.Kzz7K2b_6Y8tXfXliCFvI4-Mgp2gOfrsQ9M8LlFDnEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
