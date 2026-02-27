# Архитектура TechTalentHub

## Модели данных (аналог объектов 1С)

### 📦 Модели (аналог справочников)
- `Employee` — сотрудники (аналог Справочник.Сотрудники)
  Поля: id, bitrix_id, name, email, position, hire_date, manager, user

- `OnboardingTask` — задачи онбординга (аналог Справочник.ЗадачиОнбординга)
  Поля: id, title, description, order

### 📄 Модели (аналог документов)
- `VacationRequest` — заявки на отпуск (аналог Документ.ЗаявкаНаОтпуск)
  Поля: id, employee, request_type, start_date, end_date, status, created_at, approved_at

### 📊 Модели (аналог регистров)
- `VacationBalance` — баланс отпусков (аналог РегистрНакопления.ОстаткиОтпусков)
  Поля: id, employee, year, total_days, used_days

- `ApprovalRoute` — маршруты согласования (аналог РегистрСведений.Маршруты)
  Поля: id, type, step_no, role, sla_days

### 📈 Модели (аналог отчётов)
- `ReportDuration` — формируется через views (аналог Отчёт.ДлительностьСогласования)