from dotenv import load_dotenv
load_dotenv()
from core.session_manager import SessionManager
sm = SessionManager()
res = sm.login_with_device()
print(res)
