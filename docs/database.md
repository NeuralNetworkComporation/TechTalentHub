# Схема базы данных TechTalentHub

## Таблицы

```sql
-- Таблица сотрудников
CREATE TABLE users_employee (
    id SERIAL PRIMARY KEY,
    bitrix_id INTEGER UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    position VARCHAR(255),
    hire_date DATE,
    manager_id INTEGER REFERENCES users_employee(id),
    user_id INTEGER REFERENCES auth_user(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица заявок на отпуск
CREATE TABLE vacations_vacationrequest (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES users_employee(id),
    request_type VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    approved_at TIMESTAMP,
    approved_by_id INTEGER REFERENCES users_employee(id),
    current_step INTEGER DEFAULT 1,
    step_history JSONB DEFAULT '[]'
);