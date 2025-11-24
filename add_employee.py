# add_employee.py
from main import Employee, SessionLocal, get_password_hash

def add_employee(
    login: str,
    password: str,
    initials: str,
    name: str,
    position: str,
    rate: str,
    experience: str,
    status: str,
    salary: str,
    hours: str,
    hours_detail: str,
    penalties: list,
    absences: list,
    error_text: str = ""
):
    db = SessionLocal()
    try:
        # проверим, нет ли уже такого логина
        existing = db.query(Employee).filter(Employee.login == login.lower()).first()
        if existing:
            print(f"⚠ Сотрудник с логином {login} уже существует")
            return

        emp = Employee(
            login=login.lower(),
            password_hash=get_password_hash(password),
            initials=initials,
            name=name,
            position=position,
            rate=rate,
            experience=experience,
            status=status,
            salary=salary,
            hours=hours,
            hours_detail=hours_detail,
            penalties_json="[" + ",".join([f'"{p}"' for p in penalties]) + "]",
            absences_json="[" + ",".join([f'"{a}"' for a in absences]) + "]",
            error_text=error_text,
        )
        db.add(emp)
        db.commit()
        print(f"✅ Добавлен сотрудник {login}")
    finally:
        db.close()


if __name__ == "__main__":
    # 👉 ТУТ МЕНЯЕШЬ ДАННЫЕ ПОД НУЖНОГО СОТРУДНИКА
    add_employee(
        login="petrov",
        password="5678",
        initials="ПП",
        name="Петров Пётр Петрович",
        position="Экспедитор · Колонна № 1",
        rate="1 700 ₽/смена",
        experience="1 год 2 мес.",
        status="Активен · Основное место",
        salary="68 900 ₽",
        hours="140 ч",
        hours_detail="Переработка: 10 ч · Ночные: 6 ч.",
        penalties=[
            "Штрафов: нет",
            "Прогулы: нет",
        ],
        absences=[
            "Больничные: 1 день",
            "Отпуск: 0/28 дней",
            "Отсутствия: нет",
        ],
    )
