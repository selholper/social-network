import pytest
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Тесты для эндпоинтов аутентификации"""
    
    def test_login_success(self, client, test_user):
        """Тест успешного входа в систему"""
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/login/access-token", data=login_data)
        
        assert response.status_code == 200
        
        tokens = response.json()
        assert "access_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "bearer"
        assert len(tokens["access_token"]) > 0
    
    def test_login_wrong_username(self, client, test_user):
        """Тест входа с неправильным username"""
        login_data = {
            "username": "wrongusername",
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/login/access-token", data=login_data)
        
        assert response.status_code == 400
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_wrong_password(self, client, test_user):
        """Тест входа с неправильным паролем"""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/login/access-token", data=login_data)
        
        assert response.status_code == 400
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_inactive_user(self, client, db_session):
        """Тест входа неактивного пользователя"""
        from app.models.user import User
        from app.core.security import get_password_hash
        
        # Создаем неактивного пользователя
        inactive_user = User(
            username="inactive",
            email="inactive@example.com",
            password_hash=get_password_hash("password123"),
            is_active=False
        )
        db_session.add(inactive_user)
        db_session.commit()
        
        login_data = {
            "username": "inactive",
            "password": "password123"
        }
        
        response = client.post("/api/v1/login/access-token", data=login_data)
        
        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]
    
    def test_login_missing_username(self, client):
        """Тест входа без username"""
        login_data = {
            "password": "testpassword"
        }
        
        response = client.post("/api/v1/login/access-token", data=login_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_login_missing_password(self, client):
        """Тест входа без пароля"""
        login_data = {
            "username": "testuser"
        }
        
        response = client.post("/api/v1/login/access-token", data=login_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_login_empty_credentials(self, client):
        """Тест входа с пустыми данными"""
        login_data = {
            "username": "",
            "password": ""
        }
        
        response = client.post("/api/v1/login/access-token", data=login_data)
        
        assert response.status_code == 400
    
    def test_test_token_valid(self, client, user_token_headers):
        """Тест проверки валидного токена"""
        response = client.post("/api/v1/login/test-token", headers=user_token_headers)
        
        assert response.status_code == 200
        
        user_data = response.json()
        assert "id" in user_data
        assert "username" in user_data
        assert "email" in user_data
        assert user_data["username"] == "testuser"
    
    def test_test_token_invalid(self, client):
        """Тест проверки невалидного токена"""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.post("/api/v1/login/test-token", headers=invalid_headers)
        
        assert response.status_code == 403
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_test_token_missing(self, client):
        """Тест проверки токена без заголовка авторизации"""
        response = client.post("/api/v1/login/test-token")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_test_token_malformed_header(self, client):
        """Тест проверки токена с неправильным форматом заголовка"""
        malformed_headers = {"Authorization": "InvalidFormat token_here"}
        
        response = client.post("/api/v1/login/test-token", headers=malformed_headers)
        
        assert response.status_code == 401


class TestAuthFlow:
    """Интеграционные тесты потока аутентификации"""
    
    def test_full_auth_flow(self, client, test_user):
        """Тест полного потока аутентификации"""
        # 1. Логинимся
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        
        login_response = client.post("/api/v1/login/access-token", data=login_data)
        assert login_response.status_code == 200
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        
        # 2. Используем токен для доступа к защищенному эндпоинту
        headers = {"Authorization": f"Bearer {access_token}"}
        
        test_response = client.post("/api/v1/login/test-token", headers=headers)
        assert test_response.status_code == 200
        
        user_data = test_response.json()
        assert user_data["username"] == test_user.username
        assert user_data["email"] == test_user.email
    
    def test_token_reuse(self, client, user_token_headers):
        """Тест повторного использования токена"""
        # Используем токен несколько раз
        for _ in range(3):
            response = client.post("/api/v1/login/test-token", headers=user_token_headers)
            assert response.status_code == 200
    
    def test_different_users_different_tokens(self, client, test_user, test_superuser):
        """Тест что разные пользователи получают разные токены"""
        # Логинимся как обычный пользователь
        login_data_user = {
            "username": test_user.username,
            "password": "testpassword"
        }
        response_user = client.post("/api/v1/login/access-token", data=login_data_user)
        token_user = response_user.json()["access_token"]
        
        # Логинимся как суперпользователь
        login_data_admin = {
            "username": test_superuser.username,
            "password": "adminpassword"
        }
        response_admin = client.post("/api/v1/login/access-token", data=login_data_admin)
        token_admin = response_admin.json()["access_token"]
        
        # Токены должны быть разными
        assert token_user != token_admin
        
        # Проверяем что каждый токен работает для своего пользователя
        headers_user = {"Authorization": f"Bearer {token_user}"}
        headers_admin = {"Authorization": f"Bearer {token_admin}"}
        
        response_user_test = client.post("/api/v1/login/test-token", headers=headers_user)
        response_admin_test = client.post("/api/v1/login/test-token", headers=headers_admin)
        
        assert response_user_test.status_code == 200
        assert response_admin_test.status_code == 200
        
        user_data = response_user_test.json()
        admin_data = response_admin_test.json()
        
        assert user_data["username"] == test_user.username
        assert admin_data["username"] == test_superuser.username
