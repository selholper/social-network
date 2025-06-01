#!/usr/bin/env python3
"""
Скрипт для создания тестовых пользователей
"""

import sys
import os

# Добавляем корневую директорию проекта в Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bcrypt import gensalt, hashpw 
from app.db.postgresql.session import SessionLocal
from app.models.user import User
from app.core.security import verify_password, get_password_hash

def create_users():
    """Создает тестовых пользователей"""
    db = SessionLocal()
    
    try:
        # Проверяем, есть ли уже пользователи
        existing_users = db.query(User).count()
        print(f"Найдено пользователей в базе: {existing_users}")
        
        # Создаем администратора
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                password_hash=get_password_hash("password"),
                full_name="Admin User",
                is_superuser=True,
                is_active=True
            )
            db.add(admin)
            print("✅ Создан пользователь: admin")
        else:
            print("ℹ️  Пользователь admin уже существует")
        
        # Создаем обычного пользователя
        user = db.query(User).filter(User.username == "user").first()
        if not user:
            user = User(
                username="user",
                email="user@example.com",
                password_hash=get_password_hash("password"),
                full_name="Regular User",
                is_superuser=False,
                is_active=True
            )
            db.add(user)
            print("✅ Создан пользователь: user")
        else:
            print("ℹ️  Пользователь user уже существует")
        
        # Создаем дополнительного тестового пользователя
        testuser = db.query(User).filter(User.username == "testuser").first()
        if not testuser:
            testuser = User(
                username="testuser",
                email="testuser@example.com",
                password_hash=get_password_hash("testpass123"),
                full_name="Test User",
                is_superuser=False,
                is_active=True
            )
            db.add(testuser)
            print("✅ Создан пользователь: testuser")
        else:
            print("ℹ️  Пользователь testuser уже существует")
        
        db.commit()
        
        # Проверяем созданных пользователей
        all_users = db.query(User).all()
        print(f"\n📊 Всего пользователей в базе: {len(all_users)}")
        print("\n👥 Список пользователей:")
        for u in all_users:
            role = "Админ" if u.is_superuser else "Пользователь"
            status = "Активен" if u.is_active else "Неактивен"
            print(f"  - {u.username} ({u.email}) - {role}, {status}")
        
        print("\n🔑 Данные для входа:")
        print("Администратор:")
        print("  Username: admin")
        print("  Password: password")
        print("\nОбычный пользователь:")
        print("  Username: user") 
        print("  Password: password")
        print("\nТестовый пользователь:")
        print("  Username: testuser")
        print("  Password: testpass123")
        
    except Exception as e:
        print(f"❌ Ошибка при создании пользователей: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def test_password_hashing():
    """Тестирует хеширование паролей"""
    print("\n🔐 Тестирование хеширования паролей...")

    password = "password"
    hashed = get_password_hash(password)
    print(f"Пароль: {password}")
    print(f"Хеш: {hashed}")
    
    is_valid = verify_password(password, hashed)
    print(f"Проверка пароля: {'✅ Успешно' if is_valid else '❌ Ошибка'}")

if __name__ == "__main__":
    print("🚀 Создание тестовых пользователей...")
    
    # Тестируем хеширование паролей
    test_password_hashing()
    
    # Создаем пользователей
    create_users()
    
    print("\n✅ Готово! Теперь вы можете войти в систему.")
    print("\n🌐 Откройте http://localhost:8000/docs для тестирования API")