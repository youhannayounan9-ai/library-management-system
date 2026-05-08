from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash_val = "$2b$12$Z/gEpJk2YfBajM5ZFeLvP.1AEc60O9cDPfECDI7UIy4gmIy4TfLX2"
password = "password"

result = pwd_context.verify(password, hash_val)
print(f"Verification Result: {result}")
