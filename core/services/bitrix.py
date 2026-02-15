import requests
import logging
import random
from django.conf import settings
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================
# ЗАГЛУШКА (МОК) для разработки без Битрикса
# ============================================

class MockBitrix24API:
    """🔧 Заглушка Bitrix API для разработки (не требует реального портала)"""
    
    def __init__(self, webhook_url=None):
        print("🔧 РЕЖИМ РАЗРАБОТКИ: Используется ЗАГЛУШКА Bitrix API")
        print("   Реальные запросы к Битриксу НЕ отправляются")
        self.users_db = self._create_test_users()
    
    def _create_test_users(self):
        """Создаем тестовых пользователей"""
        return [
            {
                'ID': '1',
                'NAME': 'Иван',
                'LAST_NAME': 'Петров',
                'EMAIL': 'ivan.petrov@company.ru',
                'WORK_POSITION': 'Team Lead',
                'ACTIVE': True,
                'PERSONAL_BIRTHDAY': '1985-03-15',
                'UF_DEPARTMENT': [1],
                'WORK_PHONE': '+7 (123) 456-78-90',
            },
            {
                'ID': '2',
                'NAME': 'Мария',
                'LAST_NAME': 'Сидорова',
                'EMAIL': 'maria.sidorova@company.ru',
                'WORK_POSITION': 'HR-менеджер',
                'ACTIVE': True,
                'PERSONAL_BIRTHDAY': '1990-07-22',
                'UF_DEPARTMENT': [2],
                'WORK_PHONE': '+7 (123) 456-78-91',
            },
            {
                'ID': '3',
                'NAME': 'Алексей',
                'LAST_NAME': 'Иванов',
                'EMAIL': 'alexey.ivanov@company.ru',
                'WORK_POSITION': 'Junior Developer',
                'ACTIVE': True,
                'PERSONAL_BIRTHDAY': '1995-11-05',
                'UF_DEPARTMENT': [1],
                'WORK_PHONE': '+7 (123) 456-78-92',
                'DATE_CREATE': '2024-02-01',  # Недавно принят
            },
            {
                'ID': '4',
                'NAME': 'Елена',
                'LAST_NAME': 'Козлова',
                'EMAIL': 'elena.kozlova@company.ru',
                'WORK_POSITION': 'QA Engineer',
                'ACTIVE': True,
                'PERSONAL_BIRTHDAY': '1992-09-18',
                'UF_DEPARTMENT': [3],
                'WORK_PHONE': '+7 (123) 456-78-93',
                'DATE_CREATE': '2024-02-15',  # Новенькая
            },
            {
                'ID': '5',
                'NAME': 'Дмитрий',
                'LAST_NAME': 'Соколов',
                'EMAIL': 'dmitry.sokolov@company.ru',
                'WORK_POSITION': 'Frontend Developer',
                'ACTIVE': True,
                'PERSONAL_BIRTHDAY': '1988-04-30',
                'UF_DEPARTMENT': [1],
                'WORK_PHONE': '+7 (123) 456-78-94',
                'DATE_CREATE': '2024-01-10',  # Принят месяц назад
            },
        ]
    
    def get_users(self, filter_params=None) -> List[Dict]:
        """Вернуть тестовых пользователей"""
        users = self.users_db.copy()
        
        # Применяем фильтры (если есть)
        if filter_params:
            filtered = []
            for user in users:
                match = True
                for key, value in filter_params.items():
                    if key == 'ID' and str(user['ID']) != str(value):
                        match = False
                        break
                    elif key == '>DATE_CREATE':
                        # Простая имитация фильтра по дате
                        pass
                if match:
                    filtered.append(user)
            users = filtered
        
        return users
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить одного пользователя"""
        for user in self.users_db:
            if str(user['ID']) == str(user_id):
                return user
        return None
    
    def create_calendar_event(self, user_id: int, event_data: Dict) -> Optional[Dict]:
        """Создать событие в календаре (заглушка)"""
        event_id = random.randint(10000, 99999)
        print(f"📅 [MOCK] Создано событие в календаре для пользователя {user_id}")
        print(f"   Событие: {event_data.get('name')}")
        print(f"   Даты: {event_data.get('from')} - {event_data.get('to')}")
        print(f"   ID события: {event_id}")
        return {'id': event_id}
    
    def send_notification(self, user_id: int, message: str) -> bool:
        """Отправить уведомление (заглушка)"""
        user = self.get_user(user_id)
        user_name = user['NAME'] if user else f"ID {user_id}"
        print(f"🔔 [MOCK] Уведомление для {user_name}: {message}")
        return True


# ============================================
# РЕАЛЬНЫЙ КЛАСС для работы с API Битрикс24
# ============================================

class RealBitrix24API:
    """Реальный класс для работы с API Битрикс24"""
    
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url or settings.BITRIX24_WEBHOOK
        if not self.webhook_url:
            raise ValueError("BITRIX24_WEBHOOK не настроен в .env файле")
        print("🌐 РЕЖИМ РАБОТЫ с реальным Битрикс24")
    
    def _request(self, method: str, params: Dict = None) -> Dict:
        """Базовый метод для запросов к API"""
        url = f"{self.webhook_url}{method}"
        
        try:
            response = requests.post(url, json=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Bitrix API error: {data['error']} - {data.get('error_description', '')}")
                return {'error': data['error'], 'error_description': data.get('error_description', '')}
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return {'error': 'connection_error', 'error_description': str(e)}
    
    def get_users(self, filter_params: Dict = None) -> List[Dict]:
        """Получить список пользователей"""
        params = {}
        if filter_params:
            params['filter'] = filter_params
            
        result = self._request('user.get', params)
        return result.get('result', []) if 'result' in result else []
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Получить одного пользователя"""
        result = self._request('user.get', {'filter': {'ID': user_id}})
        users = result.get('result', [])
        return users[0] if users else None
    
    def create_calendar_event(self, user_id: int, event_data: Dict) -> Optional[Dict]:
        """Создать событие в календаре"""
        params = {
            'type': 'user',
            'ownerId': user_id,
            'name': event_data.get('name'),
            'description': event_data.get('description', ''),
            'from': event_data.get('from'),
            'to': event_data.get('to'),
            'section': event_data.get('section', 'Отпуска'),
        }
        
        result = self._request('calendar.event.add', params)
        return result.get('result') if 'result' in result else None
    
    def send_notification(self, user_id: int, message: str) -> bool:
        """Отправить уведомление пользователю"""
        params = {
            'to': user_id,
            'message': message,
            'type': 'SYSTEM',
        }
        
        result = self._request('im.notify', params)
        return result.get('result', False)


# ============================================
# ФАБРИКА для выбора режима (МОК или РЕАЛЬНЫЙ)
# ============================================

# Глобальный переключатель: 
#   True = заглушка (не требует Битрикса)
#   False = реальный API (требует вебхук в .env)
USE_MOCK_FOR_DEVELOPMENT = True  

def get_bitrix_api(webhook_url=None, force_mock=None):
    """
    Фабрика для создания API.
    
    Параметры:
        webhook_url: опциональный URL вебхука
        force_mock: если True, принудительно использовать заглушку
    
    Возвращает:
        Объект API (реальный или заглушку)
    """
    if force_mock is True:
        return MockBitrix24API(webhook_url)
    
    if force_mock is False:
        return RealBitrix24API(webhook_url)
    
    # Автоматический выбор на основе глобальной настройки
    if USE_MOCK_FOR_DEVELOPMENT:
        return MockBitrix24API(webhook_url)
    else:
        return RealBitrix24API(webhook_url)


# Для обратной совместимости (если старый код использует Bitrix24API)
Bitrix24API = get_bitrix_api