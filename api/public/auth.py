from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from core.auth.service import get_current_user, login, logout

router = APIRouter(prefix='/api/auth', tags=['auth'])


class LoginBody(BaseModel):
    email: str


@router.post('/login')
def login_route(body: LoginBody):
    return login(body.email)


@router.post('/logout')
def logout_route(authorization: str | None = Header(default=None)):
    logout(authorization)
    return {'ok': True}


@router.get('/me')
def me_route(user=Depends(get_current_user)):
    return {'id': user.user_id, 'email': user.email}
