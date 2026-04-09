from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.serving.core.database import get_db
from src.serving.core.security import create_access_token, refresh_token
from src.serving.crud.users import authenticate_user
from src.serving.schemas.user import RefreshTokenRequest, TokenResponse

router = APIRouter()

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login to obtain an access token"
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Logs in a user and returns an access token.
    
    - Requires username and password.
    - Returns a JWT token if successful.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return TokenResponse(access_token=access_token, token_type="bearer")

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token"
)
async def refresh_access_token(
    request: Request,
    refresh_token_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Refreshes the access token using a refresh token.
    
    - Requires a valid refresh token.
    - Returns a new access token if successful.
    """
    new_access_token = await refresh_token(refresh_token=refresh_token_request.refresh_token, db=db)
    return TokenResponse(access_token=new_access_token, token_type="bearer")