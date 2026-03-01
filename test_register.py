from dotenv import load_dotenv
load_dotenv()
from core.server_auth import register_device_server, check_device_server
from core.device_fingerprint import get_device_fingerprint
import sys
import traceback

with open("test_out.txt", "w", encoding="utf8") as f:
    sys.stdout = f
    sys.stderr = f
    fp = get_device_fingerprint()
    print("FP:", fp)

    try:
        check_res = check_device_server(fp)
        print("Check:", check_res)
    except Exception as e:
        print("Check Error:")
        traceback.print_exc()

    try:    
        res = register_device_server(fp, password_hash="", machine_name="Test")
        print("Register details:")
        if isinstance(res, dict) and "message" in res:
            print("message:", res["message"])
        print("Response:", res)
    except Exception as e:
        print("Register Error:")
        traceback.print_exc()
