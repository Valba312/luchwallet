from datetime import datetime, timedelta
import io
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
import json
import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    text,
)
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from passlib.context import CryptContext


# ===============================
#   НАСТРОЙКА БАЗЫ ДАННЫХ
# ===============================

DATABASE_URL = "sqlite:///./luchwallet.db"

PHOTOS_DIR = "photos"
os.makedirs(PHOTOS_DIR, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===============================
#            МОДЕЛИ БД
# ===============================


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    # открытый пароль только для админ-панели по ТЗ
    password_plain = Column(String(255), nullable=True)

    initials = Column(String(8), nullable=False)
    name = Column(String(255), nullable=False)
    position = Column(String(255), nullable=False)

    # Оклад
    rate = Column(String(50), nullable=True)
    experience = Column(String(50), nullable=True)
    status = Column(String(100), nullable=True)

    # Отображаемые поля
    salary = Column(String(50), nullable=True)   # отображаемый баланс
    hours = Column(String(50), nullable=True)    # отображаемые часы за месяц
    hours_detail = Column(String(255), nullable=True)

    penalties_json = Column(Text, nullable=True)
    absences_json = Column(Text, nullable=True)

    error_text = Column(String(255), nullable=True)

    photo_url = Column(String(512), nullable=True)

    # === динамический баланс ===
    balance_int = Column(Integer, nullable=True)               # фактический баланс в рублях
    contract_hours_per_month = Column(Integer, nullable=True)  # нормочасы в месяц
    hourly_rate = Column(Integer, nullable=True)               # ₽/час
    schedule_type = Column(String(50), nullable=True)          # office / None / ...
    work_start_hour = Column(Integer, nullable=True)           # 0–23
    work_end_hour = Column(Integer, nullable=True)             # 0–23 (не включая)
    last_balance_update = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Payment(Base):
    """
    История начислений/удержаний сотрудника.
    amount в рублях:
      >0 — начисление
      <0 — удержание
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, index=True, nullable=False)
    type = Column(String(50), nullable=False)  # salary / bonus / overtime / night / fine / other
    amount = Column(Integer, nullable=False)
    comment = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class EmployeeMonthStat(Base):
    """
    Помесячная статистика дохода/часов/штрафов.
    Хранится отдельно от основной карточки сотрудника.
    """
    __tablename__ = "employee_month_stats"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, index=True, nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)  # 1-12
    month_key = Column(String(8), nullable=False)  # jan, feb, ...

    income = Column(Integer, nullable=False, default=0)  # общий доход за месяц
    salary = Column(Integer, nullable=True)              # начисленная зарплата
    hours = Column(Integer, nullable=True)               # отработанные часы

    penalties_json = Column(Text, nullable=True)         # JSON-список строк
    absences_json = Column(Text, nullable=True)          # JSON-список строк

    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ===============================
#         Pydantic-схемы
# ===============================

class LoginRequest(BaseModel):
    role: str   # "employee" или "admin"
    login: str
    password: str


class LoginResponse(BaseModel):
    role: str
    login: str
    data: dict


class EmployeeBase(BaseModel):
    initials: str
    name: str
    position: str
    rate: Optional[str] = None
    experience: Optional[str] = None
    status: Optional[str] = None
    salary: Optional[str] = None
    hours: Optional[str] = None
    hours_detail: Optional[str] = None
    penalties: List[str] = []
    absences: List[str] = []
    error_text: Optional[str] = ""
    photo_url: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    login: str
    password: str


class EmployeeUpdate(BaseModel):
    initials: Optional[str] = None
    name: Optional[str] = None
    position: Optional[str] = None
    rate: Optional[str] = None
    experience: Optional[str] = None
    status: Optional[str] = None
    salary: Optional[str] = None
    hours: Optional[str] = None
    hours_detail: Optional[str] = None
    penalties: Optional[List[str]] = None
    absences: Optional[List[str]] = None
    error_text: Optional[str] = None
    photo_url: Optional[str] = None
    # смена логина/пароля
    login: Optional[str] = None
    password: Optional[str] = None


class EmployeeShort(BaseModel):
    id: int
    login: str
    name: str
    position: str
    is_active: bool
    photo_url: Optional[str] = None

    password: Optional[str] = Field(None, alias="password_plain")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class EmployeeDetail(EmployeeBase):
    id: int
    login: str
    is_active: bool
    password: Optional[str] = Field(None, alias="password_plain")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class PaymentBaseSchema(BaseModel):
    type: str
    amount: int
    comment: Optional[str] = None


class PaymentCreate(PaymentBaseSchema):
    pass


class PaymentOut(PaymentBaseSchema):
    id: int
    employee_id: int
    created_at: datetime

    class Config:
        orm_mode = True


# ===============================
#        ВСПОМОГАТЕЛЬНОЕ
# ===============================

def json_dumps_list(values: List[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def json_loads_list(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def money_to_int(value: Optional[str]) -> int:
    """'92 430 ₽' -> 92430"""
    if not value:
        return 0
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    return int(digits) if digits else 0


def int_to_money(value: int) -> str:
    """92430 -> '92 430 ₽'"""
    s = f"{value:,}".replace(",", " ")
    return f"{s} ₽"


def is_office_work_time(dt: datetime, start_hour: int, end_hour: int) -> bool:
    """
    Простейшая модель: офисники работают Пн–Пт с start_hour до end_hour (без учёта обеда).
    """
    if dt.weekday() >= 5:  # 5,6 = сб, вс
        return False
    h = dt.hour
    if start_hour <= end_hour:
        return start_hour <= h < end_hour
    # если смена «через ночь»
    return h >= start_hour or h < end_hour


def accrue_balance_for_employee(emp: Employee, now: Optional[datetime] = None):
    """
    Обновляет баланс сотрудника в БД по почасовой ставке.
    Для простоты:
      - автоматом считаем только для schedule_type == 'office'
      - берём каждый полный час между last_balance_update и now,
        если час попадает в рабочее время – начисляем hourly_rate.
    """
    if emp.schedule_type != "office":
        return
    if not emp.hourly_rate:
        return

    if now is None:
        now = datetime.utcnow()

    # инициализация
    if not emp.last_balance_update:
        emp.last_balance_update = now
        if emp.balance_int is None:
            emp.balance_int = money_to_int(emp.salary or "0")
        return

    cursor = emp.last_balance_update.replace(minute=0, second=0, microsecond=0)
    if cursor >= now:
        return

    hours_to_pay = 0
    while cursor + timedelta(hours=1) <= now:
        if is_office_work_time(cursor, emp.work_start_hour or 8, emp.work_end_hour or 19):
            hours_to_pay += 1
        cursor += timedelta(hours=1)

    if hours_to_pay > 0:
        current_balance = emp.balance_int or money_to_int(emp.salary or "0")
        current_balance += hours_to_pay * emp.hourly_rate
        emp.balance_int = current_balance
        emp.salary = int_to_money(current_balance)

    emp.last_balance_update = cursor


MONTH_META = {
    1: {"key": "jan", "short": "Янв", "full": "Январь"},
    2: {"key": "feb", "short": "Фев", "full": "Февраль"},
    3: {"key": "mar", "short": "Мар", "full": "Март"},
    4: {"key": "apr", "short": "Апр", "full": "Апрель"},
    5: {"key": "may", "short": "Май", "full": "Май"},
    6: {"key": "jun", "short": "Июн", "full": "Июнь"},
    7: {"key": "jul", "short": "Июл", "full": "Июль"},
    8: {"key": "aug", "short": "Авг", "full": "Август"},
    9: {"key": "sep", "short": "Сен", "full": "Сентябрь"},
    10: {"key": "oct", "short": "Окт", "full": "Октябрь"},
    11: {"key": "nov", "short": "Ноя", "full": "Ноябрь"},
    12: {"key": "dec", "short": "Дек", "full": "Декабрь"},
}


def build_months_for_employee(db: Session, emp_id: int) -> List[dict]:
    """Отдаём месяцы в удобном для фронта формате."""
    stats = (
        db.query(EmployeeMonthStat)
        .filter(EmployeeMonthStat.employee_id == emp_id)
        .order_by(EmployeeMonthStat.year.asc(), EmployeeMonthStat.month.asc())
        .all()
    )
    result: List[dict] = []
    for s in stats:
        meta = MONTH_META.get(s.month, None)
        if meta:
            key = s.month_key or meta["key"]
            short = meta["short"]
            full = meta["full"]
        else:
            key = s.month_key or str(s.month)
            short = key
            full = key
        result.append(
            {
                "key": key,
                "short": short,
                "fullName": full,
                "year": s.year,
                "month": s.month,  # <-- ЭТО ВАЖНО: номер месяца для фронта
                "income": s.income,
                "salary": s.salary,
                "hours": s.hours,
                "penalties": json_loads_list(s.penalties_json),
                "absences": json_loads_list(s.absences_json),
            }
        )
    return result



def seed_month_stats_for_employee(
    db: Session,
    emp: Employee,
    months_data: List[dict],
):
    """Создаём помесячную статистику, если её ещё нет."""
    if not emp:
        return
    exists = (
        db.query(EmployeeMonthStat)
        .filter(EmployeeMonthStat.employee_id == emp.id)
        .count()
    )
    if exists:
        return

    for m in months_data:
        stat = EmployeeMonthStat(
            employee_id=emp.id,
            year=m["year"],
            month=m["month"],
            month_key=m["key"],
            income=m["income"],
            salary=m.get("salary"),
            hours=m.get("hours"),
            penalties_json=json_dumps_list(m.get("penalties", [])),
            absences_json=json_dumps_list(m.get("absences", [])),
        )
        db.add(stat)


# ===============================
#        ИНИЦИАЛИЗАЦИЯ БД
# ===============================

def init_db():
    """Создаём таблицы и демо-данные."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # добавляем колонку password_plain, если её нет
        try:
            db.execute(text("ALTER TABLE employees ADD COLUMN password_plain VARCHAR(255);"))
            db.commit()
        except Exception:
            db.rollback()

        # --- добавляем новые колонки, если их ещё нет ---
        for ddl in [
            "ALTER TABLE employees ADD COLUMN balance_int INTEGER;",
            "ALTER TABLE employees ADD COLUMN contract_hours_per_month INTEGER;",
            "ALTER TABLE employees ADD COLUMN hourly_rate INTEGER;",
            "ALTER TABLE employees ADD COLUMN schedule_type VARCHAR(50);",
            "ALTER TABLE employees ADD COLUMN work_start_hour INTEGER;",
            "ALTER TABLE employees ADD COLUMN work_end_hour INTEGER;",
            "ALTER TABLE employees ADD COLUMN last_balance_update DATETIME;",
        ]:
            try:
                db.execute(text(ddl))
                db.commit()
            except Exception:
                db.rollback()

        # демо-сотрудник ivan
        if not db.query(Employee).filter_by(login="ivan").first():
            emp = Employee(
                login="ivan",
                password_hash=get_password_hash("1234"),
                password_plain="1234",
                initials="ИИ",
                name="Иванов Иван Иванович",
                position="Водитель грузового автомобиля · Колонна № 3",
                rate="1 850 ₽/смена",
                experience="4 года 7 мес.",
                status="Активен · Основное место",
                salary="92 430 ₽",
                hours="152 ч",
                hours_detail="Переработка: 18 ч · Ночные: 12 ч.",
                penalties_json=json_dumps_list(
                    [
                        "Штрафов: 1 — превышение времени стоянки",
                        "Прогулы: нет",
                        "Замечания: отсутствуют",
                    ]
                ),
                absences_json=json_dumps_list(
                    [
                        "Больничные: 3 дня (ОРВИ)",
                        "Отпуск: 14/28 дней",
                        "Отсутствия: 1 день за свой счёт",
                    ]
                ),
                error_text="",
                photo_url=None,
                balance_int=92430,
                contract_hours_per_month=152,
                hourly_rate=608,          # 92 430 / 152 ≈ 608 ₽/ч
                schedule_type=None,       # водителю пока не начисляем автоматически
                work_start_hour=None,
                work_end_hour=None,
                last_balance_update=datetime.utcnow(),
            )
            db.add(emp)

        # демо-сотрудник anna
        if not db.query(Employee).filter_by(login="anna").first():
            emp = Employee(
                login="anna",
                password_hash=get_password_hash("qwerty"),
                password_plain="qwerty",
                initials="АП",
                name="Антонова Анна Петровна",
                position="Диспетчер смен · Офис № 2",
                rate="2 050 ₽/смена",
                experience="2 года 3 мес.",
                status="Активна · Совместительство",
                salary="74 300 ₽",
                hours="128 ч",
                hours_detail="Переработка: 6 ч · Ночные: 4 ч.",
                penalties_json=json_dumps_list(
                    [
                        "Штрафов: нет",
                        "Прогулы: нет",
                        "Замечания: 1 — опоздание на планёрку",
                    ]
                ),
                absences_json=json_dumps_list(
                    [
                        "Больничные: не было",
                        "Отпуск: 7/28 дней",
                        "Отсутствия: нет",
                    ]
                ),
                error_text="",
                photo_url=None,
                balance_int=74300,
                contract_hours_per_month=128,
                hourly_rate=580,          # 74 300 / 128 ≈ 580 ₽/ч
                schedule_type="office",   # будни 8–19
                work_start_hour=8,
                work_end_hour=19,
                last_balance_update=datetime.utcnow(),
            )
            db.add(emp)

        # демо-админ
        if not db.query(Admin).filter_by(login="admin").first():
            admin = Admin(
                login="admin",
                password_hash=get_password_hash("admin123"),
                name="Администратор системы",
            )
            db.add(admin)

        # на всякий случай — чтобы были id у только что добавленных сотрудников
        db.flush()

        # помесячные данные по ivan
        ivan = db.query(Employee).filter_by(login="ivan").first()
        if ivan:
            seed_month_stats_for_employee(
                db,
                ivan,
                [
                    {
                        "year": 2024,
                        "month": 6,
                        "key": "jun",
                        "income": 87762,
                        "salary": 87762,
                        "hours": 140,
                        "penalties": ["Штрафов: нет", "Прогулы: нет"],
                        "absences": ["Больничные: 1 день", "Отпуск: 5/28 дней"],
                    },
                    {
                        "year": 2024,
                        "month": 7,
                        "key": "jul",
                        "income": 90789,
                        "salary": 90789,
                        "hours": 144,
                        "penalties": ["Штрафов: 1 — превышение времени стоянки"],
                        "absences": ["Больничные: нет", "Отпуск: 9/28 дней"],
                    },
                    {
                        "year": 2024,
                        "month": 8,
                        "key": "aug",
                        "income": 89562,
                        "salary": 89562,
                        "hours": 146,
                        "penalties": ["Штрафов: нет"],
                        "absences": ["Больничные: нет", "Отпуск: 14/28 дней"],
                    },
                    {
                        "year": 2024,
                        "month": 9,
                        "key": "sep",
                        "income": 90349,
                        "salary": 90349,
                        "hours": 148,
                        "penalties": ["Штрафов: нет"],
                        "absences": ["Отсутствия: 1 день за свой счёт"],
                    },
                    {
                        "year": 2024,
                        "month": 10,
                        "key": "oct",
                        "income": 89967,
                        "salary": 92430,
                        "hours": 152,
                        "penalties": ["Штрафов: 1 — превышение времени стоянки"],
                        "absences": ["Больничные: 3 дня (ОРВИ)", "Отпуск: 14/28 дней"],
                    },
                    {
                        "year": 2024,
                        "month": 11,
                        "key": "nov",
                        "income": 96836,
                        "salary": 102430,
                        "hours": 156,
                        "penalties": ["Штрафов: нет"],
                        "absences": ["Больничные: нет", "Отпуск: 18/28 дней"],
                    },
                ],
            )

        # помесячные данные по anna
        anna = db.query(Employee).filter_by(login="anna").first()
        if anna:
            seed_month_stats_for_employee(
                db,
                anna,
                [
                    {
                        "year": 2024,
                        "month": 6,
                        "key": "jun",
                        "income": 60310,
                        "salary": 60310,
                        "hours": 116,
                        "penalties": [],
                        "absences": ["Больничные: нет"],
                    },
                    {
                        "year": 2024,
                        "month": 7,
                        "key": "jul",
                        "income": 62140,
                        "salary": 62140,
                        "hours": 120,
                        "penalties": [],
                        "absences": ["Отпуск: 3/28 дней"],
                    },
                    {
                        "year": 2024,
                        "month": 8,
                        "key": "aug",
                        "income": 64300,
                        "salary": 64300,
                        "hours": 124,
                        "penalties": [],
                        "absences": ["Отпуск: 7/28 дней"],
                    },
                    {
                        "year": 2024,
                        "month": 9,
                        "key": "sep",
                        "income": 70100,
                        "salary": 70100,
                        "hours": 128,
                        "penalties": ["Замечания: 1 — опоздание на планёрку"],
                        "absences": [],
                    },
                    {
                        "year": 2024,
                        "month": 10,
                        "key": "oct",
                        "income": 71500,
                        "salary": 71500,
                        "hours": 130,
                        "penalties": [],
                        "absences": [],
                    },
                    {
                        "year": 2024,
                        "month": 11,
                        "key": "nov",
                        "income": 76800,
                        "salary": 76800,
                        "hours": 132,
                        "penalties": [],
                        "absences": ["Отпуск: 10/28 дней"],
                    },
                ],
            )

        db.commit()
    finally:
        db.close()


# ===============================
#     ПРОВЕРКА ПРАВ АДМИНА
# ===============================

def require_admin(
    db: Session = Depends(get_db),
    admin_login: str = Header(..., alias="X-Admin-Login"),
    admin_password: str = Header(..., alias="X-Admin-Password"),
) -> Admin:
    adm = db.query(Admin).filter(Admin.login == admin_login.lower()).first()
    if not adm or not verify_password(admin_password, adm.password_hash):
        raise HTTPException(status_code=401, detail="Админ не авторизован")
    return adm


# ===============================
#           FASTAPI APP
# ===============================

app = FastAPI(title="LuchWallet API", version="2.2.0")

app.mount("/static", StaticFiles(directory=PHOTOS_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {"status": "ok", "app": "LuchWallet API"}


# ---------- ЛОГИН (сотрудник / админ) ----------

@app.post("/api/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    role = payload.role.lower()
    login_value = payload.login.strip().lower()
    password = payload.password

    if role == "employee":
        emp = db.query(Employee).filter(Employee.login == login_value).first()
        if not emp or not verify_password(password, emp.password_hash):
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")

        # авто-начисление баланса
        accrue_balance_for_employee(emp)
        db.commit()
        db.refresh(emp)

        # помесячные данные для графика
        months = build_months_for_employee(db, emp.id)

        data = {
            "id": emp.id,
            "initials": emp.initials,
            "name": emp.name,
            "position": emp.position,
            "rate": emp.rate,
            "experience": emp.experience,
            "status": emp.status,
            "salary": emp.salary,
            "hours": emp.hours,
            "hoursDetail": emp.hours_detail,
            "penalties": json_loads_list(emp.penalties_json),
            "absences": json_loads_list(emp.absences_json),
            "errorText": emp.error_text or "",
            "photo_url": emp.photo_url,
            "months": months,
        }
        return LoginResponse(role="employee", login=login_value, data=data)

    elif role == "admin":
        adm = db.query(Admin).filter(Admin.login == login_value).first()
        if not adm or not verify_password(password, adm.password_hash):
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")

        data = {"name": adm.name}
        return LoginResponse(role="admin", login=login_value, data=data)

    else:
        raise HTTPException(status_code=400, detail="Неизвестная роль пользователя")


# ---------- АДМИН: СПИСОК СОТРУДНИКОВ ----------

@app.get("/api/employees", response_model=List[EmployeeShort])
def list_employees(
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    emps = db.query(Employee).order_by(Employee.id.asc()).all()
    return emps


# ---------- АДМИН: ПОДРОБНОСТИ СОТРУДНИКА ----------

@app.get("/api/employees/{emp_id}", response_model=EmployeeDetail)
def get_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    accrue_balance_for_employee(emp)
    db.commit()
    db.refresh(emp)

    return EmployeeDetail(
        id=emp.id,
        login=emp.login,
        initials=emp.initials,
        name=emp.name,
        position=emp.position,
        rate=emp.rate,
        experience=emp.experience,
        status=emp.status,
        salary=emp.salary,
        hours=emp.hours,
        hours_detail=emp.hours_detail,
        penalties=json_loads_list(emp.penalties_json),
        absences=json_loads_list(emp.absences_json),
        error_text=emp.error_text,
        photo_url=emp.photo_url,
        is_active=emp.is_active,
        password=emp.password_plain,
    )


# ---------- АДМИН: ДОБАВИТЬ СОТРУДНИКА ----------

@app.post("/api/employees", response_model=EmployeeDetail)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    if db.query(Employee).filter(Employee.login == payload.login.lower()).first():
        raise HTTPException(status_code=400, detail="Логин уже занят")

    emp = Employee(
        login=payload.login.lower(),
        password_hash=get_password_hash(payload.password),
        password_plain=payload.password,
        initials=payload.initials,
        name=payload.name,
        position=payload.position,
        rate=payload.rate,
        experience=payload.experience,
        status=payload.status,
        salary=payload.salary,
        hours=payload.hours,
        hours_detail=payload.hours_detail,
        penalties_json=json_dumps_list(payload.penalties),
        absences_json=json_dumps_list(payload.absences),
        error_text=payload.error_text or "",
        photo_url=payload.photo_url,
        is_active=True,
        balance_int=money_to_int(payload.salary or "0"),
        contract_hours_per_month=None,
        hourly_rate=None,
        schedule_type=None,
        work_start_hour=None,
        work_end_hour=None,
        last_balance_update=datetime.utcnow(),
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)

    return get_employee(emp.id, db=db, admin=admin)


# ---------- АДМИН: ОБНОВИТЬ СОТРУДНИКА ----------

@app.put("/api/employees/{emp_id}", response_model=EmployeeDetail)
def update_employee(
    emp_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    data = payload.dict(exclude_unset=True)

    new_login = data.pop("login", None)
    if new_login:
        new_login = new_login.lower()
        if new_login != emp.login and db.query(Employee).filter(Employee.login == new_login).first():
            raise HTTPException(status_code=400, detail="Новый логин уже занят")
        emp.login = new_login

    new_password = data.pop("password", None)
    if new_password:
        emp.password_hash = get_password_hash(new_password)
        emp.password_plain = new_password

    if "initials" in data:
        emp.initials = data["initials"]
    if "name" in data:
        emp.name = data["name"]
    if "position" in data:
        emp.position = data["position"]
    if "rate" in data:
        emp.rate = data["rate"]
    if "experience" in data:
        emp.experience = data["experience"]
    if "status" in data:
        emp.status = data["status"]
    if "salary" in data:
        emp.salary = data["salary"]
        emp.balance_int = money_to_int(emp.salary)
    if "hours" in data:
        emp.hours = data["hours"]
    if "hours_detail" in data:
        emp.hours_detail = data["hours_detail"]
    if "penalties" in data and data["penalties"] is not None:
        emp.penalties_json = json_dumps_list(data["penalties"])
    if "absences" in data and data["absences"] is not None:
        emp.absences_json = json_dumps_list(data["absences"])
    if "error_text" in data:
        emp.error_text = data["error_text"]
    if "photo_url" in data:
        emp.photo_url = data["photo_url"]

    db.commit()
    db.refresh(emp)

    return get_employee(emp.id, db=db, admin=admin)


# ---------- АДМИН: УДАЛИТЬ СОТРУДНИКА ----------

@app.delete("/api/employees/{emp_id}")
def delete_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    db.delete(emp)
    db.commit()
    return {"status": "deleted", "id": emp_id}


# ---------- АДМИН: ЗАГРУЗКА ФОТО СОТРУДНИКА ----------

@app.post("/api/employees/{emp_id}/photo")
def upload_employee_photo(
    emp_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"employee_{emp_id}{ext}"
    filepath = os.path.join(PHOTOS_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(file.file.read())

    emp.photo_url = f"/static/{filename}"
    db.commit()
    db.refresh(emp)

    return {"status": "ok", "photo_url": emp.photo_url}


# ---------- АДМИН: ЭКСПОРТ КАРТОЧКИ В EXCEL ----------

@app.get("/api/employees/{emp_id}/export")
def export_employee_excel(
    emp_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    wb = Workbook()
    ws = wb.active
    ws.title = "Карточка сотрудника"

    ws.append(["Поле", "Значение"])
    ws.append(["ID", emp.id])
    ws.append(["Логин", emp.login])
    ws.append(["ФИО", emp.name])
    ws.append(["Инициалы", emp.initials])
    ws.append(["Должность", emp.position])
    ws.append(["Оклад", emp.rate or ""])
    ws.append(["Стаж", emp.experience or ""])
    ws.append(["Статус", emp.status or ""])
    ws.append(["Баланс", emp.salary or ""])
    ws.append(["Отработанное время", emp.hours or ""])
    ws.append(["Детализация времени", emp.hours_detail or ""])
    ws.append(["Примечание / ошибка", emp.error_text or ""])

    penalties = " ; ".join(json_loads_list(emp.penalties_json))
    absences = " ; ".join(json_loads_list(emp.absences_json))

    ws.append(["Штрафы и дисциплина", penalties])
    ws.append(["Больничные и отсутствия", absences])

    if emp.photo_url:
        ws.append(["Фото (URL)", emp.photo_url])

    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)

    filename = f"employee_{emp_id}_card.xlsx"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


# ---------- АДМИН: ПЛАТЕЖИ (КОШЕЛЁК) ----------

@app.get("/api/employees/{emp_id}/payments", response_model=List[PaymentOut])
def list_payments_for_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    payments = (
        db.query(Payment)
        .filter(Payment.employee_id == emp_id)
        .order_by(Payment.created_at.desc(), Payment.id.desc())
        .all()
    )
    return payments


@app.post("/api/employees/{emp_id}/payments", response_model=PaymentOut)
def create_payment_for_employee(
    emp_id: int,
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    payment = Payment(
        employee_id=emp_id,
        type=payload.type,
        amount=payload.amount,
        comment=payload.comment,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


@app.delete("/api/payments/{payment_id}")
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(require_admin),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Платёж не найден")

    db.delete(payment)
    db.commit()
    return {"status": "deleted", "id": payment_id}
