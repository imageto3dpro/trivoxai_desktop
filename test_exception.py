from dotenv import load_dotenv
load_dotenv()
from core.supabase_client import get_supabase
import json

sb = get_supabase()
try:
    res = sb.rpc("register_device_server", {
        "p_fingerprint": "debug2",
        "p_password_hash": "",
        "p_machine_name": "debug",
        "p_platform": "debug",
        "p_app_version": "1"
    }).execute()
    print("Success:", res)
except Exception as e:
    print("Exception type:", type(e))
    print("Exception dict?:", isinstance(e, dict))
    print("Has message?:", hasattr(e, 'message'))
    print("Has details?:", hasattr(e, 'details'))
    if hasattr(e, 'to_dict'):
        print("to_dict() exists")
    print("Exception str:", str(e))
    if hasattr(e, '__dict__'):
        print("__dict__:", e.__dict__)
