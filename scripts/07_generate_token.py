
import os
import time
import jwt
from dotenv import load_dotenv

load_dotenv()

now = int(time.time())

# payload = {
#     "sub": "COGNITO_SUB_LIMITED_USER",
#     "iss": os.environ["JWT_ISSUER"],
#     "aud": os.environ["JWT_AUDIENCE"],
#     "iat": now,
#     "exp": now + 3600
# }

payload = {
    "sub": "COGNITO_SUB_FULL_ACCESS_USER",
    "iss": os.environ["JWT_ISSUER"],
    "aud": os.environ["JWT_AUDIENCE"],
    "iat": now,
    "exp": now + 3600
}

token = jwt.encode(
    payload,
    os.environ["JWT_SECRET_KEY"],
    algorithm="HS256"
)

print(token)
