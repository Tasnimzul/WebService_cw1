from passlib.context import CryptContext #for hashing
#handles password

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Bcrypt is deliberately slow and computationally expensive, making brute force attacks impractical.

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
# doesn't hash the plain password and compare — it uses bcrypt's built-in verification which handles the salt internally. 
# The salt is a random value embedded in the hash that ensures two identical passwords produce different hashes, preventing rainbow table attacks.
#the plaintext password is never stored anywhere. Not in the database, not in logs, nowhere.