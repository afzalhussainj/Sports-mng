import os
os.chdir(r'c:\Users\SLCW\Desktop\sports\sports_gala')

from decouple import config
from supabase import create_client

url = config('SUPABASE_URL')
key = config('SUPABASE_SERVICE_ROLE_KEY')

print(f"URL: {url}")
print(f"KEY: {key[:20]}...")

supabase = create_client(url, key)
print("Client created successfully")

res = supabase.table("slideshow_images").select("public_url,created_at").order("created_at", desc=True).limit(5).execute()
print(f"Response data: {res.data}")
print(f"Image URLs: {[row.get('public_url') for row in (res.data or []) if row.get('public_url')]}")
