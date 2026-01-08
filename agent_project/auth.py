import os, jwt, time
from dotenv import load_dotenv
from schemas import DB_User_Schema
from fastapi import HTTPException, status

load_dotenv()
SECRET = os.getenv("JWT_SECRET")
ALG = "HS256"
TTL_SECONDS = 60 * 30

def auth_sign_jwt(name: str) -> str:
    now = int(time.time())
    payload = {
        "sub": name,            # 谁（user_id）
        "iat": now,                # 何时签发
        "exp": now + TTL_SECONDS,  # 何时过期
    }
    token = jwt.encode(payload, SECRET, algorithm=ALG)
    return token

def auth_decode_username(token: str) -> str:
    # 会同时：1) 验签 2) 检查 exp（过期会抛异常）
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALG])
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing sub"
            )
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.InvalidTokenError:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return username

