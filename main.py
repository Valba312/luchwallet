import os
import io
from datetime import datetime
from typing import List, Optional

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Depends,
    HTTPException,
    Header,
)
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    relationship,
    Session,
)

from openpyxl import Workbook

# =========================
#     НАСТРОЙКА БАЗЫ
# =========================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./luchwallet.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
#        МОДЕЛИ
# =========================

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    initials = Column(String, nullable=True)
    name = Column(String, nullable=True)
    position = Column(String, nullable=True)

    rate = Column(String, nullable=True)          # "1850 ₽/смена"
    experience = Column(String, nullable=True)    # "4 года 7 мес."
    status = Column(String, nullable=True)        # "Активен · Основное место"

    salary = Column(String, nullable=True)        # "92430 ₽"
    hours = Column(String, nullable=True)         # "152 ч"
    hours_detail = Column(String, nullable=True)  # "Переработка: 0 ч · Ночные: 0 ч."

    penalties_raw = Column(Text, nullable=True)   # строки через \n
    absences_raw = Column(Text, nullable=True)    # строки через \n
    error_text = Column(String, nullable=True)

    photo_url = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    payments = relationship("Payment", back_populates="employee", cascade="all,delete")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    type = Column(String, nullable=False)  # salary / bonus / overtime / night / fine / other
    amount = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="payments")


Base.metadata.create_all(bind=engine)


# =========================
#      Pydantic-схемы
# =========================

class LoginRequest(BaseModel):
    role: str
    login: str
    password: str


class EmployeeBase(BaseModel):
    login: str
    initials: Optional[str] = None
    name: Optional[str] = None
    position: Optional[str] = None
    rate: Optional[str] = None
    experience: Optional[str] = None
    status: Optional[str] = None
    salary: Optional[str] = None
    hours: Optional[str] = None
    hours_detail: Optional[str] = None
    penalties: List[str] = []
    absences: List[str] = []
    error_text: Optional[str] = None
    photo_url: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    password: str


class EmployeeUpdate(EmployeeBase):
    password: Optional[str] = None


class EmployeeOut(EmployeeBase):
    id: int

    class Config:
      orm_mode = True


class PaymentCreate(BaseModel):
    type: str
    amount: int
    comment: Optional[str] = None


class PaymentOut(BaseModel):
    id: int
    employee_id: int
    type: str
    amount: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class EmployeePaymentsRequest(BaseModel):
    login: str
    password: str


# =========================
#      УТИЛИТЫ
# =========================

