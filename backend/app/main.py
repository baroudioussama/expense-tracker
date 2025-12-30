from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, validator
from passlib.context import CryptContext
from datetime import datetime, timedelta, UTC
from jose import JWTError, jwt
from typing import Optional, List,Dict
import secrets
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from enum import Enum
from fastapi.middleware.cors import CORSMiddleware
import os
import json

try:
    # For Docker/package usage
    from .category_classifier import CategoryClassifier
except ImportError:
    # For local development
    from category_classifier import CategoryClassifier


# Configuration
SECRET_KEY = os.getenv("SECRET_KEY","c6484b9bb5c5e985f36e7107eb5501a89d866874035ff5b9664da78f6f01c060")
ALGORITHM = os.getenv("ALGORITHM","HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES",30))
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:oussema@localhost:5432/expense_tracker_db"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Debugging
import logging
logging.basicConfig(level=logging.DEBUG)

# Initialize FastAPI
app = FastAPI(title="Personal Expense Tracker")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Load AI model at startup
classifier = CategoryClassifier()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

#####  Database Models  #####
class UserDB(Base):
    __tablename__ = "users"
    
    email = Column(String, primary_key=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    expenses = relationship("ExpenseDB", back_populates="user", cascade="all, delete")

class ResetTokenDB(Base):
    __tablename__ = "reset_tokens"
    
    token = Column(String, primary_key=True, index=True)
    email = Column(String)
    expires = Column(DateTime)

class ExpenseDB(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_email = Column(String, ForeignKey("users.email"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    merchant = Column(String, nullable=True)
    category = Column(String, nullable=False, default="Uncategorized")
    predicted_category = Column(String, nullable=True)
    date = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("UserDB", back_populates="expenses")
    
class IncomeDB(Base):
    __tablename__ = "incomes"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_email = Column(String, ForeignKey("users.email"), nullable=False)
    amount = Column(Float, nullable=False)
    source = Column(String, nullable=False)
    description = Column(String, nullable=True)
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#####  Pydantic Models  #####

# User models
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    
    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v.encode("utf-8")) > 72:
            return v.encode("utf-8")[:72].decode("utf-8", errors="ignore")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPassword(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    token: str
    new_password: str
    @validator("new_password")
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        if len(v.encode("utf-8")) > 72:
            raise ValueError("New password cannot exceed 72 characters")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    email: str
    full_name: str


# Expense models
class ExpenseCreate(BaseModel):
    amount: float
    description: str
    merchant: Optional[str] = None
    category: Optional[str] = None
    date: Optional[datetime] = None
    
    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    merchant: Optional[str] = None
    date: Optional[datetime] = None
    @validator("amount")
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

class ExpenseOut(BaseModel):
    id: int
    user_email: str
    amount: float
    description: Optional[str]
    merchant: Optional[str]
    category: str
    predicted_category: Optional[str]
    date: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# Income models
class IncomeCreate(BaseModel):
    amount: float
    source: str
    description: Optional[str] = None
    date: datetime
    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v
    @validator("source")
    def validate_source(cls, v):
        allowed_sources = [
            "Salary", "Freelance", "Business", "Investment", 
            "Rental", "Gift", "Bonus", "Other"
        ]
        if v not in allowed_sources:
            raise ValueError(f"Source must be one of: {', '.join(allowed_sources)}")
        return v

class IncomeResponse(BaseModel):
    id: int
    user_email: str
    amount: float
    source: str
    description: Optional[str]
    date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class IncomeUpdate(BaseModel):
    amount: Optional[float] = None
    source: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None

# Enums
class OrderBy(str, Enum):
    date = "date"
    amount = "amount"
    category = "category"
    created_at = "created_at"

class OrderDirection(str, Enum):
    asc = "asc"
    desc = "desc"

#####  AI Chatbot Routes  #####

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    data: Optional[Dict] = None

def get_user_financial_context(user_email: str, db: Session) -> str:
    """Get user's financial data for AI context"""
    
    # Get overview
    total_income = db.query(func.sum(IncomeDB.amount)).filter(
        IncomeDB.user_email == user_email
    ).scalar() or 0
    
    total_expenses = db.query(func.sum(ExpenseDB.amount)).filter(
        ExpenseDB.user_email == user_email
    ).scalar() or 0
    
    balance = total_income - total_expenses
    
    # Get expense by category
    expenses_by_category = db.query(
        ExpenseDB.category,
        func.sum(ExpenseDB.amount).label("total")
    ).filter(
        ExpenseDB.user_email == user_email
    ).group_by(ExpenseDB.category).all()
    
    # Get recent expenses
    recent_expenses = db.query(ExpenseDB).filter(
        ExpenseDB.user_email == user_email
    ).order_by(ExpenseDB.date.desc()).limit(10).all()
    
    # Get income sources
    income_sources = db.query(
        IncomeDB.source,
        func.sum(IncomeDB.amount).label("total")
    ).filter(
        IncomeDB.user_email == user_email
    ).group_by(IncomeDB.source).all()
    
    # Build context
    context = f"""
User Financial Summary:
- Total Income: ${total_income:.2f}
- Total Expenses: ${total_expenses:.2f}
- Balance: ${balance:.2f}
- Savings Rate: {(balance/total_income*100):.1f}% if total_income > 0 else 0

Expenses by Category:
{chr(10).join([f"- {cat}: ${amt:.2f}" for cat, amt in expenses_by_category])}

Income Sources:
{chr(10).join([f"- {src}: ${amt:.2f}" for src, amt in income_sources])}

Recent Expenses (last 10):
{chr(10).join([f"- {exp.description}: ${exp.amount:.2f} ({exp.category})" for exp in recent_expenses[:5]])}
"""
    
    return context

def generate_ai_response(user_message: str, context: str) -> str:
    """Generate AI response using simple rule-based system"""
    
    user_message_lower = user_message.lower()
    
    # Simple keyword-based responses
    if any(word in user_message_lower for word in ["hello", "hi", "hey"]):
        return "Hello! I'm your financial assistant. I can help you understand your spending, income, and provide financial advice. What would you like to know?"
    
    elif any(word in user_message_lower for word in ["balance", "how much", "money"]):
        # Extract balance from context
        import re
        balance_match = re.search(r'Balance: \$([0-9.]+)', context)
        if balance_match:
            balance = float(balance_match.group(1))
            return f"Your current balance is ${balance:.2f}. {'Great job saving!' if balance > 0 else 'Consider reducing expenses to improve your balance.'}"
    
    elif "spend" in user_message_lower or "expenses" in user_message_lower:
        # Extract top category
        import re
        categories = re.findall(r'- ([A-Za-z/]+): \$([0-9.]+)', context)
        if categories:
            top_cat, top_amt = categories[0]
            return f"Your highest spending category is {top_cat} with ${float(top_amt):.2f}. Would you like tips on reducing expenses in this area?"
    
    elif "income" in user_message_lower:
        income_match = re.search(r'Total Income: \$([0-9.]+)', context)
        if income_match:
            income = float(income_match.group(1))
            return f"Your total income is ${income:.2f}. You can increase this by exploring side hustles, freelancing, or asking for a raise!"
    
    elif any(word in user_message_lower for word in ["save", "saving", "savings"]):
        return "Here are some savings tips:\n1. Follow the 50-30-20 rule (50% needs, 30% wants, 20% savings)\n2. Automate your savings\n3. Cut unnecessary subscriptions\n4. Cook at home more often\n5. Track every expense"
    
    elif any(word in user_message_lower for word in ["budget", "plan"]):
        return "I recommend the 50-30-20 budget rule:\n- 50% for needs (rent, utilities, groceries)\n- 30% for wants (entertainment, dining out)\n- 20% for savings and debt repayment\n\nCheck your Recommendations page for a personalized budget!"
    
    elif any(word in user_message_lower for word in ["reduce", "cut", "lower"]):
        return "To reduce expenses:\n1. Review subscriptions you don't use\n2. Meal prep instead of eating out\n3. Use public transport\n4. Compare prices before buying\n5. Wait 24 hours before impulse purchases"
    
    elif "recommendation" in user_message_lower or "advice" in user_message_lower:
        return "I analyze your spending patterns and provide personalized recommendations! Check the 'Recommendations' page for detailed insights on improving your financial health."
    
    else:
        return f"I'm here to help with your finances! You can ask me about:\n- Your balance and spending\n- Income sources\n- Savings tips\n- Budget recommendations\n- Expense reduction strategies\n\nWhat would you like to know?"

#####  Helper Functions  #####

# Helper functions
def verify_password(plain_password, hashed_password):
    # Truncate to 72 characters for bcrypt compatibility
    plain_password = str(plain_password)[:72]  # Convert to string and truncate
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # Bcrypt has a 72 character limit
    password = str(password)[:72]  # Convert to string and truncate
    return pwd_context.hash(password)



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(UserDB).filter(UserDB.email == email).first()
    if user is None:
        raise credentials_exception
    return user

#####  Authentication Routes  #####

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserRegister, db: Session = Depends(get_db)):
    """Register a new user account"""
    try:
        logging.debug(f"Attempting to register user: {user.email}")
        
        existing_user = db.query(UserDB).filter(UserDB.email == user.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        hashed_password = get_password_hash(user.password)
        db_user = UserDB(
            email=user.email,
            full_name=user.full_name,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return {"message": "User registered successfully", "email": user.email}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    user = db.query(UserDB).filter(UserDB.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/forgot-password")
async def forgot_password(data: ForgotPassword, db: Session = Depends(get_db)):
    """Request password reset token"""
    user = db.query(UserDB).filter(UserDB.email == data.email).first()
    if not user:
        return {"message": "If the email exists, a reset token has been sent"}
    
    reset_token = secrets.token_urlsafe(32)
    db_token = ResetTokenDB(
        token=reset_token,
        email=data.email,
        expires=datetime.utcnow() + timedelta(hours=1)
    )
    db.add(db_token)
    db.commit()
    
    print(f"Reset token for {data.email}: {reset_token}")
    
    return {
        "message": "If the email exists, a reset token has been sent",
        "reset_token": reset_token
    }

@app.post("/reset-password")
async def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    """Reset password using token"""
    token_data = db.query(ResetTokenDB).filter(ResetTokenDB.token == data.token).first()
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    if datetime.utcnow() > token_data.expires:
        db.delete(token_data)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    user = db.query(UserDB).filter(UserDB.email == token_data.email).first()
    user.hashed_password = get_password_hash(data.new_password)
    db.delete(token_data)
    db.commit()
    
    return {"message": "Password reset successfully"}

@app.get("/me", response_model=User)
async def get_me(current_user: UserDB = Depends(get_current_user)):
    """Get current user information"""
    return {
        "email": current_user.email,
        "full_name": current_user.full_name
    }

#####  Expense Routes with AI  #####

@app.post("/expenses", response_model=ExpenseOut)
async def add_expense(
    expense_in: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Create expense with AI category prediction"""
    # AI MAGIC - Predict category
    predicted= classifier.predict(
        expense_in.description or "", 
        expense_in.merchant or ""
    )
    
    logging.info(f"AI Prediction: {predicted}")
    
    db_expense = ExpenseDB(
        user_email=current_user.email,
        amount=expense_in.amount,
        description=expense_in.description,
        merchant=expense_in.merchant,
        category=expense_in.category or predicted,  # Use user category or AI prediction
        predicted_category=predicted,
        date=expense_in.date or datetime.now(UTC)
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.get("/expenses", response_model=List[ExpenseOut])
async def get_expenses(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    order_by: OrderBy = OrderBy.date,
    order_direction: OrderDirection = OrderDirection.desc,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Get all expenses with filtering and ordering"""
    query = db.query(ExpenseDB).filter(ExpenseDB.user_email == current_user.email)
    
    if category:
        query = query.filter(ExpenseDB.category == category)
    if min_amount is not None:
        query = query.filter(ExpenseDB.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(ExpenseDB.amount <= max_amount)
    if start_date:
        query = query.filter(ExpenseDB.date >= start_date)
    if end_date:
        query = query.filter(ExpenseDB.date <= end_date)
    
    order_column = getattr(ExpenseDB, order_by.value)
    if order_direction == OrderDirection.desc:
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())
    
    return query.offset(skip).limit(limit).all()

@app.get("/expenses/{expense_id}", response_model=ExpenseOut)
async def get_expense(
    expense_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific expense by ID"""
    expense = db.query(ExpenseDB).filter(
        ExpenseDB.id == expense_id,
        ExpenseDB.user_email == current_user.email
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    return expense

@app.put("/expenses/{expense_id}", response_model=ExpenseOut)
async def update_expense(
    expense_id: int,
    expense_update: ExpenseUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an expense"""
    expense = db.query(ExpenseDB).filter(
        ExpenseDB.id == expense_id,
        ExpenseDB.user_email == current_user.email
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    try:
        update_data = expense_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(expense, field, value)
        
        db.commit()
        db.refresh(expense)
        
        return expense
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update expense: {str(e)}"
        )

@app.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an expense"""
    expense = db.query(ExpenseDB).filter(
        ExpenseDB.id == expense_id,
        ExpenseDB.user_email == current_user.email
    ).first()
    
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense not found"
        )
    
    try:
        db.delete(expense)
        db.commit()
        return None
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete expense: {str(e)}"
        )

@app.get("/dashboard/summary")
async def get_summary(
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    """Get expense summary by category"""
    result = db.query(
        ExpenseDB.category,
        func.count().label("count"),
        func.sum(ExpenseDB.amount).label("total")
    ).filter(ExpenseDB.user_email == current_user.email)\
     .group_by(ExpenseDB.category).all()
    
    return [{"category": r[0], "count": r[1], "total": float(r[2] or 0)} for r in result]

#####  Income Routes  #####

@app.post("/income", response_model=IncomeResponse, status_code=status.HTTP_201_CREATED)
async def create_income(
    income: IncomeCreate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new income entry"""
    db_income = IncomeDB(
        user_email=current_user.email,
        amount=income.amount,
        source=income.source,
        description=income.description,
        date=income.date
    )
    db.add(db_income)
    db.commit()
    db.refresh(db_income)
    return db_income

@app.get("/income", response_model=List[IncomeResponse])
async def get_incomes(
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all income entries"""
    incomes = db.query(IncomeDB).filter(
        IncomeDB.user_email == current_user.email
    ).order_by(IncomeDB.date.desc()).all()
    return incomes

@app.put("/income/{income_id}", response_model=IncomeResponse)
async def update_income(
    income_id: int,
    income_update: IncomeUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an income entry"""
    income = db.query(IncomeDB).filter(
        IncomeDB.id == income_id,
        IncomeDB.user_email == current_user.email
    ).first()

    if not income:
        raise HTTPException(status_code=404, detail="Income not found")

    for field, value in income_update.dict(exclude_unset=True).items():
        setattr(income, field, value)

    db.commit()
    db.refresh(income)
    return income


@app.delete("/income/{income_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_income(
    income_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an income entry"""
    income = db.query(IncomeDB).filter(
        IncomeDB.id == income_id,
        IncomeDB.user_email == current_user.email
    ).first()
    
    if not income:
        raise HTTPException(status_code=404, detail="Income not found")
    
    db.delete(income)
    db.commit()

@app.get("/financial-overview")
async def get_financial_overview(
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get income vs expenses overview"""
    total_expenses = db.query(func.sum(ExpenseDB.amount)).filter(
        ExpenseDB.user_email == current_user.email
    ).scalar() or 0
    
    total_income = db.query(func.sum(IncomeDB.amount)).filter(
        IncomeDB.user_email == current_user.email
    ).scalar() or 0
    
    balance = total_income - total_expenses
    
    return {
        "total_income": float(total_income),
        "total_expenses": float(total_expenses),
        "balance": float(balance),
        "savings_rate": round((balance / total_income * 100), 2) if total_income > 0 else 0
    }



@app.get("/dashboard/monthly-stats")
async def get_monthly_stats(
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monthly expense statistics"""
    result = db.query(
        func.date_trunc('month', ExpenseDB.date).label('month'),
        func.sum(ExpenseDB.amount).label('total_expenses'),
        func.count().label('num_expenses')
    ).filter(
        ExpenseDB.user_email == current_user.email
    ).group_by(
        func.date_trunc('month', ExpenseDB.date)
    ).order_by("month").all()
    
    return [
        {
            "month": str(r.month.date()),
            "total_expenses": float(r.total_expenses),
            "num_expenses": r.num_expenses
        }
        for r in result
    ]

@app.get("/recommendations")
async def get_recommendations(
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized financial recommendations"""
    # Fetch totals
    total_income = db.query(func.sum(IncomeDB.amount)).filter(
        IncomeDB.user_email == current_user.email
    ).scalar() or 0
    
    total_expenses = db.query(func.sum(ExpenseDB.amount)).filter(
        ExpenseDB.user_email == current_user.email
    ).scalar() or 0
    
    balance = total_income - total_expenses
    
    # Fetch category distribution
    categories = db.query(
        ExpenseDB.category,
        func.sum(ExpenseDB.amount).label("total")
    ).filter(
        ExpenseDB.user_email == current_user.email
    ).group_by(ExpenseDB.category).all()
    
    category_data = {cat: float(total) for cat, total in categories}
    
    recs = []
    
    # 1. Overspending warning
    if total_expenses > total_income:
        overspending = total_expenses - total_income
        recs.append({
            "type": "warning",
            "priority": "high",
            "title": "Overspending Alert",
            "message": f"⚠️ You are spending ${overspending:.2f} more than you earn. Consider reducing high-cost categories.",
            "action": "Review your expenses and cut unnecessary spending"
        })
    
    # 2. High category spending
    if category_data:
        highest_cat = max(category_data, key=category_data.get)
        highest_amount = category_data[highest_cat]
        percentage = (highest_amount / total_expenses * 100) if total_expenses > 0 else 0
        
        recs.append({
            "type": "insight",
            "priority": "medium",
            "title": "Highest Spending Category",
            "message": f"📌 Your highest spending category is **{highest_cat}** (${highest_amount:.2f}, {percentage:.1f}% of total).",
            "action": f"Try reducing {highest_cat} spending by 10-15% next month to save ${highest_amount * 0.1:.2f}-${highest_amount * 0.15:.2f}"
        })
    
    # 3. Savings advice
    if balance > 0:
        savings_rate = (balance / total_income * 100) if total_income > 0 else 0
        
        if savings_rate >= 20:
            recs.append({
                "type": "success",
                "priority": "low",
                "title": "Great Savings!",
                "message": f"💰 Excellent! You're saving {savings_rate:.1f}% of your income (${balance:.2f}).",
                "action": "Keep up the good work! Consider investing your savings."
            })
        elif savings_rate >= 10:
            recs.append({
                "type": "success",
                "priority": "low",
                "title": "Good Savings",
                "message": f"💰 You're saving {savings_rate:.1f}% of your income (${balance:.2f}).",
                "action": "Try to increase your savings rate to 20% for better financial health."
            })
        else:
            recs.append({
                "type": "info",
                "priority": "medium",
                "title": "Low Savings Rate",
                "message": f"💵 You're saving only {savings_rate:.1f}% of your income (${balance:.2f}).",
                "action": "Financial experts recommend saving at least 20% of your income. Look for areas to cut spending."
            })
    else:
        recs.append({
            "type": "error",
            "priority": "high",
            "title": "Negative Balance",
            "message": f"⛔ You have a deficit of ${abs(balance):.2f}.",
            "action": "Urgently reduce optional expenses and consider additional income sources."
        })
    
    # 4. Food spending check
    food_categories = ["Food", "Groceries", "Restaurant", "Dining", "Entertainment"]
    food_spending = sum(category_data.get(cat, 0) for cat in food_categories)
    
    if total_expenses > 0 and food_spending / total_expenses > 0.3:
        food_percentage = (food_spending / total_expenses * 100)
        recs.append({
            "type": "warning",
            "priority": "medium",
            "title": "High Food Spending",
            "message": f"🍽 You spend {food_percentage:.1f}% on food and entertainment (${food_spending:.2f}).",
            "action": "Try meal prepping, cooking at home, or limiting takeout to save money."
        })
    
    # 5. Housing cost check
    housing_categories = ["Rent/Mortgage", "Utilities", "Insurance"]
    housing_cost = sum(category_data.get(cat, 0) for cat in housing_categories)
    
    if total_income > 0:
        housing_percentage = (housing_cost / total_income * 100)
        if housing_percentage > 30:
            recs.append({
                "type": "warning",
                "priority": "high",
                "title": "High Housing Costs",
                "message": f"🏠 Your housing costs are {housing_percentage:.1f}% of income (${housing_cost:.2f}).",
                "action": "Consider finding cheaper housing or increasing your income. Experts recommend keeping housing under 30% of income."
            })
    
    # 6. Debt check
    debt_spending = category_data.get("Debt/Loans", 0)
    if debt_spending > 0 and total_income > 0:
        debt_percentage = (debt_spending / total_income * 100)
        if debt_percentage > 15:
            recs.append({
                "type": "warning",
                "priority": "high",
                "title": "High Debt Payments",
                "message": f"💳 You're spending {debt_percentage:.1f}% on debt (${debt_spending:.2f}).",
                "action": "Focus on paying off high-interest debt first. Consider debt consolidation."
            })
    
    # 7. No expenses tracked
    if total_expenses == 0:
        recs.append({
            "type": "info",
            "priority": "low",
            "title": "Start Tracking",
            "message": "📝 You haven't tracked any expenses yet!",
            "action": "Start logging your daily expenses to get personalized recommendations."
        })
    
    # --- Month-to-Month Spending Trend (Improved) ---
    today = datetime.now(UTC)
    last_30 = today - timedelta(days=30)
    prev_30 = today - timedelta(days=60)
    
    last_month_expenses = db.query(func.sum(ExpenseDB.amount)).filter(
        ExpenseDB.user_email == current_user.email,
        ExpenseDB.date >= last_30
    ).scalar() or 0
    
    previous_month_expenses = db.query(func.sum(ExpenseDB.amount)).filter(
        ExpenseDB.user_email == current_user.email,
        ExpenseDB.date >= prev_30,
        ExpenseDB.date < last_30
    ).scalar() or 0
    
    # 8. Spending Trend — Compare Last Month vs Previous Month
    if previous_month_expenses > 0 and last_month_expenses > previous_month_expenses:
        increase = (last_month_expenses - previous_month_expenses) / previous_month_expenses * 100
        recs.append({
            "type": "warning",
            "priority": "medium",
            "title": "Monthly Spending Increase",
            "message": (
                f"📈 Your spending increased by {increase:.1f}% compared to the previous month "
                f"(${previous_month_expenses:.2f} → ${last_month_expenses:.2f})."
            ),
            "action": "Review last month's expenses and identify categories driving the increase."
        })
    elif previous_month_expenses > 0 and last_month_expenses < previous_month_expenses:
        decrease = (previous_month_expenses - last_month_expenses) / previous_month_expenses * 100
        recs.append({
            "type": "success",
            "priority": "low",
            "title": "Good Job Reducing Spending",
            "message": (
                f"📉 Your monthly spending decreased by {decrease:.1f}% compared to the previous month "
                f"(${previous_month_expenses:.2f} → ${last_month_expenses:.2f})."
            ),
            "action": "Keep maintaining this positive trend!"
        })
    
    # Calculate financial health score
    health_score = 0
    if total_income > 0:
        savings_rate = (balance / total_income * 100) if balance > 0 else 0
        if savings_rate >= 20:
            health_score += 40
        elif savings_rate >= 10:
            health_score += 25
        elif savings_rate > 0:
            health_score += 10
        
        if housing_cost / total_income <= 0.3:
            health_score += 30
        
        if total_expenses > 0 and food_spending / total_expenses <= 0.3:
            health_score += 20
        
        if total_income > 0 and debt_spending / total_income <= 0.15:
            health_score += 10
    
    return {
        "financial_health_score": min(health_score, 100),
        "health_level": "Excellent" if health_score >= 80 else "Good" if health_score >= 60 else "Fair" if health_score >= 40 else "Needs Improvement",
        "total_income": float(total_income),
        "total_expenses": float(total_expenses),
        "balance": float(balance),
        "savings_rate": round((balance / total_income * 100), 2) if total_income > 0 else 0,
        "spending_trend": {
            "last_month": float(last_month_expenses),
            "previous_month": float(previous_month_expenses),
            "change_percentage": round(((last_month_expenses - previous_month_expenses) / previous_month_expenses * 100), 2) if previous_month_expenses > 0 else None
        },
        "recommendations": recs,
        "category_breakdown": category_data
    }

@app.get("/budget-suggestions")
async def get_budget_suggestions(
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get suggested budget based on 50-30-20 rule"""
    total_income = db.query(func.sum(IncomeDB.amount)).filter(
        IncomeDB.user_email == current_user.email
    ).scalar() or 0
    
    if total_income == 0:
        return {
            "message": "Add income entries to get budget suggestions",
            "suggested_budget": {}
        }
    
    # 50-30-20 Budget Rule
    suggested_budget = {
        "needs": {
            "amount": total_income * 0.50,
            "percentage": 50,
            "categories": ["Rent/Mortgage", "Utilities", "Groceries", "Transport", "Insurance"],
            "description": "Essential expenses"
        },
        "wants": {
            "amount": total_income * 0.30,
            "percentage": 30,
            "categories": ["Entertainment", "Dining", "Travel", "Shopping"],
            "description": "Non-essential spending"
        },
        "savings": {
            "amount": total_income * 0.20,
            "percentage": 20,
            "categories": ["Saving", "Investment", "Debt/Loans"],
            "description": "Savings and debt repayment"
        }
    }
    
    return {
        "total_income": float(total_income),
        "suggested_budget": suggested_budget,
        "rule": "50-30-20 Rule",
        "description": "50% needs, 30% wants, 20% savings"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(
    message: ChatMessage,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI Chatbot endpoint"""
    try:
        # Get user's financial context
        context = get_user_financial_context(current_user.email, db)
        
        # Generate response
        response = generate_ai_response(message.message, context)
        
        return ChatResponse(response=response)
        
    except Exception as e:
        logging.error(f"Chat error: {str(e)}")
        return ChatResponse(
            response="Sorry, I encountered an error. Please try again."
        )

#####  Root  #####

@app.get("/")
async def root():
    return {
        "message": "Personal Expense Tracker API",
        "version": "1.0",
        "features": ["Authentication", "Expenses with AI", "Income", "Financial Overview"]
    }