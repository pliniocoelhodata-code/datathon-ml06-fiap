from sqlalchemy.orm import Session

from src.serving.core.hashing import hash_password, verify_password
from src.serving.models.user import User
from src.serving.schemas.user import UserResponse

def get_user_by_username(db: Session, username: str) -> User | None:
    """
    Get a user by their username from the database.
    
    :param db: Database session
    :param username: Username of the user to retrieve
    :return: User object if found, else None
    """
    return db.query(User).filter(User.username == username).first()

def authenticate_user(
    db: Session, 
    username: str, 
    password: str
) -> UserResponse | None:
    """
    Authenticate a user by checking their username and password.
    
    :param db: Database session
    :param username: Username of the user
    :param password: Password of the user
    :return: User object if authentication is successful, else None
    """
    user = get_user_by_username(db, username)
    if user and verify_password(password, user.hashed_password):
        return user
    
    return None

def create_user(db: Session, username: str, password: str) -> UserResponse | None:
    """
    Create a new user in the database.
    
    :param db: Database session
    :param username: Username of the new user
    :param password: Password of the new user
    :return: User object of the newly created user
    """
    if get_user_by_username(db, username):
        return None
    
    hashed_password = hash_password(password)
    new_user = User(username=username, hashed_password=hashed_password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse.model_validate(new_user)

