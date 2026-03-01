from dotenv import load_dotenv
load_dotenv()
from core.server_auth import check_device_server
from core.device_fingerprint import get_device_fingerprint

fp = get_device_fingerprint()
res = check_device_server(fp)
print(res)
