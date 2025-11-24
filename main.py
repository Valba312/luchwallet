from datetime import datetime
import json
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
)
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from passlib.context import CryptContext


# ===============================
#   НАСТРОЙКА БАЗЫ ДАННЫХ
# ===============================

# Локальная SQLite
DATABASE_URL = "sqlite:///./luchwallet.db"

# Для PostgreSQL потом будет так:
# DATABASE_URL = "postgresql+psycopg2://user:password@host:5432/dbname"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Используем argon2
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

    initials = Column(String(8), nullable=False)
    name = Column(String(255), nullable=False)
    position = Column(String(255), nullable=False)

    rate = Column(String(50), nullable=True)         # "1 850 ₽/смена"
    experience = Column(String(50), nullable=True)   # "4 года 7 мес."
    status = Column(String(100), nullable=True)      # "Активен · Основное место"

    salary = Column(String(50), nullable=True)       # "92 430 ₽"
    hours = Column(String(50), nullable=True)        # "152 ч"
    hours_detail = Column(String(255), nullable=True)

    penalties_json = Column(Text, nullable=True)     # JSON-список строк
    absences_json = Column(Text, nullable=True)      # JSON-список строк

    error_text = Column(String(255), nullable=True)

    photo_url = Column(String(512), nullable=True)   # ссылка на фото (аватар)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


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
    # все поля опциональные, можно менять только то, что нужно
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
    # смена логина/пароля при необходимости
    login: Optional[str] = None
    password: Optional[str] = None


class EmployeeShort(BaseModel):
    id: int
    login: str
    name: str
    position: str
    is_active: bool
    photo_url: Optional[str] = None

    class Config:
        orm_mode = True


class EmployeeDetail(EmployeeBase):
    id: int
    login: str
    is_active: bool

    class Config:
        orm_mode = True


# ===============================
#        ИНИЦИАЛИЗАЦИЯ БД
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


def init_db():
    """Создаём таблицы и демо-данные."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # демо-сотрудник ivan
        if not db.query(Employee).filter_by(login="ivan").first():
            emp = Employee(
                login="ivan",
                password_hash=get_password_hash("1234"),
                initials="ИИ",
                name="Иванов Иван Иванович",
                position="Водитель грузового автомобиля · Колонна № 3",
                rate="1 850 ₽/смена",
                experience="4 года 7 мес.",
                status="Активен · Основное место",
                salary="92 430 ₽",
                hours="152 ч",
                hours_detail="Переработка: 18 ч · Ночные: 12 ч.",
                penalties_json=json_dumps_list([
                    "Штрафов: 1 — превышение времени стоянки",
                    "Прогулы: нет",
                    "Замечания: отсутствуют",
                ]),
                absences_json=json_dumps_list([
                    "Больничные: 3 дня (ОРВИ)",
                    "Отпуск: 14/28 дней",
                    "Отсутствия: 1 день за свой счёт",
                ]),
                error_text="",
                photo_url=None,
            )
            db.add(emp)

        # демо-сотрудник anna
        if not db.query(Employee).filter_by(login="anna").first():
            emp = Employee(
                login="anna",
                password_hash=get_password_hash("qwerty"),
                initials="АП",
                name="Антонова Анна Петровна",
                position="Диспетчер смен · Офис № 2",
                rate="2 050 ₽/смена",
                experience="2 года 3 мес.",
                status="Активна · Совместительство",
                salary="74 300 ₽",
                hours="128 ч",
                hours_detail="Переработка: 6 ч · Ночные: 4 ч.",
                penalties_json=json_dumps_list([
                    "Штрафов: нет",
                    "Прогулы: нет",
                    "Замечания: 1 — опоздание на планёрку",
                ]),
                absences_json=json_dumps_list([
                    "Больничные: не было",
                    "Отпуск: 7/28 дней",
                    "Отсутствия: нет",
                ]),
                error_text="",
                photo_url=None,
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
    """
    Примитивная авторизация админа:
    любой admin-эндпоинт требует два заголовка:
    X-Admin-Login и X-Admin-Password.
    """
    adm = db.query(Admin).filter(Admin.login == admin_login.lower()).first()
    if not adm or not verify_password(admin_password, adm.password_hash):
        raise HTTPException(status_code=401, detail="Админ не авторизован")
    return adm


# ===============================
#           FASTAPI APP
# ===============================

app = FastAPI(title="LuchWallet API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # потом можно ограничить доменом фронта
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

        data = {
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

    # изменение логина
    new_login = data.pop("login", None)
    if new_login:
        new_login = new_login.lower()
        if new_login != emp.login and db.query(Employee).filter(Employee.login == new_login).first():
            raise HTTPException(status_code=400, detail="Новый логин уже занят")
        emp.login = new_login

    # изменение пароля
    new_password = data.pop("password", None)
    if new_password:
        emp.password_hash = get_password_hash(new_password)

    # остальные поля
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