ADMIN_LOGIN = os.getenv("ADMIN_LOGIN", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def check_admin(
    x_admin_login: str | None = Header(None, alias="X-Admin-Login"),
    x_admin_password: str | None = Header(None, alias="X-Admin-Password"),
):
    if x_admin_login != ADMIN_LOGIN or x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Админ: неверный логин или пароль")


def penalties_to_text(p_list: List[str]) -> str:
    return "\n".join(p_list or [])


def text_to_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [s.strip() for s in value.split("\n") if s.strip()]


def serialize_employee(emp: Employee) -> dict:
    """То, что получает фронт в режиме сотрудника (user.data)."""
    data = {
        "id": emp.id,
        "login": emp.login,
        "initials": emp.initials or "",
        "name": emp.name or "",
        "position": emp.position or "",
        "rate": emp.rate or "",
        "experience": emp.experience or "",
        "status": emp.status or "",
        "salary": emp.salary or "",
        "hours": emp.hours or "",
        "hoursDetail": emp.hours_detail or "",
        "hours_detail": emp.hours_detail or "",
        "penalties": text_to_list(emp.penalties_raw),
        "absences": text_to_list(emp.absences_raw),
        "errorText": emp.error_text or "",
        "error_text": emp.error_text or "",
        "photo_url": emp.photo_url or "",
    }

    # Месячные данные по платежам
    data["months"] = build_months_for_employee(emp)
    return data


def month_names_short_ru():
    return ["Янв", "Фев", "Мар", "Апр", "Май", "Июн",
            "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]


def month_names_full_ru():
    return ["январь", "февраль", "март", "апрель", "май", "июнь",
            "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]


def build_months_for_employee(emp: Employee) -> List[dict]:
    """Строим последние 12 месяцев по платежам (как для графика дохода)."""
    if not emp.payments:
        return []

    # сгруппируем по (год, месяц)
    by_ym: dict[tuple[int, int], List[Payment]] = {}
    for p in emp.payments:
        d = p.created_at or datetime.utcnow()
        key = (d.year, d.month)
        by_ym.setdefault(key, []).append(p)

    short_names = month_names_short_ru()
    full_names = month_names_full_ru()

    months = []
    for (year, month) in sorted(by_ym.keys()):
        plist = by_ym[(year, month)]
        income = sum(p.amount for p in plist)
        # Зарплата = только положительные суммы
        salary_val = sum(p.amount for p in plist if p.amount > 0)
        # для часов можно ничего не считать — пусть остаётся None
        penalties_texts = [
            (p.comment or "").strip()
            for p in plist
            if p.amount < 0 or p.type == "fine"
        ]
        penalties_texts = [t for t in penalties_texts if t]

        months.append(
            {
                "key": f"{year}-{month:02d}",
                "year": year,
                "month": month,
                "short": short_names[month - 1],
                "fullName": full_names[month - 1].capitalize(),
                "income": income,
                "salary": salary_val,
                "hours": None,
                "penalties": penalties_texts,
                "absences": text_to_list(emp.absences_raw),
            }
        )

    return months


def format_rub(num: Optional[int]) -> str:
    if num is None:
        return ""
    return f"{num:,.0f} ₽".replace(",", " ")


# =========================
#       FASTAPI APP
# =========================

app = FastAPI(title="LuchWallet API")

# CORS (чтобы фронт на Vercel мог стучаться)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # при желании можно ужесточить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статика для фотографий
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# =========================
#         ЭНДПОИНТЫ
# =========================

@app.post("/api/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    role = body.role.lower()
    login = body.login.strip().lower()
    password = body.password

    if role == "admin":
        if login == ADMIN_LOGIN and password == ADMIN_PASSWORD:
            return {"role": "admin", "login": login}
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    if role == "employee":
        emp = db.query(Employee).filter(Employee.login == login).first()
        if not emp or emp.password != password:
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")

        data = serialize_employee(emp)
        return {"role": "employee", "login": login, "data": data}

    raise HTTPException(status_code=400, detail="Неизвестная роль")


# ---------- EMPLOYEES (админ) ----------

@app.get("/api/employees", response_model=List[EmployeeOut])
def list_employees(
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),
):
    emps = db.query(Employee).order_by(Employee.id.asc()).all()
    return [
        EmployeeOut(
            id=e.id,
            login=e.login,
            initials=e.initials,
            name=e.name,
            position=e.position,
            rate=e.rate,
            experience=e.experience,
            status=e.status,
            salary=e.salary,
            hours=e.hours,
            hours_detail=e.hours_detail,
            penalties=text_to_list(e.penalties_raw),
            absences=text_to_list(e.absences_raw),
            error_text=e.error_text,
            photo_url=e.photo_url,
        )
        for e in emps
    ]


@app.get("/api/employees/{emp_id}", response_model=EmployeeOut)
def get_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    return EmployeeOut(
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
        penalties=text_to_list(emp.penalties_raw),
        absences=text_to_list(emp.absences_raw),
        error_text=emp.error_text,
        photo_url=emp.photo_url,
    )


@app.post("/api/employees", response_model=EmployeeOut)
def create_employee(
    body: EmployeeCreate,
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),
):
    existing = db.query(Employee).filter(Employee.login == body.login).first()
    if existing:
        raise HTTPException(status_code=400, detail="Логин уже используется")

    emp = Employee(
        login=body.login.strip().lower(),
        password=body.password,
        initials=body.initials,
        name=body.name,
        position=body.position,
        rate=body.rate,
        experience=body.experience,
        status=body.status,
        salary=body.salary,
        hours=body.hours,
        hours_detail=body.hours_detail,
        penalties_raw=penalties_to_text(body.penalties),
        absences_raw="\n".join(body.absences or []),
        error_text=body.error_text,
        photo_url=body.photo_url,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return get_employee(emp.id, db)


@app.put("/api/employees/{emp_id}", response_model=EmployeeOut)
def update_employee(
    emp_id: int,
    body: EmployeeUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    # проверка логина на уникальность
    if body.login and body.login != emp.login:
        exists = (
            db.query(Employee)
            .filter(Employee.login == body.login, Employee.id != emp_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="Логин уже используется")

    emp.login = body.login.strip().lower()
    if body.password:
        emp.password = body.password

    emp.initials = body.initials
    emp.name = body.name
    emp.position = body.position
    emp.rate = body.rate
    emp.experience = body.experience
    emp.status = body.status
    emp.salary = body.salary
    emp.hours = body.hours
    emp.hours_detail = body.hours_detail
    emp.penalties_raw = penalties_to_text(body.penalties)
    emp.absences_raw = "\n".join(body.absences or [])
    emp.error_text = body.error_text
    emp.photo_url = body.photo_url

    db.commit()
    db.refresh(emp)
    return get_employee(emp.id, db)


@app.delete("/api/employees/{emp_id}")
def delete_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    db.delete(emp)
    db.commit()
    return {"ok": True}


# ---------- ЗАГРУЗКА ФОТО (админ) ----------

@app.post("/api/employees/{emp_id}/photo")
def upload_employee_photo(
    emp_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    filename = f"employee_{emp_id}{ext}"
    filepath = os.path.join("static", filename)

    with open(filepath, "wb") as f:
        f.write(file.file.read())

    url = f"/static/{filename}"
    emp.photo_url = url
    db.commit()
    db.refresh(emp)
    return {"photo_url": url}


# ---------- PAYMENTS (админ) ----------

@app.get("/api/employees/{emp_id}/payments", response_model=List[PaymentOut])
def get_payments_for_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    payments = (
        db.query(Payment)
        .filter(Payment.employee_id == emp_id)
        .order_by(Payment.created_at.desc())
        .all()
    )
    return payments


@app.post("/api/employees/{emp_id}/payments", response_model=PaymentOut)
def add_payment_for_employee(
    emp_id: int,
    body: PaymentCreate,
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    payment = Payment(
        employee_id=emp_id,
        type=body.type,
        amount=body.amount,
        comment=body.comment,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@app.delete("/api/payments/{payment_id}")
def delete_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),
):
    p = db.query(Payment).filter(Payment.id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Операция не найдена")
    db.delete(p)
    db.commit()
    return {"ok": True}


# ---------- ЭКСПОРТ В EXCEL (админ) ----------

@app.get("/api/employees/{emp_id}/export")
def export_employee_excel(
    emp_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")

    wb = Workbook()
    ws = wb.active
    ws.title = "Карточка сотрудника"

    ws["A1"] = "ID"
    ws["B1"] = emp.id

    ws["A2"] = "Логин"
    ws["B2"] = emp.login

    ws["A3"] = "ФИО"
    ws["B3"] = emp.name

    ws["A4"] = "Должность"
    ws["B4"] = emp.position

    ws["A5"] = "Оклад"
    ws["B5"] = emp.rate

    ws["A6"] = "Стаж"
    ws["B6"] = emp.experience

    ws["A7"] = "Статус"
    ws["B7"] = emp.status

    ws["A8"] = "Баланс"
    ws["B8"] = emp.salary

    ws["A9"] = "Отработанное время"
    ws["B9"] = emp.hours

    ws["A10"] = "Детализация времени"
    ws["B10"] = emp.hours_detail

    ws["A11"] = "Штрафы и прогулы"
    ws["B11"] = emp.penalties_raw or ""

    ws["A12"] = "Больничные и отсутствия"
    ws["B12"] = emp.absences_raw or ""

    ws["A13"] = "Примечание / ошибка"
    ws["B13"] = emp.error_text or ""

    # Лист с операциями
    ws2 = wb.create_sheet("Операции")
    ws2.append(["Дата", "Тип", "Сумма", "Комментарий"])
    for p in emp.payments:
        ws2.append(
            [
                p.created_at.strftime("%d.%m.%Y %H:%M"),
                p.type,
                p.amount,
                p.comment or "",
            ]
        )

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"employee_{emp_id}_card.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


# ---------- НОВЫЙ ЭНДПОИНТ ДЛЯ СОТРУДНИКА: ИСТОРИЯ ОПЕРАЦИЙ ----------

@app.post("/api/employee/payments", response_model=List[PaymentOut])
def employee_payments(
    body: EmployeePaymentsRequest,
    db: Session = Depends(get_db),
):
    """История операций для сотрудника (логин/пароль как при входе в кошелёк)."""
    login = body.login.strip().lower()
    emp = db.query(Employee).filter(Employee.login == login).first()
    if not emp or emp.password != body.password:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    payments = (
        db.query(Payment)
        .filter(Payment.employee_id == emp.id)
        .order_by(Payment.created_at.desc())
        .all()
    )
    return payments
