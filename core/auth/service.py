from __future__ import annotations

import secrets
from typing import Optional

from fastapi import Header, HTTPException, Query

from storage.db import SessionLocal
from storage.models import Session, User


class AuthenticatedUser:
    def __init__(self, user_id: str, email: str):
        self.user_id = user_id
        self.email = email


def login(email: str) -> dict:
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, display_name=email.split('@')[0])
            db.add(user)
            db.commit()
            db.refresh(user)
        token = secrets.token_urlsafe(32)
        session = Session(user_id=user.id, token=token)
        db.add(session)
        db.commit()
        return {'token': token, 'user': {'id': user.id, 'email': user.email, 'display_name': user.display_name}}


def get_current_user(authorization: Optional[str] = Header(default=None), token_passthrough: Optional[str] = Query(default=None)) -> AuthenticatedUser:
    token = None
    if authorization and authorization.startswith('Bearer '):
        token = authorization.split(' ', 1)[1].strip()
    elif token_passthrough:
        token = token_passthrough
    if not token:
        raise HTTPException(status_code=401, detail='Missing bearer token')
    with SessionLocal() as db:
        session = db.query(Session).filter(Session.token == token, Session.active.is_(True)).first()
        if not session:
            raise HTTPException(status_code=401, detail='Invalid session')
        user = db.query(User).filter(User.id == session.user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail='User not found')
        return AuthenticatedUser(user_id=user.id, email=user.email)


def logout(authorization: Optional[str]) -> None:
    if not authorization or not authorization.startswith('Bearer '):
        return
    token = authorization.split(' ', 1)[1].strip()
    with SessionLocal() as db:
        session = db.query(Session).filter(Session.token == token, Session.active.is_(True)).first()
        if session:
            session.active = False
            db.commit()
