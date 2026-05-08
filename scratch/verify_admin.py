from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash_val = "$2b$12$.wg/BzrWpfqpr5vqyAtsRuggZ28iaFLbBd7ggosWNMAINx1NZ8J4a"
password = "admin123"

result = pwd_context.verify(password, hash_val)
print(f"Verification Result: {result}")
