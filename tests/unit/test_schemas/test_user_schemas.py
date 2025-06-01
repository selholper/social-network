import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserUpdate, User, UserBasic


class TestUserCreate:
    """Тесты для схемы создания пользователя"""
    
    def test_valid_user_create(self):
        """Тест валидного создания пользователя"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User"
        }
        user = UserCreate(**user_data)
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "password123"
        assert user.full_name == "Test User"
    
    def test_user_create_minimal_data(self):
        """Тест создания пользователя с минимальными данными"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
        user = UserCreate(**user_data)
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "password123"
        assert user.full_name is None
    
    def test_user_create_invalid_email(self):
        """Тест создания пользователя с невалидным email"""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "password123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        assert "email" in str(exc_info.value)
    
    def test_user_create_missing_required_fields(self):
        """Тест создания пользователя без обязательных полей"""
        user_data = {
            "username": "testuser"
            # Отсутствуют email и password
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        errors = str(exc_info.value)
        assert "email" in errors
        assert "password" in errors
    
    def test_username_alphanumeric_validation(self):
        """Тест валидации что username должен быть буквенно-цифровым"""
        user_data = {
            "username": "test@user",  # Содержит недопустимый символ
            "email": "test@example.com",
            "password": "password123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        assert "alphanumeric" in str(exc_info.value)


class TestUserUpdate:
    """Тесты для схемы обновления пользователя"""
    
    def test_user_update_partial(self):
        """Тест частичного обновления пользователя"""
        update_data = {
            "full_name": "Updated Name"
        }
        user_update = UserUpdate(**update_data)
        
        assert user_update.full_name == "Updated Name"
        assert user_update.username is None
        assert user_update.email is None
    
    def test_user_update_all_fields(self):
        """Тест обновления всех полей пользователя"""
        update_data = {
            "username": "newusername",
            "email": "new@example.com",
            "full_name": "New Full Name",
            "bio": "New bio",
            "avatar_url": "https://example.com/avatar.jpg",
            "password": "newpassword123"
        }
        user_update = UserUpdate(**update_data)
        
        assert user_update.username == "newusername"
        assert user_update.email == "new@example.com"
        assert user_update.full_name == "New Full Name"
        assert user_update.bio == "New bio"
        assert user_update.avatar_url == "https://example.com/avatar.jpg"
        assert user_update.password == "newpassword123"
    
    def test_user_update_empty(self):
        """Тест пустого обновления пользователя"""
        user_update = UserUpdate()
        
        assert user_update.username is None
        assert user_update.email is None
        assert user_update.full_name is None
        assert user_update.bio is None
        assert user_update.avatar_url is None
        assert user_update.password is None


class TestUserResponse:
    """Тесты для схемы ответа пользователя"""
    
    def test_user_response_from_dict(self):
        """Тест создания User из словаря"""
        from datetime import datetime
        
        user_data = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "bio": "Test bio",
            "avatar_url": "https://example.com/avatar.jpg",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        user = User(**user_data)
        
        assert user.id == 1
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
    
    def test_user_basic_minimal_fields(self):
        """Тест UserBasic с минимальными полями"""
        user_data = {
            "id": 1,
            "username": "testuser"
        }
        
        user_basic = UserBasic(**user_data)
        
        assert user_basic.id == 1
        assert user_basic.username == "testuser"
        assert user_basic.full_name is None
        assert user_basic.avatar_url is None


class TestUserSchemaValidation:
    """Тесты валидации схем пользователя"""
    
    def test_email_validation_cases(self):
        """Тест различных случаев валидации email"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@example.com"
        ]
        
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test.example.com",
            ""
        ]
        
        # Тестируем валидные email
        for email in valid_emails:
            user_data = {
                "username": "testuser",
                "email": email,
                "password": "password123"
            }
            user = UserCreate(**user_data)
            assert user.email == email
        
        # Тестируем невалидные email
        for email in invalid_emails:
            user_data = {
                "username": "testuser",
                "email": email,
                "password": "password123"
            }
            with pytest.raises(ValidationError):
                UserCreate(**user_data)
    
    def test_username_validation_cases(self):
        """Тест различных случаев валидации username"""
        valid_usernames = [
            "testuser",
            "user123",
            "123user",
            "TestUser"
        ]
        
        invalid_usernames = [
            "test@user",
            "test user",
            "test-user",
            "test.user",
            ""
        ]
        
        # Тестируем валидные username
        for username in valid_usernames:
            user_data = {
                "username": username,
                "email": "test@example.com",
                "password": "password123"
            }
            user = UserCreate(**user_data)
            assert user.username == username
        
        # Тестируем невалидные username
        for username in invalid_usernames:
            user_data = {
                "username": username,
                "email": "test@example.com",
                "password": "password123"
            }
            with pytest.raises(ValidationError):
                UserCreate(**user_data)