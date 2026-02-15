from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Employee
from core.services.bitrix import get_bitrix_api
import logging
from datetime import datetime
import secrets
import string

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Синхронизация пользователей из Битрикс24 (или тестовых данных)'

    def add_arguments(self, parser):
        parser.add_argument('--webhook', type=str, help='Bitrix24 webhook URL (опционально)')
        parser.add_argument('--real', action='store_true', help='Использовать реальный API (если не указан, то заглушка)')

    def handle(self, *args, **options):
        self.stdout.write('Начинаем синхронизацию пользователей...')

        try:
            # Используем реальный API только если указан флаг --real
            use_real = options.get('real', False)
            bitrix = get_bitrix_api(
                webhook_url=options.get('webhook'),
                force_mock=not use_real  # Если не real, то принудительно мок
            )

            users = bitrix.get_users()

            if not users:
                self.stdout.write(self.style.WARNING('Нет пользователей для синхронизации'))
                return

            created = 0
            updated = 0

            for bitrix_user in users:
                # Пропускаем неактивных
                if bitrix_user.get('ACTIVE') is False:
                    continue

                # Получаем данные
                bitrix_id = str(bitrix_user['ID'])
                name = f"{bitrix_user.get('NAME', '')} {bitrix_user.get('LAST_NAME', '')}".strip()
                email = bitrix_user.get('EMAIL', '')
                position = bitrix_user.get('WORK_POSITION', '')

                # Пытаемся извлечь дату приема
                hire_date = None
                if 'DATE_CREATE' in bitrix_user:
                    try:
                        hire_date = datetime.strptime(bitrix_user['DATE_CREATE'], '%Y-%m-%d').date()
                    except:
                        pass

                if not name:
                    name = bitrix_user.get('LOGIN', f'User_{bitrix_id}')

                # Создаем или обновляем сотрудника
                employee, created_flag = Employee.objects.update_or_create(
                    bitrix_id=bitrix_id,
                    defaults={
                        'name': name,
                        'email': email,
                        'position': position,
                        'hire_date': hire_date,
                        'is_active': True,
                    }
                )

                if created_flag:
                    created += 1
                    self.stdout.write(f'   ➕ Добавлен сотрудник: {name}')

                    # Создаем пользователя Django для входа в админку
                    username = f"bitrix_{bitrix_id}"
                    user, user_created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': email,
                            'first_name': bitrix_user.get('NAME', ''),
                            'last_name': bitrix_user.get('LAST_NAME', ''),
                        }
                    )
                    if user_created:
                        # Генерируем простой пароль для теста
                        alphabet = string.ascii_letters + string.digits
                        random_password = ''.join(secrets.choice(alphabet) for _ in range(10))
                        user.set_password(random_password)
                        user.save()
                        self.stdout.write(f'      👤 Создан пользователь: {username} / {random_password}')

                    employee.user = user
                    employee.save()
                else:
                    updated += 1

            self.stdout.write(self.style.SUCCESS(
                f'✅ Синхронизация завершена: создано {created}, обновлено {updated}'
            ))

            # Показываем список сотрудников
            self.stdout.write('\nСписок сотрудников в базе:')
            for emp in Employee.objects.all():
                self.stdout.write(f'  - {emp.name} ({emp.position})')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка синхронизации: {e}'))
            logger.exception("Sync error")