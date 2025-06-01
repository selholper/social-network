import pytest
from fastapi.testclient import TestClient


class TestUserEndpoints:
    """Тесты для пользовательских эндпоинтов"""
    
    def test_get_current_user(self, client, user_token_headers, test_user):
        """Тест получения информации о текущем пользователе"""
        response = client.get("/api/v1/users/me", headers=user_token_headers)
        
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["id"] == test_user.id
        assert user_data["username"] == test_user.username
        assert user_data["email"] == test_user.email
        assert user_data["full_name"] == test_user.full_name
        assert user_data["is_active"] == test_user.is_active
    
    def test_get_current_user_unauthorized(self, client):
        """Тест получения информации о пользователе без авторизации"""
        response = client.get("/api/v1/users/me")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_create_user_success(self, client):
        """Тест успешного создания пользователя"""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User"
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        
        assert response.status_code == 200
        
        created_user = response.json()
        assert created_user["username"] == "newuser"
        assert created_user["email"] == "newuser@example.com"
        assert created_user["full_name"] == "New User"
        assert created_user["is_active"] is True
        assert "password" not in created_user  # Пароль не должен возвращаться
    
    def test_create_user_duplicate_username(self, client, test_user):
        """Тест создания пользователя с существующим username"""
        user_data = {
            "username": test_user.username,  # Дублирующийся username
            "email": "different@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        
        assert response.status_code == 400
        assert "username already exists" in response.json()["detail"]
    
    def test_create_user_duplicate_email(self, client, test_user):
        """Тест создания пользователя с существующим email"""
        user_data = {
            "username": "differentuser",
            "email": test_user.email,  # Дублирующийся email
            "password": "password123"
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        
        assert response.status_code == 400
        assert "email already exists" in response.json()["detail"]
    
    def test_create_user_invalid_data(self, client):
        """Тест создания пользователя с невалидными данными"""
        user_data = {
            "username": "test@user",  # Невалидный username
            "email": "invalid-email",  # Невалидный email
            "password": "123"  # Слишком короткий пароль (если есть валидация)
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_update_current_user(self, client, user_token_headers, test_user):
        """Тест обновления информации о текущем пользователе"""
        update_data = {
            "full_name": "Updated Full Name",
            "bio": "Updated bio"
        }
        
        response = client.put("/api/v1/users/me", headers=user_token_headers, json=update_data)
        
        assert response.status_code == 200
        
        updated_user = response.json()
        assert updated_user["full_name"] == "Updated Full Name"
        assert updated_user["bio"] == "Updated bio"
        assert updated_user["username"] == test_user.username  # Не изменился
        assert updated_user["email"] == test_user.email  # Не изменился
    
    def test_update_current_user_username(self, client, user_token_headers):
        """Тест обновления username текущего пользователя"""
        update_data = {
            "username": "newusername"
        }
        
        response = client.put("/api/v1/users/me", headers=user_token_headers, json=update_data)
        
        assert response.status_code == 200
        
        updated_user = response.json()
        assert updated_user["username"] == "newusername"
    
    def test_update_current_user_duplicate_username(self, client, user_token_headers, test_superuser):
        """Тест обновления username на уже существующий"""
        update_data = {
            "username": test_superuser.username  # Уже существующий username
        }
        
        response = client.put("/api/v1/users/me", headers=user_token_headers, json=update_data)
        
        assert response.status_code == 400
        assert "username already exists" in response.json()["detail"]
    
    def test_update_current_user_password(self, client, user_token_headers, test_user):
        """Тест обновления пароля текущего пользователя"""
        update_data = {
            "password": "newpassword123"
        }
        
        response = client.put("/api/v1/users/me", headers=user_token_headers, json=update_data)
        
        assert response.status_code == 200
        
        # Проверяем что можем войти с новым паролем
        login_data = {
            "username": test_user.username,
            "password": "newpassword123"
        }
        
        login_response = client.post("/api/v1/login/access-token", data=login_data)
        assert login_response.status_code == 200
    
    def test_get_users_list_as_superuser(self, client, superuser_token_headers):
        """Тест получения списка пользователей суперпользователем"""
        response = client.get("/api/v1/users/", headers=superuser_token_headers)
        
        assert response.status_code == 200
        
        users = response.json()
        assert isinstance(users, list)
        assert len(users) == 1
    
    def test_get_users_list_as_regular_user(self, client, user_token_headers):
        """Тест получения списка пользователей обычным пользователем"""
        response = client.get("/api/v1/users/", headers=user_token_headers)
        
        assert response.status_code == 400
        assert "doesn't have enough privileges" in response.json()["detail"]
    
    def test_get_user_by_id_as_superuser(self, client, superuser_token_headers, test_user):
        """Тест получения пользователя по ID суперпользователем"""
        response = client.get(f"/api/v1/users/{test_user.id}", headers=superuser_token_headers)
        
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["id"] == test_user.id
        assert user_data["username"] == test_user.username
    
    def test_get_user_by_id_self(self, client, user_token_headers, test_user):
        """Тест получения собственной информации по ID"""
        response = client.get(f"/api/v1/users/{test_user.id}", headers=user_token_headers)
        
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["id"] == test_user.id
    
    def test_get_user_by_id_other_as_regular_user(self, client, user_token_headers, test_superuser):
        """Тест получения другого пользователя по ID обычным пользователем"""
        response = client.get(f"/api/v1/users/{test_superuser.id}", headers=user_token_headers)
        
        assert response.status_code == 400
        assert "doesn't have enough privileges" in response.json()["detail"]
    
    def test_update_user_by_id_as_superuser(self, client, superuser_token_headers, test_user):
        """Тест обновления пользователя по ID суперпользователем"""
        update_data = {
            "full_name": "Updated by Admin",
            "is_active": False
        }
        
        response = client.put(
            f"/api/v1/users/{test_user.id}", 
            headers=superuser_token_headers, 
            json=update_data
        )
        
        assert response.status_code == 200
        
        updated_user = response.json()
        assert updated_user["full_name"] == "Updated by Admin"
        assert updated_user["is_active"] is False
    
    def test_update_user_by_id_as_regular_user(self, client, user_token_headers, test_superuser):
        """Тест обновления другого пользователя обычным пользователем"""
        update_data = {
            "full_name": "Hacked Name"
        }
        
        response = client.put(
            f"/api/v1/users/{test_superuser.id}", 
            headers=user_token_headers, 
            json=update_data
        )
        
        assert response.status_code == 400
        assert "doesn't have enough privileges" in response.json()["detail"]


class TestUserValidation:
    """Тесты валидации пользовательских данных"""
    
    def test_create_user_missing_required_fields(self, client):
        """Тест создания пользователя без обязательных полей"""
        incomplete_data = {
            "username": "testuser"
            # Отсутствуют email и password
        }
        
        response = client.post("/api/v1/users/", json=incomplete_data)
        
        assert response.status_code == 422
        
        errors = response.json()["detail"]
        error_fields = [error["loc"][-1] for error in errors]
        assert "email" in error_fields
        assert "password" in error_fields
    
    def test_create_user_invalid_email_format(self, client):
        """Тест создания пользователя с невалидным форматом email"""
        user_data = {
            "username": "testuser",
            "email": "not-an-email",
            "password": "password123"
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        
        assert response.status_code == 422
        
        errors = response.json()["detail"]
        email_error = next(error for error in errors if error["loc"][-1] == "email")
        assert "email" in email_error["msg"].lower()
    
    def test_update_user_partial_data(self, client, user_token_headers):
        """Тест частичного обновления пользователя"""
        # Обновляем только одно поле
        update_data = {
            "bio": "Just updated bio"
        }
        
        response = client.put("/api/v1/users/me", headers=user_token_headers, json=update_data)
        
        assert response.status_code == 200
        
        updated_user = response.json()
        assert updated_user["bio"] == "Just updated bio"
        # Другие поля должны остаться без изменений
        assert updated_user["username"] == "testuser"