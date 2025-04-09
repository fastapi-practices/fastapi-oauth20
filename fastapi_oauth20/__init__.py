#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from .clients.feishu import FeiShuOAuth20 as FeiShuOAuth20
from .clients.gitee import GiteeOAuth20 as GiteeOAuth20
from .clients.github import GitHubOAuth20 as GitHubOAuth20
from .clients.google import GoogleOAuth20 as GoogleOAuth20
from .clients.linuxdo import LinuxDoOAuth20 as LinuxDoOAuth20
from .clients.oschina import OSChinaOAuth20 as OSChinaOAuth20
from .integrations.fastapi import FastAPIOAuth20 as FastAPIOAuth20

__version__ = '0.0.1'
