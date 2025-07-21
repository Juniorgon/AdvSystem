from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
from enum import Enum
import jwt
import bcrypt
import asyncio
from whatsapp_service import PaymentReminderService, WhatsAppService
from scheduler import PaymentScheduler


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize WhatsApp and Scheduler services
payment_reminder_service = PaymentReminderService(db)
payment_scheduler = PaymentScheduler(db)
whatsapp_service = WhatsAppService()

# Create the main app without a prefix
app = FastAPI()

# Start scheduler on startup
@app.on_event("startup")
async def startup_event():
    payment_scheduler.start()
    logging.info("PaymentScheduler iniciado")

@app.on_event("shutdown") 
async def shutdown_event():
    payment_scheduler.stop()
    logging.info("PaymentScheduler parado")

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

# Enums
class ClientType(str, Enum):
    individual = "individual"
    corporate = "corporate"

class TransactionType(str, Enum):
    receita = "receita"
    despesa = "despesa"

class TransactionStatus(str, Enum):
    pendente = "pendente"
    pago = "pago"
    vencido = "vencido"

# Authentication Models
class UserRole(str, Enum):
    admin = "admin"
    lawyer = "lawyer"
    secretary = "secretary"

# Branch Models
class Branch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    cnpj: str
    address: str
    phone: str
    email: str
    responsible: str  # Nome do responsável
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BranchCreate(BaseModel):
    name: str
    cnpj: str
    address: str
    phone: str
    email: str
    responsible: str

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    full_name: str
    role: UserRole
    branch_id: Optional[str] = None  # Vinculação com filial
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
    branch_id: Optional[str] = None

class UserLogin(BaseModel):
    username_or_email: str  # Pode ser username ou email
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
        username_or_email: str = payload.get("sub")
        if username_or_email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Try to find in users first
    user_doc = await db.users.find_one({
        "$or": [
            {"username": username_or_email},
            {"email": username_or_email}
        ]
    })
    if user_doc:
        return User(**user_doc)
    
    # Try to find in lawyers (for lawyer authentication)
    lawyer_doc = await db.lawyers.find_one({"email": username_or_email})
    if lawyer_doc:
        # Create user object from lawyer data
        user_dict = {
            "id": lawyer_doc['id'],
            "username": lawyer_doc['email'],
            "email": lawyer_doc['email'],
            "full_name": lawyer_doc['full_name'],
            "role": UserRole.lawyer,
            "branch_id": lawyer_doc['branch_id'],
            "is_active": lawyer_doc['is_active'],
            "created_at": lawyer_doc['created_at']
        }
        return User(**user_dict)
    
    raise credentials_exception

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
    branch_id: str  # Vinculação obrigatória com filial
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
    branch_id: str  # Vinculação obrigatória com filial

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
    branch_id: str  # Vinculação obrigatória com filial
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
    branch_id: str  # Vinculação obrigatória com filial

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
    branch_id: str  # Vinculação obrigatória com filial
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
    branch_id: str  # Vinculação obrigatória com filial

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
    branch_id: str  # Vinculação obrigatória com filial
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ContractCreate(BaseModel):
    client_id: str
    process_id: Optional[str] = None
    value: float
    payment_conditions: str
    installments: int
    branch_id: str  # Vinculação obrigatória com filial

class Lawyer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str
    oab_number: str
    oab_state: str  # Estado da OAB (SP, RJ, MG, etc.)
    email: str
    phone: str
    specialization: Optional[str] = ""
    branch_id: str  # Vinculação obrigatória com filial
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class LawyerCreate(BaseModel):
    full_name: str
    oab_number: str
    oab_state: str
    email: str
    phone: str
    specialization: Optional[str] = ""
    branch_id: str  # Vinculação obrigatória com filial

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
    # Try to find user by username or email
    user_doc = await db.users.find_one({
        "$or": [
            {"username": user_credentials.username_or_email},
            {"email": user_credentials.username_or_email}
        ]
    })
    
    # If not found in users, try to find in lawyers collection for lawyer login
    if not user_doc:
        lawyer_doc = await db.lawyers.find_one({"email": user_credentials.username_or_email})
        if lawyer_doc:
            # Verify password is the OAB number
            if user_credentials.password == lawyer_doc['oab_number']:
                # Create temporary user object for lawyer
                user_dict = {
                    "id": lawyer_doc['id'],
                    "username": lawyer_doc['email'],
                    "email": lawyer_doc['email'],
                    "full_name": lawyer_doc['full_name'],
                    "role": "lawyer",
                    "branch_id": lawyer_doc['branch_id'],
                    "is_active": lawyer_doc['is_active'],
                    "created_at": lawyer_doc['created_at']
                }
                
                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(
                    data={"sub": lawyer_doc['email']}, expires_delta=access_token_expires
                )
                
                user = User(**user_dict)
                return Token(access_token=access_token, token_type="bearer", user=user)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Para advogados, use seu email e os números da sua OAB como senha",
                )
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )
    
    user_in_db = UserInDB(**user_doc)
    if not verify_password(user_credentials.password, user_in_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha incorreta",
        )
    
    if not user_in_db.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    
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

