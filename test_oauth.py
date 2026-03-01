from dotenv import load_dotenv
load_dotenv()

from core.supabase_client import get_supabase
import os

print("URL:", os.environ.get("SUPABASE_URL"))
client = get_supabase()

if client:
    try:
        res = client.auth.get_authorization_url(provider="google")
        print("Google OAuth url (get_authorization_url):", res)
    except Exception as e:
        print("get_authorization_url Exception:", type(e), e)
        try:
            res2 = client.auth.sign_in_with_oauth({"provider": "google"})
            print("sign_in_with_oauth url:", res2.url)
        except Exception as e2:
            print("sign_in_with_oauth Exception:", type(e2), e2)
