import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash
)
from app.core.config import settings


class TestPasswordHashing:
    """Тесты для хеширования паролей"""
    
    def test_hash_password(self):
        """Тест создания хеша пароля"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")
    
    def test_verify_correct_password(self):
        """Тест проверки правильного пароля"""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_wrong_password(self):
        """Тест проверки неправильного пароля"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """Тест что разные пароли дают разные хеши"""
        password1 = "password1"
        password2 = "password2"
        
        hash1 = get_password_hash(password1)
        hash2 = get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_same_password_different_hashes(self):
        """Тест что один пароль дает разные хеши (соль)"""
        password = "testpassword123"
        
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Хеши должны быть разными из-за соли
        assert hash1 != hash2
        # Но оба должны проверяться как правильные
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Тесты для JWT токенов"""
    
    def test_create_access_token(self):
        """Тест создания access токена"""
        user_id = 123
        token = create_access_token(subject=user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_token_with_expiration(self):
        """Тест создания токена с кастомным временем истечения"""
        user_id = 123
        expires_delta = timedelta(minutes=15)
        token = create_access_token(subject=user_id, expires_delta=expires_delta)
        
        # Декодируем токен для проверки
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert "sub" in payload
        assert "exp" in payload
        assert payload["sub"] == str(user_id)
    
    def test_token_subject(self):
        """Тест что токен содержит правильный subject"""
        user_id = 456
        token = create_access_token(subject=user_id)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["sub"] == str(user_id)
    
    def test_token_with_string_subject(self):
        """Тест создания токена со строковым subject"""
        subject = "user@example.com"
        token = create_access_token(subject=subject)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["sub"] == subject
    
    def test_invalid_token_decode(self):
        """Тест что невалидный токен вызывает ошибку"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(jwt.JWTError):
            jwt.decode(invalid_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    
    def test_token_with_wrong_secret(self):
        """Тест что токен с неправильным секретом не декодируется"""
        user_id = 123
        token = create_access_token(subject=user_id)
        wrong_secret = "wrong_secret_key"
        
        with pytest.raises(jwt.JWTError):
            jwt.decode(token, wrong_secret, algorithms=[settings.ALGORITHM])


class TestSecurityIntegration:
    """Интеграционные тесты безопасности"""
    
    def test_password_and_token_workflow(self):
        """Тест полного workflow: хеширование пароля + создание токена"""
        # Создаем пользователя
        password = "userpassword123"
        user_id = 789
        
        # Хешируем пароль
        password_hash = get_password_hash(password)
        
        # Проверяем пароль
        assert verify_password(password, password_hash) is True
        
        # Создаем токен
        token = create_access_token(subject=user_id)
        
        # Декодируем токен
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        assert payload["sub"] == str(user_id)
        assert "exp" in payload