# Branch endpoints
@api_router.post("/branches", response_model=Branch)
async def create_branch(branch: BranchCreate, current_user: User = Depends(get_current_user)):
    # Only admin can create branches
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create branches"
        )
    
    # Check if CNPJ already exists
    existing_branch = await db.branches.find_one({"cnpj": branch.cnpj})
    if existing_branch:
        raise HTTPException(status_code=400, detail="Branch with this CNPJ already exists")
    
    branch_dict = branch.dict()
    branch_obj = Branch(**branch_dict)
    await db.branches.insert_one(branch_obj.dict())
    return branch_obj

@api_router.get("/branches", response_model=List[Branch])
async def get_branches(current_user: User = Depends(get_current_user)):
    # Super admin can see all branches, regular admin/lawyer can only see their own
    if current_user.role == UserRole.admin and not current_user.branch_id:
        # Super admin without branch_id can see all
        branches = await db.branches.find({"is_active": True}).to_list(1000)
    elif current_user.branch_id:
        # User with branch_id can only see their branch
        branches = await db.branches.find({
            "id": current_user.branch_id, 
            "is_active": True
        }).to_list(1000)
    else:
        # Default: see all active branches
        branches = await db.branches.find({"is_active": True}).to_list(1000)
    
    return [Branch(**branch) for branch in branches]

@api_router.get("/branches/{branch_id}", response_model=Branch)
async def get_branch(branch_id: str, current_user: User = Depends(get_current_user)):
    branch = await db.branches.find_one({"id": branch_id})
    if branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")
    return Branch(**branch)

@api_router.put("/branches/{branch_id}", response_model=Branch)
async def update_branch(
    branch_id: str, 
    branch: BranchCreate, 
    current_user: User = Depends(get_current_user)
):
    # Only admin can update branches
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update branches"
        )
    
    existing_branch = await db.branches.find_one({"id": branch_id})
    if existing_branch is None:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    # Check if CNPJ conflicts with other branches
    cnpj_conflict = await db.branches.find_one({
        "cnpj": branch.cnpj,
        "id": {"$ne": branch_id}
    })
    if cnpj_conflict:
        raise HTTPException(status_code=400, detail="Another branch with this CNPJ already exists")
    
    update_data = branch.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.branches.update_one({"id": branch_id}, {"$set": update_data})
    updated_branch = await db.branches.find_one({"id": branch_id})
    return Branch(**updated_branch)

# Client endpoints
@api_router.post("/clients", response_model=Client)
async def create_client(client: ClientCreate):
    client_dict = client.dict()
    client_obj = Client(**client_dict)
    await db.clients.insert_one(client_obj.dict())
    return client_obj

