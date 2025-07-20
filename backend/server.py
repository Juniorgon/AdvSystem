from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from enum import Enum
import jwt
import bcrypt


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class ClientType(str, Enum):
    individual = "individual"
    corporate = "corporate"

class ProcessRole(str, Enum):
    creditor = "creditor"
    debtor = "debtor"

class TransactionType(str, Enum):
    receita = "receita"
    despesa = "despesa"

class TransactionStatus(str, Enum):
    pendente = "pendente"
    pago = "pago"
    vencido = "vencido"

# Authentication configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'gb_advocacia_secret_key_2025')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

# Authentication Models
class UserRole(str, Enum):
    admin = "admin"
    lawyer = "lawyer"
    secretary = "secretary"

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserInDB(User):
    hashed_password: str

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: UserRole

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# Password hashing utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    user_doc = await db.users.find_one({"username": username})
    if user_doc is None:
        raise credentials_exception
    
    user = User(**user_doc)
    return user

# Models
class Address(BaseModel):
    street: str
    number: str
    city: str
    district: str
    state: str
    complement: Optional[str] = ""

class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    nationality: str
    civil_status: str
    profession: str
    cpf: str
    address: Address
    phone: str
    client_type: ClientType
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ClientCreate(BaseModel):
    name: str
    nationality: str
    civil_status: str
    profession: str
    cpf: str
    address: Address
    phone: str
    client_type: ClientType

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    nationality: Optional[str] = None
    civil_status: Optional[str] = None
    profession: Optional[str] = None
    cpf: Optional[str] = None
    address: Optional[Address] = None
    phone: Optional[str] = None
    client_type: Optional[ClientType] = None

