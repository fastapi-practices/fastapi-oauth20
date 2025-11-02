#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import httpx

TEST_CLIENT_ID = 'test_client_id'
TEST_CLIENT_SECRET = 'test_client_secret'
TEST_ACCESS_TOKEN = 'test_access_token'
INVALID_TOKEN = 'invalid_token'
TEST_STATE = 'test_state'


def create_mock_user_data(provider_name: str, **overrides):
    """Create mock user data for a specific provider with optional overrides."""
    MOCK_USER_DATA = {
        'github': {
            'id': 123456,
            'login': 'testuser',
            'name': 'Test User',
            'email': 'test@example.com',
            'bio': 'Test bio',
            'location': 'Test Location',
        },
        'google': {
            'id': '123456789',
            'email': 'test@gmail.com',
            'name': 'Test User',
            'picture': 'https://lh3.googleusercontent.com/test.jpg',
        },
        'gitee': {
            'id': 123456,
            'login': 'testuser',
            'name': 'Test User',
            'email': 'test@example.com',
            'avatar_url': 'https://avatar.example.com/testuser.png',
        },
        'feishu': {
            'user_id': 'test_user_123',
            'employee_id': 'emp_456',
            'name': 'Test User',
            'email': 'test@example.com',
            'mobile': '13800000000',
        },
        'linuxdo': {
            'id': 123456,
            'username': 'testuser',
            'name': 'Test User',
            'email': 'test@example.com',
            'avatar_url': 'https://linux.do/avatar/testuser.png',
        },
        'oschina': {
            'id': 123456,
            'name': 'Test User',
            'email': 'test@example.com',
            'avatar': 'https://oschina.net/img/test.jpg',
        },
    }

    base_data = MOCK_USER_DATA.get(provider_name, {}).copy()
    base_data.update(overrides)
    return base_data


def mock_user_info_response(respx_mock, user_info_url: str, user_data: dict, status_code: int = 200):
    """Mock user info endpoint response."""
    return respx_mock.get(user_info_url).mock(return_value=httpx.Response(status_code, json=user_data))
