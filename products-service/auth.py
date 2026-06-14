import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

load_dotenv()

SECRET_TOKEN = os.getenv("SECRET_TOKEN")

# define el esquema de seguridad — esto agrega el candado en /docs
security = HTTPBearer()

def verificar_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Token invalido")