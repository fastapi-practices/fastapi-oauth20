#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import uvicorn

from fastapi import Depends, FastAPI
from starlette.responses import PlainTextResponse

from fastapi_oauth20 import FastAPIOAuth20, GoogleOAuth20

app = FastAPI()

GOOGLE_CLIENT_ID = '1053650337583-ljnla4m1e5cg16erq3tld5vjflqh4bij.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'
GOOGLE_REDIRECT_URI = 'http://localhost:8000/auth/google'

google_client = GoogleOAuth20(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
oauth20 = FastAPIOAuth20(google_client, GOOGLE_REDIRECT_URI)


@app.get('/login/google')
async def login_google():
    return await google_client.get_authorization_url(redirect_uri=GOOGLE_REDIRECT_URI)


@app.get('/auth/google', response_model=None)
async def auth_google(oauth: oauth20 = Depends()):
    token, state = oauth
    access_token = token['access_token']
    print(access_token)
    # do something
    userinfo = await google_client.get_userinfo(access_token)
    print(userinfo)
    # do something
    return PlainTextResponse(content='恭喜你，OAuth2 登录成功')


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
