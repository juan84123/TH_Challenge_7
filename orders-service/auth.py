import os
from fastapi import HTTPException, Header
from dotenv import load_dotenv

load_dotenv()

SECRET_TOKEN = os.getenv("SECRET_TOKEN")

# verifica que el token del header sea el correcto
def verificar_token(authorization: str = Header(...)):
    if authorization != f"Bearer {SECRET_TOKEN}":
        raise HTTPException(status_code=401, detail="Token invalido")