@api_router.get("/clients", response_model=List[Client])
async def get_clients(current_user: User = Depends(get_current_user)):
    # Apply branch filter based on user's branch_id
    query = {}
    if current_user.branch_id:
        # User is restricted to their branch
        query["branch_id"] = current_user.branch_id
    elif current_user.role != UserRole.admin or current_user.branch_id is not None:
        # Non-admin users or branch-restricted admins can only see their branch data
        return []
    # Super admin (role=admin, branch_id=None) can see all clients
    
    clients = await db.clients.find(query).to_list(1000)
    return [Client(**client) for client in clients]

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str):
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return Client(**client)

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str):
    # Check if client exists
    client = await db.clients.find_one({"id": client_id})
    if client is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Check for dependencies
    dependencies = []
    
    # Check for processes
    processes_count = await db.processes.count_documents({"client_id": client_id})
    if processes_count > 0:
        dependencies.append(f"{processes_count} processo(s)")
    
    # Check for contracts
    contracts_count = await db.contracts.count_documents({"client_id": client_id})
    if contracts_count > 0:
        dependencies.append(f"{contracts_count} contrato(s)")
    
    # Check for financial transactions
    financial_count = await db.financial_transactions.count_documents({"client_id": client_id})
    if financial_count > 0:
        dependencies.append(f"{financial_count} transação(ões) financeira(s)")
    
    if dependencies:
        dependency_text = ", ".join(dependencies)
        raise HTTPException(
            status_code=400, 
            detail=f"Não é possível excluir este cliente pois ele possui: {dependency_text}. Remova essas dependências primeiro."
        )
    
    # If no dependencies, delete the client
    result = await db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    return {"message": "Cliente excluído com sucesso"}

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
async def get_processes(current_user: User = Depends(get_current_user)):
    # Apply branch filter
    query = {}
    if current_user.branch_id:
        query["branch_id"] = current_user.branch_id
    elif current_user.role != UserRole.admin or current_user.branch_id is not None:
        return []
    
    processes = await db.processes.find(query).to_list(1000)
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
    # Check if process exists
    process = await db.processes.find_one({"id": process_id})
    if process is None:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    
    # Check for dependencies (financial transactions)
    financial_count = await db.financial_transactions.count_documents({"process_id": process_id})
    if financial_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível excluir este processo pois ele possui {financial_count} transação(ões) financeira(s) vinculada(s). Remova essas transações primeiro."
        )
    
    # If no dependencies, delete the process
    result = await db.processes.delete_one({"id": process_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    
    return {"message": "Processo excluído com sucesso"}

# Financial Transaction endpoints
@api_router.post("/financial", response_model=FinancialTransaction)
async def create_financial_transaction(transaction: FinancialTransactionCreate):
    transaction_dict = transaction.dict()
    transaction_obj = FinancialTransaction(**transaction_dict)
    await db.financial_transactions.insert_one(transaction_obj.dict())
    return transaction_obj

@api_router.get("/financial", response_model=List[FinancialTransaction])
async def get_financial_transactions(current_user: User = Depends(get_current_user)):
    # Apply branch filter
    query = {}
    if current_user.branch_id:
        query["branch_id"] = current_user.branch_id
    elif current_user.role != UserRole.admin or current_user.branch_id is not None:
        return []
    
    transactions = await db.financial_transactions.find(query).to_list(1000)
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
    # Check if transaction exists
    transaction = await db.financial_transactions.find_one({"id": transaction_id})
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transação financeira não encontrada")
    
    # Check if transaction is already paid
    if transaction.get("status") == "pago":
        raise HTTPException(
            status_code=400,
            detail="Não é possível excluir uma transação que já foi paga. Para reverter, altere o status primeiro."
        )
    
    # If no restrictions, delete the transaction
    result = await db.financial_transactions.delete_one({"id": transaction_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transação financeira não encontrada")
    
    return {"message": "Transação financeira excluída com sucesso"}

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
async def get_contracts(current_user: User = Depends(get_current_user)):
    # Apply branch filter
    query = {}
    if current_user.branch_id:
        query["branch_id"] = current_user.branch_id
    elif current_user.role != UserRole.admin or current_user.branch_id is not None:
        return []
    
    contracts = await db.contracts.find(query).to_list(1000)
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

# Lawyer endpoints (Admin only)
@api_router.post("/lawyers", response_model=Lawyer)
async def create_lawyer(lawyer: LawyerCreate, current_user: User = Depends(get_current_user)):
    # Only admin can create lawyers
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can register lawyers"
        )
    
    # Check if OAB number already exists
    existing_lawyer = await db.lawyers.find_one({
        "oab_number": lawyer.oab_number, 
        "oab_state": lawyer.oab_state
    })
    if existing_lawyer:
        raise HTTPException(
            status_code=400, 
            detail=f"Lawyer with OAB {lawyer.oab_number}/{lawyer.oab_state} already exists"
        )
    
    # Check if email already exists
    existing_email = await db.lawyers.find_one({"email": lawyer.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    lawyer_dict = lawyer.dict()
    lawyer_obj = Lawyer(**lawyer_dict)
    await db.lawyers.insert_one(lawyer_obj.dict())
    return lawyer_obj

@api_router.get("/lawyers", response_model=List[Lawyer])
async def get_lawyers(current_user: User = Depends(get_current_user)):
    # Apply branch filter
    query = {"is_active": True}
    if current_user.branch_id:
        query["branch_id"] = current_user.branch_id
    elif current_user.role != UserRole.admin or current_user.branch_id is not None:
        return []
    
    lawyers = await db.lawyers.find(query).to_list(1000)
    return [Lawyer(**lawyer) for lawyer in lawyers]

@api_router.get("/lawyers/{lawyer_id}", response_model=Lawyer)
async def get_lawyer(lawyer_id: str, current_user: User = Depends(get_current_user)):
    lawyer = await db.lawyers.find_one({"id": lawyer_id})
    if lawyer is None:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    return Lawyer(**lawyer)

@api_router.put("/lawyers/{lawyer_id}", response_model=Lawyer)
async def update_lawyer(
    lawyer_id: str, 
    lawyer: LawyerCreate, 
    current_user: User = Depends(get_current_user)
):
    # Only admin can update lawyers
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update lawyers"
        )
    
    existing_lawyer = await db.lawyers.find_one({"id": lawyer_id})
    if existing_lawyer is None:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    
    # Check if OAB number conflicts with other lawyers (excluding current one)
    oab_conflict = await db.lawyers.find_one({
        "oab_number": lawyer.oab_number,
        "oab_state": lawyer.oab_state,
        "id": {"$ne": lawyer_id}
    })
    if oab_conflict:
        raise HTTPException(
            status_code=400, 
            detail=f"Another lawyer with OAB {lawyer.oab_number}/{lawyer.oab_state} already exists"
        )
    
    # Check if email conflicts with other lawyers (excluding current one)
    email_conflict = await db.lawyers.find_one({
        "email": lawyer.email,
        "id": {"$ne": lawyer_id}
    })
    if email_conflict:
        raise HTTPException(status_code=400, detail="Email already registered by another lawyer")
    
    update_data = lawyer.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    await db.lawyers.update_one({"id": lawyer_id}, {"$set": update_data})
    updated_lawyer = await db.lawyers.find_one({"id": lawyer_id})
    return Lawyer(**updated_lawyer)

@api_router.delete("/lawyers/{lawyer_id}")
async def deactivate_lawyer(lawyer_id: str, current_user: User = Depends(get_current_user)):
    # Only admin can deactivate lawyers
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can deactivate lawyers"
        )
    
    lawyer = await db.lawyers.find_one({"id": lawyer_id})
    if lawyer is None:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    
    # Soft delete - just set is_active to False
    await db.lawyers.update_one(
        {"id": lawyer_id}, 
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": "Lawyer deactivated successfully"}

# Dashboard endpoint
@api_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    # Apply branch filter
    branch_filter = {}
    if current_user.branch_id:
        branch_filter["branch_id"] = current_user.branch_id
    elif current_user.role != UserRole.admin or current_user.branch_id is not None:
        # Non-admin or branch-restricted users get empty stats
        return DashboardStats(
            total_clients=0, total_processes=0, total_revenue=0, total_expenses=0,
            pending_payments=0, overdue_payments=0, monthly_revenue=0, monthly_expenses=0
        )
    
    # Count totals with branch filter
    total_clients = await db.clients.count_documents(branch_filter)
    total_processes = await db.processes.count_documents(branch_filter)
    
    # Calculate financial totals with branch filter
    revenue_pipeline = [
        {"$match": {**branch_filter, "type": "receita"}},
        {"$group": {"_id": None, "total": {"$sum": "$value"}}}
    ]
    revenue_result = await db.financial_transactions.aggregate(revenue_pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0
    
    expenses_pipeline = [
        {"$match": {**branch_filter, "type": "despesa"}},
        {"$group": {"_id": None, "total": {"$sum": "$value"}}}
    ]
    expenses_result = await db.financial_transactions.aggregate(expenses_pipeline).to_list(1)
    total_expenses = expenses_result[0]["total"] if expenses_result else 0
    
    # Count pending and overdue payments with branch filter
    pending_payments = await db.financial_transactions.count_documents({**branch_filter, "status": "pendente"})
    overdue_payments = await db.financial_transactions.count_documents({**branch_filter, "status": "vencido"})
    
    # Calculate monthly revenue and expenses (current month) with branch filter
    from datetime import datetime, timedelta
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month_start = current_month_start + timedelta(days=32)
    next_month_start = next_month_start.replace(day=1)
    
    monthly_revenue_pipeline = [
        {"$match": {
            **branch_filter,
            "type": "receita",
            "due_date": {"$gte": current_month_start, "$lt": next_month_start}
        }},
        {"$group": {"_id": None, "total": {"$sum": "$value"}}}
    ]
    monthly_revenue_result = await db.financial_transactions.aggregate(monthly_revenue_pipeline).to_list(1)
    monthly_revenue = monthly_revenue_result[0]["total"] if monthly_revenue_result else 0
    
    monthly_expenses_pipeline = [
        {"$match": {
            **branch_filter,
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

# WhatsApp API Routes
@api_router.post("/whatsapp/send-reminder/{transaction_id}")
async def send_manual_reminder(transaction_id: str, current_user: User = Depends(get_current_user)):
    """
    Envia lembrete manual de pagamento via WhatsApp
    """
    if current_user.role not in ['admin', 'lawyer']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    result = await payment_reminder_service.send_manual_reminder(transaction_id)
    
    if result["success"]:
        return {"message": "Lembrete enviado com sucesso", "data": result}
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Erro ao enviar lembrete"))

@api_router.post("/whatsapp/check-payments")
async def trigger_payment_check(current_user: User = Depends(get_current_user)):
    """
    Dispara verificação manual de pagamentos pendentes
    """
    if current_user.role not in ['admin']:
        raise HTTPException(status_code=403, detail="Apenas administradores podem disparar verificações")
    
    try:
        await payment_reminder_service.check_and_send_reminders()
        return {"message": "Verificação de pagamentos executada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na verificação: {str(e)}")

@api_router.get("/whatsapp/status")
async def get_whatsapp_status(current_user: User = Depends(get_current_user)):
    """
    Retorna status do serviço WhatsApp e jobs agendados
    """
    if current_user.role not in ['admin', 'lawyer']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    jobs = payment_scheduler.get_jobs_status()
    
    return {
        "whatsapp_enabled": whatsapp_service.is_enabled,
        "scheduler_running": payment_scheduler.scheduler.running,
        "jobs": jobs,
        "next_check": jobs[0]["next_run"] if jobs else None
    }

@api_router.post("/whatsapp/send-message")
async def send_whatsapp_message(
    message_data: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Envia mensagem personalizada via WhatsApp
    """
    if current_user.role not in ['admin', 'lawyer']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    phone_number = message_data.get("phone_number")
    message = message_data.get("message")
    
    if not phone_number or not message:
        raise HTTPException(status_code=400, detail="phone_number e message são obrigatórios")
    
    result = await whatsapp_service.send_message(phone_number, message)
    
    if result["success"]:
        return {"message": "Mensagem enviada com sucesso", "data": result}
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Erro ao enviar mensagem"))

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

@app.on_event("startup")
async def startup_event():
    # Create default branches if they don't exist
    existing_branches = await db.branches.count_documents({})
    if existing_branches == 0:
        # Create default branches
        filial_caxias = Branch(
            name="GB Advocacia & N. Comin - Caxias do Sul",
            cnpj="12.345.678/0001-90",
            address="Rua Os Dezoito do Forte, 1234 - Centro, Caxias do Sul - RS",
            phone="(54) 3456-7890",
            email="caxias@gbadvocacia.com",
            responsible="Dr. Gustavo Batista"
        )
        
        filial_nova_prata = Branch(
            name="GB Advocacia & N. Comin - Nova Prata",
            cnpj="12.345.678/0002-01",
            address="Rua General Osório, 567 - Centro, Nova Prata - RS",
            phone="(54) 3242-1234",
            email="novaprata@gbadvocacia.com",
            responsible="Dra. Natália Comin"
        )
        
        await db.branches.insert_one(filial_caxias.dict())
        await db.branches.insert_one(filial_nova_prata.dict())
        
        logger.info("Default branches created: Caxias do Sul and Nova Prata")
        
        # Create admin users for each branch
        admin_caxias = UserInDB(
            username="admin_caxias",
            email="admin.caxias@gbadvocacia.com",
            full_name="Administrador Caxias do Sul",
            role=UserRole.admin,
            branch_id=filial_caxias.id,
            hashed_password=get_password_hash("admin123"),
            is_active=True
        )
        
        admin_nova_prata = UserInDB(
            username="admin_novaprata",
            email="admin.novaprata@gbadvocacia.com",
            full_name="Administrador Nova Prata",
            role=UserRole.admin,
            branch_id=filial_nova_prata.id,
            hashed_password=get_password_hash("admin123"),
            is_active=True
        )
        
        await db.users.insert_one(admin_caxias.dict())
        await db.users.insert_one(admin_nova_prata.dict())
        
        logger.info("Branch administrators created:")
        logger.info("Caxias Admin: username=admin_caxias, password=admin123")
        logger.info("Nova Prata Admin: username=admin_novaprata, password=admin123")
    
    # Create super admin (without branch) if it doesn't exist
    existing_super_admin = await db.users.find_one({"username": "admin", "branch_id": None})
    if not existing_super_admin:
        super_admin_user = UserInDB(
            username="admin",
            email="admin@gbadvocacia.com",
            full_name="Super Administrador GB Advocacia",
            role=UserRole.admin,
            branch_id=None,  # Super admin has no branch restriction
            hashed_password=get_password_hash("admin123"),
            is_active=True
        )
        await db.users.insert_one(super_admin_user.dict())
        logger.info("Super admin user created: username=admin, password=admin123")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()