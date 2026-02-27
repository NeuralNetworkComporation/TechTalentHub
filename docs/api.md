# API TechTalentHub

## ЭНДПОИНТ 1: Получение статистики

### GET /api/stats/
**Назначение:** Получение общей статистики по сотрудникам и заявкам

**Пример ответа:**
```json
{
  "total_employees": 24,
  "in_onboarding": 5,
  "on_vacation": 3,
  "completed_onboarding": 16
}