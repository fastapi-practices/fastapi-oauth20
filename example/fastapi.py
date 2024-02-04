#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from fastapi import Depends, FastAPI
from fastapi_oauth20.clients.google import GoogleOAuth20
from fastapi_oauth20.integrations.fastapi import OAuth20
from starlette.responses import PlainTextResponse

app = FastAPI()

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = 'http://localhost:8000/auth/google'

GOOGLE_OAUTH2 = GoogleOAuth20(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)


@app.get('/login/google')
async def login_google():
    return GOOGLE_OAUTH2.get_authorization_url(redirect_uri='GOOGLE_REDIRECT_URI')


@app.get('/auth/google')
async def auth_google(oauth: OAuth20 = Depends()):
    token, state = oauth
    access_token = token['access_token']
    print(access_token)
    # do something
    userinfo = GOOGLE_OAUTH2.get_userinfo(access_token)
    print(userinfo)
    # do something
    return PlainTextResponse(content='恭喜你，OAuth2 登录成功', status_code=200)
