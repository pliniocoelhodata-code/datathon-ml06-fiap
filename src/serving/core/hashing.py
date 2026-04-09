from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if the plain text password matches the hashed password.
    
    :param plain_password: Plain text password
    :param hashed_password: Hashed password
    :return: True if the passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """
    Hashes a plain text password.
    
    :param password: Plain text password
    :return: Hashed password
    """
    return pwd_context.hash(password)