class Process(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    process_number: str
    type: str
    status: str
    value: float
    description: str
    role: ProcessRole
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProcessCreate(BaseModel):
    client_id: str
    process_number: str
    type: str
    status: str
    value: float
    description: str
    role: ProcessRole

class ProcessUpdate(BaseModel):
    process_number: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    value: Optional[float] = None
    description: Optional[str] = None
    role: Optional[ProcessRole] = None

class FinancialTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: Optional[str] = None
    process_id: Optional[str] = None
    type: TransactionType
    description: str
    value: float
    due_date: datetime
    payment_date: Optional[datetime] = None
    status: TransactionStatus
    category: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class FinancialTransactionCreate(BaseModel):
    client_id: Optional[str] = None
    process_id: Optional[str] = None
    type: TransactionType
    description: str
    value: float
    due_date: datetime
    payment_date: Optional[datetime] = None
    status: TransactionStatus = TransactionStatus.pendente
    category: str

class FinancialTransactionUpdate(BaseModel):
    description: Optional[str] = None
    value: Optional[float] = None
    due_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    status: Optional[TransactionStatus] = None
    category: Optional[str] = None

class Contract(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    process_id: Optional[str] = None
    value: float
    payment_conditions: str
    installments: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ContractCreate(BaseModel):
    client_id: str
    process_id: Optional[str] = None
    value: float
    payment_conditions: str
    installments: int

class DashboardStats(BaseModel):
    total_clients: int
    total_processes: int
    total_revenue: float
    total_expenses: float
    pending_payments: int
    overdue_payments: int
    monthly_revenue: float
    monthly_expenses: float

# Authentication endpoints
@api_router.post("/auth/register", response_model=User)
async def register_user(user: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    existing_email = await db.users.find_one({"email": user.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    user_dict = user.dict()
    del user_dict['password']
    
    user_in_db = UserInDB(**user_dict, hashed_password=hashed_password)
    await db.users.insert_one(user_in_db.dict())
    
    return User(**user_dict)

@api_router.post("/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin):
    user_doc = await db.users.find_one({"username": user_credentials.username})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    user_in_db = UserInDB(**user_doc)
    if not verify_password(user_credentials.password, user_in_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    if not user_in_db.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_in_db.username}, expires_delta=access_token_expires
    )
    
    user = User(**{k: v for k, v in user_in_db.dict().items() if k != 'hashed_password'})
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.get("/auth/users", response_model=List[User])
async def get_all_users(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users_cursor = db.users.find()
    users = []
    async for user_doc in users_cursor:
        user = User(**{k: v for k, v in user_doc.items() if k != 'hashed_password'})
        users.append(user)
    
    return users

@api_router.post("/auth/create-admin")
async def create_admin_user():
    # Check if admin already exists
    existing_admin = await db.users.find_one({"role": "admin"})
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin user already exists")
    
    # Create default admin user
    admin_user = UserCreate(
        username="admin",
        email="admin@gbadvocacia.com",
        full_name="Administrador GB Advocacia",
        password="admin123",
        role=UserRole.admin
    )
    
    hashed_password = get_password_hash(admin_user.password)
    user_dict = admin_user.dict()
    del user_dict['password']
    
    user_in_db = UserInDB(**user_dict, hashed_password=hashed_password)
    await db.users.insert_one(user_in_db.dict())
    
    return {"message": "Admin user created successfully", "username": "admin", "password": "admin123"}

# Client endpoints
@api_router.post("/clients", response_model=Client)
async def create_client(client: ClientCreate):
    client_dict = client.dict()
    client_obj = Client(**client_dict)
    await db.clients.insert_one(client_obj.dict())
    return client_obj

@api_router.get("/clients", response_model=List[Client])
async def get_clients():
    clients = await db.clients.find().to_list(1000)
    return [Client(**client) for client in clients]

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str):
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return Client(**client)

@api_router.put("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, client_update: ClientUpdate):
    existing_client = await db.clients.find_one({"id": client_id})
    if not existing_client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    update_data = client_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.clients.update_one({"id": client_id}, {"$set": update_data})
    
    updated_client = await db.clients.find_one({"id": client_id})
    return Client(**updated_client)

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str):
    result = await db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}

# Process endpoints
@api_router.post("/processes", response_model=Process)
async def create_process(process: ProcessCreate):
    # Verify client exists
    client = await db.clients.find_one({"id": process.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    process_dict = process.dict()
    process_obj = Process(**process_dict)
    await db.processes.insert_one(process_obj.dict())
    return process_obj

@api_router.get("/processes", response_model=List[Process])
async def get_processes():
    processes = await db.processes.find().to_list(1000)
    return [Process(**process) for process in processes]

@api_router.get("/processes/{process_id}", response_model=Process)
async def get_process(process_id: str):
    process = await db.processes.find_one({"id": process_id})
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    return Process(**process)

@api_router.get("/clients/{client_id}/processes", response_model=List[Process])
async def get_client_processes(client_id: str):
    processes = await db.processes.find({"client_id": client_id}).to_list(1000)
    return [Process(**process) for process in processes]

@api_router.put("/processes/{process_id}", response_model=Process)
async def update_process(process_id: str, process_update: ProcessUpdate):
    existing_process = await db.processes.find_one({"id": process_id})
    if not existing_process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    update_data = process_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.processes.update_one({"id": process_id}, {"$set": update_data})
    
    updated_process = await db.processes.find_one({"id": process_id})
    return Process(**updated_process)

@api_router.delete("/processes/{process_id}")
async def delete_process(process_id: str):
    result = await db.processes.delete_one({"id": process_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Process not found")
    return {"message": "Process deleted successfully"}

# Financial Transaction endpoints
@api_router.post("/financial", response_model=FinancialTransaction)
async def create_financial_transaction(transaction: FinancialTransactionCreate):
    transaction_dict = transaction.dict()
    transaction_obj = FinancialTransaction(**transaction_dict)
    await db.financial_transactions.insert_one(transaction_obj.dict())
    return transaction_obj

@api_router.get("/financial", response_model=List[FinancialTransaction])
async def get_financial_transactions():
    transactions = await db.financial_transactions.find().to_list(1000)
    return [FinancialTransaction(**transaction) for transaction in transactions]

@api_router.get("/financial/{transaction_id}", response_model=FinancialTransaction)
async def get_financial_transaction(transaction_id: str):
    transaction = await db.financial_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return FinancialTransaction(**transaction)

@api_router.put("/financial/{transaction_id}", response_model=FinancialTransaction)
async def update_financial_transaction(transaction_id: str, transaction_update: FinancialTransactionUpdate):
    existing_transaction = await db.financial_transactions.find_one({"id": transaction_id})
    if not existing_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    update_data = transaction_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.financial_transactions.update_one({"id": transaction_id}, {"$set": update_data})
    
    updated_transaction = await db.financial_transactions.find_one({"id": transaction_id})
    return FinancialTransaction(**updated_transaction)

@api_router.delete("/financial/{transaction_id}")
async def delete_financial_transaction(transaction_id: str):
    result = await db.financial_transactions.delete_one({"id": transaction_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted successfully"}

# Contract endpoints
@api_router.post("/contracts", response_model=Contract)
async def create_contract(contract: ContractCreate):
    # Verify client exists
    client = await db.clients.find_one({"id": contract.client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    contract_dict = contract.dict()
    contract_obj = Contract(**contract_dict)
    await db.contracts.insert_one(contract_obj.dict())
    return contract_obj

@api_router.get("/contracts", response_model=List[Contract])
async def get_contracts():
    contracts = await db.contracts.find().to_list(1000)
    return [Contract(**contract) for contract in contracts]

@api_router.get("/contracts/{contract_id}", response_model=Contract)
async def get_contract(contract_id: str):
    contract = await db.contracts.find_one({"id": contract_id})
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return Contract(**contract)

@api_router.get("/clients/{client_id}/contracts", response_model=List[Contract])
async def get_client_contracts(client_id: str):
    contracts = await db.contracts.find({"client_id": client_id}).to_list(1000)
    return [Contract(**contract) for contract in contracts]

# Dashboard endpoint
@api_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats():
    # Count totals
    total_clients = await db.clients.count_documents({})
    total_processes = await db.processes.count_documents({})
    
    # Calculate financial totals
    revenue_pipeline = [
        {"$match": {"type": "receita"}},
        {"$group": {"_id": None, "total": {"$sum": "$value"}}}
    ]
    revenue_result = await db.financial_transactions.aggregate(revenue_pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    expenses_pipeline = [
        {"$match": {"type": "despesa"}},
        {"$group": {"_id": None, "total": {"$sum": "$value"}}}
    ]
    expenses_result = await db.financial_transactions.aggregate(expenses_pipeline).to_list(1)
    total_expenses = expenses_result[0]["total"] if expenses_result else 0
    
    # Count pending and overdue payments
    pending_payments = await db.financial_transactions.count_documents({"status": "pendente"})
    overdue_payments = await db.financial_transactions.count_documents({"status": "vencido"})
    
    # Calculate monthly revenue and expenses (current month)
    from datetime import datetime, timedelta
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month_start = current_month_start + timedelta(days=32)
    next_month_start = next_month_start.replace(day=1)
    
    monthly_revenue_pipeline = [
        {"$match": {
            "type": "receita",
            "due_date": {"$gte": current_month_start, "$lt": next_month_start}
        }},
        {"$group": {"_id": None, "total": {"$sum": "$value"}}}
    ]
    monthly_revenue_result = await db.financial_transactions.aggregate(monthly_revenue_pipeline).to_list(1)
    monthly_revenue = monthly_revenue_result[0]["total"] if monthly_revenue_result else 0
    
    monthly_expenses_pipeline = [
        {"$match": {
            "type": "despesa",
            "due_date": {"$gte": current_month_start, "$lt": next_month_start}
        }},
        {"$group": {"_id": None, "total": {"$sum": "$value"}}}
    ]
    monthly_expenses_result = await db.financial_transactions.aggregate(monthly_expenses_pipeline).to_list(1)
    monthly_expenses = monthly_expenses_result[0]["total"] if monthly_expenses_result else 0
    
    return DashboardStats(
        total_clients=total_clients,
        total_processes=total_processes,
        total_revenue=total_revenue,
        total_expenses=total_expenses,
        pending_payments=pending_payments,
        overdue_payments=overdue_payments,
        monthly_revenue=monthly_revenue,
        monthly_expenses=monthly_expenses
    )

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()