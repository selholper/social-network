import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.core.security import get_password_hash


class TestUserModel:
    """Тесты для модели User"""
    
    def test_create_user(self, db_session):
        """Тест создания пользователя"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            full_name="Test User"
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_superuser is False
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
    
    def test_user_unique_username(self, db_session):
        """Тест уникальности username"""
        # Создаем первого пользователя
        user1 = User(
            username="testuser",
            email="test1@example.com",
            password_hash=get_password_hash("password123")
        )
        db_session.add(user1)
        db_session.commit()
        
        # Пытаемся создать второго пользователя с тем же username
        user2 = User(
            username="testuser",  # Дублирующийся username
            email="test2@example.com",
            password_hash=get_password_hash("password123")
        )
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_unique_email(self, db_session):
        """Тест уникальности email"""
        # Создаем первого пользователя
        user1 = User(
            username="testuser1",
            email="test@example.com",
            password_hash=get_password_hash("password123")
        )
        db_session.add(user1)
        db_session.commit()
        
        # Пытаемся создать второго пользователя с тем же email
        user2 = User(
            username="testuser2",
            email="test@example.com",  # Дублирующийся email
            password_hash=get_password_hash("password123")
        )
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_default_values(self, db_session):
        """Тест значений по умолчанию"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash("password123")
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Проверяем значения по умолчанию
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.full_name is None
        assert user.bio is None
        assert user.avatar_url is None
    
    def test_user_timestamps(self, db_session):
        """Тест автоматических временных меток"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash("password123")
        )
        
        before_creation = datetime.utcnow()
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        after_creation = datetime.utcnow()
        
        # Проверяем что created_at установлен правильно
        assert before_creation <= user.created_at <= after_creation
        assert before_creation <= user.updated_at <= after_creation
        
        # Проверяем что created_at и updated_at примерно равны при создании
        time_diff = abs((user.updated_at - user.created_at).total_seconds())
        assert time_diff < 1  # Разница меньше секунды
    
    def test_user_update_timestamp(self, db_session):
        """Тест обновления временной метки при изменении"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash("password123")
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        original_updated_at = user.updated_at
        
        # Небольшая задержка чтобы время изменилось
        import time
        time.sleep(0.1)
        
        # Обновляем пользователя
        user.full_name = "Updated Name"
        db_session.commit()
        db_session.refresh(user)
        
        # Проверяем что updated_at изменился
        assert user.updated_at > original_updated_at
    
    def test_user_superuser_flag(self, db_session):
        """Тест флага суперпользователя"""
        # Обычный пользователь
        regular_user = User(
            username="regular",
            email="regular@example.com",
            password_hash=get_password_hash("password123"),
            is_superuser=False
        )
        
        # Суперпользователь
        super_user = User(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("password123"),
            is_superuser=True
        )
        
        db_session.add_all([regular_user, super_user])
        db_session.commit()
        
        assert regular_user.is_superuser is False
        assert super_user.is_superuser is True
    
    def test_user_active_flag(self, db_session):
        """Тест флага активности пользователя"""
        # Активный пользователь
        active_user = User(
            username="active",
            email="active@example.com",
            password_hash=get_password_hash("password123"),
            is_active=True
        )
        
        # Неактивный пользователь
        inactive_user = User(
            username="inactive",
            email="inactive@example.com",
            password_hash=get_password_hash("password123"),
            is_active=False
        )
        
        db_session.add_all([active_user, inactive_user])
        db_session.commit()
        
        assert active_user.is_active is True
        assert inactive_user.is_active is False
    
    def test_user_optional_fields(self, db_session):
        """Тест опциональных полей пользователя"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            full_name="Test User",
            bio="This is a test user bio",
            avatar_url="https://example.com/avatar.jpg"
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.full_name == "Test User"
        assert user.bio == "This is a test user bio"
        assert user.avatar_url == "https://example.com/avatar.jpg"
    
    def test_user_password_hash_not_plain_text(self, db_session):
        """Тест что пароль хранится в виде хеша, а не открытого текста"""
        plain_password = "mypassword123"
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=get_password_hash(plain_password)
        )
        
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Хеш не должен равняться исходному паролю
        assert user.password_hash != plain_password
        # Хеш должен начинаться с префикса bcrypt
        assert user.password_hash.startswith("$2b$")
        # Хеш должен быть достаточно длинным
        assert len(user.password_hash) >= 60