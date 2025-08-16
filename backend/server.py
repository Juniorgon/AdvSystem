from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
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
import json
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_

# Import database models and connection
from database import (
    get_db, create_tables, drop_tables, SessionLocal,
    User as DBUser, Client as DBClient, Process as DBProcess, 
    FinancialTransaction as DBFinancialTransaction, Contract as DBContract,
    Lawyer as DBLawyer, Branch as DBBranch, Task as DBTask,
    ContractNumberSequence as DBContractNumberSequence,
    UserRole, ClientType, ProcessRole, TransactionType, TransactionStatus
)

# Import Google Drive service
from google_drive_service import google_drive_service

# Import Enhanced Security Module
from security import (
    security_manager, SecurityHeaders, PasswordValidator, 
    validate_input_security, hash_password, verify_password,
    SecurityEvent
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create the main app without a prefix
app = FastAPI(
    title="Law Firm Management System",
    description="Sistema de Gestão de Escritório de Advocacia com Segurança Avançada",
    version="2.0.0"
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enhanced Security Middleware
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Enhanced security middleware"""
    client_ip = request.client.host if request.client else "unknown"
    
    # Validate request security
    if not security_manager.validate_request(request):
        return Response(
            content="Rate limit exceeded",
            status_code=429,
            headers=SecurityHeaders.get_security_headers()
        )
    
    # Process request
    response = await call_next(request)
    
    # Add security headers to all responses
    for header, value in SecurityHeaders.get_security_headers().items():
        response.headers[header] = value
    
    # Log security event for sensitive endpoints
    if request.url.path.startswith("/api/auth") or request.url.path.startswith("/api/admin"):
        security_manager.log_security_event(SecurityEvent(
            event_type="SENSITIVE_ENDPOINT_ACCESS",
            ip_address=client_ip,
            user_agent=request.headers.get("User-Agent", "Unknown"),
            timestamp=datetime.utcnow(),
            details={
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": response.status_code
            }
        ))
    
    return response

# Authentication configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'gb_advocacia_secret_key_2025')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

# Pydantic Models
class Address(BaseModel):
    street: str
    number: str
    city: str
    district: str
    state: str
    complement: Optional[str] = ""

class User(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    role: UserRole
    branch_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str
    password: str
    role: UserRole
    branch_id: Optional[str] = None

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class Branch(BaseModel):
    id: str
    name: str
    cnpj: str
    address: str
    phone: str
    email: str
    responsible: str
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class BranchCreate(BaseModel):
    name: str
    cnpj: str
    address: str
    phone: str
    email: str
    responsible: str

class Client(BaseModel):
    id: str
    name: str
    nationality: str
    civil_status: str
    profession: str
    cpf: str
    street: str
    number: str
    city: str
    district: str
    state: str
    complement: Optional[str] = ""
    phone: str
    client_type: ClientType
    branch_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ClientCreate(BaseModel):
    name: str
    nationality: str
    civil_status: str
    profession: str
    cpf: str
    address: Address
    phone: str
    client_type: ClientType
    branch_id: str

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    nationality: Optional[str] = None
    civil_status: Optional[str] = None
    profession: Optional[str] = None
    cpf: Optional[str] = None
    address: Optional[Address] = None
    phone: Optional[str] = None
    client_type: Optional[ClientType] = None

class Lawyer(BaseModel):
    id: str
    full_name: str
    oab_number: str
    oab_state: str
    email: str
    phone: str
    specialization: Optional[str] = ""
    branch_id: str
    access_financial_data: bool = True
    allowed_branch_ids: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class LawyerCreate(BaseModel):
    full_name: str
    oab_number: str
    oab_state: str
    email: str
    phone: str
    specialization: Optional[str] = ""
    branch_id: str
    access_financial_data: bool = True
    allowed_branch_ids: Optional[List[str]] = None

class LawyerUpdate(BaseModel):
    full_name: Optional[str] = None
    oab_number: Optional[str] = None
    oab_state: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    access_financial_data: Optional[bool] = None
    allowed_branch_ids: Optional[List[str]] = None

class Process(BaseModel):
    id: str
    client_id: str
    process_number: str
    type: str
    status: str
    value: float
    description: str
    role: ProcessRole
    branch_id: str
    responsible_lawyer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ProcessCreate(BaseModel):
    client_id: str
    process_number: str
    type: str
    status: str
    value: float
    description: str
    role: ProcessRole
    branch_id: str
    responsible_lawyer_id: Optional[str] = None

class ProcessUpdate(BaseModel):
    process_number: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    value: Optional[float] = None
    description: Optional[str] = None
    role: Optional[ProcessRole] = None
    responsible_lawyer_id: Optional[str] = None

class FinancialTransaction(BaseModel):
    id: str
    client_id: Optional[str] = None
    process_id: Optional[str] = None
    type: TransactionType
    description: str
    value: float
    due_date: datetime
    payment_date: Optional[datetime] = None
    status: TransactionStatus
    category: str
    branch_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

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
    branch_id: str

class FinancialTransactionUpdate(BaseModel):
    description: Optional[str] = None
    value: Optional[float] = None
    due_date: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    status: Optional[TransactionStatus] = None
    category: Optional[str] = None

class Contract(BaseModel):
    id: str
    contract_number: str
    client_id: str
    process_id: Optional[str] = None
    value: float
    payment_conditions: str
    installments: int
    branch_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ContractCreate(BaseModel):
    client_id: str
    process_id: Optional[str] = None
    value: float
    payment_conditions: str
    installments: int
    branch_id: str

class Task(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    due_date: datetime
    priority: str = "medium"
    status: str = "pending"
    assigned_lawyer_id: str
    client_id: Optional[str] = None
    process_id: Optional[str] = None
    branch_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: datetime
    priority: str = "medium"
    status: str = "pending"
    assigned_lawyer_id: str
    client_id: Optional[str] = None
    process_id: Optional[str] = None
    branch_id: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_lawyer_id: Optional[str] = None
    client_id: Optional[str] = None
    process_id: Optional[str] = None

class GoogleDriveAuthRequest(BaseModel):
    authorization_code: str

class ProcuracaoRequest(BaseModel):
    client_id: str
    process_id: Optional[str] = None
    
class DocumentInfo(BaseModel):
    id: str
    name: str
    created_time: str
    web_view_link: str
    mime_type: str

class DashboardStats(BaseModel):
    total_clients: int
    total_processes: int
    total_revenue: float
    total_expenses: float
    pending_payments: int
    overdue_payments: int
    monthly_revenue: float
    monthly_expenses: float

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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
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
    
    # Try to find user
    user_db = db.query(DBUser).filter(
        or_(DBUser.username == username_or_email, DBUser.email == username_or_email)
    ).first()
    
    if user_db:
        return User.from_orm(user_db)
    
    # Try to find in lawyers (for lawyer authentication)
    lawyer_db = db.query(DBLawyer).filter(DBLawyer.email == username_or_email).first()
    if lawyer_db:
        # Create user object from lawyer data
        user_dict = {
            "id": lawyer_db.id,
            "username": lawyer_db.email,
            "email": lawyer_db.email,
            "full_name": lawyer_db.full_name,
            "role": UserRole.lawyer,
            "branch_id": lawyer_db.branch_id,
            "is_active": lawyer_db.is_active,
            "created_at": lawyer_db.created_at
        }
        return User(**user_dict)
    
    raise credentials_exception

def get_next_contract_number(branch_id: str, db: Session) -> str:
    current_year = datetime.now().year
    
    # Get or create sequence for this branch and year
    sequence = db.query(DBContractNumberSequence).filter(
        DBContractNumberSequence.branch_id == branch_id,
        DBContractNumberSequence.year == current_year
    ).first()
    
    if not sequence:
        sequence = DBContractNumberSequence(
            branch_id=branch_id,
            year=current_year,
            last_number=0
        )
        db.add(sequence)
        db.flush()
    
    sequence.last_number += 1
    db.commit()
    
    return f"CONT-{current_year}-{sequence.last_number:04d}"

def check_financial_access(current_user: User, db: Session) -> bool:
    """Check if user has access to financial data"""
    if current_user.role == UserRole.admin:
        return True
    
    if current_user.role == UserRole.lawyer:
        lawyer = db.query(DBLawyer).filter(DBLawyer.email == current_user.email).first()
        if lawyer:
            return lawyer.access_financial_data
    
    return False

def get_accessible_branches(current_user: User, db: Session) -> List[str]:
    """Get list of branch IDs the user has access to"""
    if current_user.role == UserRole.admin and not current_user.branch_id:
        # Super admin has access to all branches
        return []  # Empty list means all branches
    
    if current_user.role == UserRole.lawyer:
        lawyer = db.query(DBLawyer).filter(DBLawyer.email == current_user.email).first()
        if lawyer and lawyer.allowed_branch_ids:
            try:
                return json.loads(lawyer.allowed_branch_ids)
            except:
                pass
    
    # Default: only own branch
    return [current_user.branch_id] if current_user.branch_id else []

# Authentication endpoints
@api_router.post("/auth/register", response_model=User)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(DBUser).filter(DBUser.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    existing_email = db.query(DBUser).filter(DBUser.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    
    user_db = DBUser(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hashed_password,
        role=user.role,
        branch_id=user.branch_id
    )
    
    db.add(user_db)
    db.commit()
    db.refresh(user_db)
    
    return User.from_orm(user_db)

@api_router.post("/auth/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    # Try to find user by username or email
    user_db = db.query(DBUser).filter(
        or_(DBUser.username == user_credentials.username_or_email, 
            DBUser.email == user_credentials.username_or_email)
    ).first()
    
    # If not found in users, try lawyers
    if not user_db:
        lawyer_db = db.query(DBLawyer).filter(DBLawyer.email == user_credentials.username_or_email).first()
        if lawyer_db:
            # Verify password is the OAB number
            if user_credentials.password == lawyer_db.oab_number:
                user_dict = {
                    "id": lawyer_db.id,
                    "username": lawyer_db.email,
                    "email": lawyer_db.email,
                    "full_name": lawyer_db.full_name,
                    "role": UserRole.lawyer,
                    "branch_id": lawyer_db.branch_id,
                    "is_active": lawyer_db.is_active,
                    "created_at": lawyer_db.created_at
                }
                
                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(
                    data={"sub": lawyer_db.email}, expires_delta=access_token_expires
                )
                
                user = User(**user_dict)
                return Token(access_token=access_token, token_type="bearer", user=user)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Para advogados, use seu email e os números da sua OAB como senha",
                )
    
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )
    
    if not verify_password(user_credentials.password, user_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha incorreta",
        )
    
    if not user_db.is_active:
        raise HTTPException(status_code=400, detail="Usuário inativo")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_db.username}, expires_delta=access_token_expires
    )
    
    user = User.from_orm(user_db)
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# Branch endpoints
@api_router.post("/branches", response_model=Branch)
async def create_branch(branch: BranchCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create branches"
        )
    
    # Check if CNPJ already exists
    existing_branch = db.query(DBBranch).filter(DBBranch.cnpj == branch.cnpj).first()
    if existing_branch:
        raise HTTPException(status_code=400, detail="Branch with this CNPJ already exists")
    
    branch_db = DBBranch(**branch.dict())
    db.add(branch_db)
    db.commit()
    db.refresh(branch_db)
    
    return Branch.from_orm(branch_db)

@api_router.get("/branches", response_model=List[Branch])
async def get_branches(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accessible_branches = get_accessible_branches(current_user, db)
    
    query = db.query(DBBranch).filter(DBBranch.is_active == True)
    
    if accessible_branches:  # If not empty, filter by accessible branches
        query = query.filter(DBBranch.id.in_(accessible_branches))
    
    branches = query.all()
    return [Branch.from_orm(branch) for branch in branches]

# Client endpoints
@api_router.post("/clients", response_model=Client)
async def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    client_data = client.dict()
    # Extract address
    address = client_data.pop('address')
    client_data.update(address)
    
    client_db = DBClient(**client_data)
    db.add(client_db)
    db.commit()
    db.refresh(client_db)
    
    return Client.from_orm(client_db)

@api_router.get("/clients", response_model=List[Client])
async def get_clients(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accessible_branches = get_accessible_branches(current_user, db)
    
    query = db.query(DBClient)
    
    if accessible_branches:
        query = query.filter(DBClient.branch_id.in_(accessible_branches))
    
    clients = query.all()
    return [Client.from_orm(client) for client in clients]

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str, db: Session = Depends(get_db)):
    client = db.query(DBClient).filter(DBClient.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return Client.from_orm(client)

@api_router.put("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, client_update: ClientUpdate, db: Session = Depends(get_db)):
    client_db = db.query(DBClient).filter(DBClient.id == client_id).first()
    if not client_db:
        raise HTTPException(status_code=404, detail="Client not found")
    
    update_data = client_update.dict(exclude_unset=True)
    if 'address' in update_data:
        address = update_data.pop('address')
        update_data.update(address)
    
    for field, value in update_data.items():
        setattr(client_db, field, value)
    
    client_db.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client_db)
    
    return Client.from_orm(client_db)

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str, db: Session = Depends(get_db)):
    client = db.query(DBClient).filter(DBClient.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Check dependencies
    dependencies = []
    
    processes_count = db.query(DBProcess).filter(DBProcess.client_id == client_id).count()
    if processes_count > 0:
        dependencies.append(f"{processes_count} processo(s)")
    
    contracts_count = db.query(DBContract).filter(DBContract.client_id == client_id).count()
    if contracts_count > 0:
        dependencies.append(f"{contracts_count} contrato(s)")
    
    financial_count = db.query(DBFinancialTransaction).filter(DBFinancialTransaction.client_id == client_id).count()
    if financial_count > 0:
        dependencies.append(f"{financial_count} transação(ões) financeira(s)")
    
    if dependencies:
        dependency_text = ", ".join(dependencies)
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível excluir este cliente pois ele possui: {dependency_text}. Remova essas dependências primeiro."
        )
    
    db.delete(client)
    db.commit()
    
    return {"message": "Cliente excluído com sucesso"}

# Lawyer endpoints
@api_router.post("/lawyers", response_model=Lawyer)
async def create_lawyer(lawyer: LawyerCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can register lawyers"
        )
    
    # Check if OAB number already exists
    existing_lawyer = db.query(DBLawyer).filter(
        DBLawyer.oab_number == lawyer.oab_number,
        DBLawyer.oab_state == lawyer.oab_state
    ).first()
    if existing_lawyer:
        raise HTTPException(
            status_code=400,
            detail=f"Lawyer with OAB {lawyer.oab_number}/{lawyer.oab_state} already exists"
        )
    
    # Check if email already exists
    existing_email = db.query(DBLawyer).filter(DBLawyer.email == lawyer.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    lawyer_data = lawyer.dict()
    if lawyer.allowed_branch_ids:
        lawyer_data['allowed_branch_ids'] = json.dumps(lawyer.allowed_branch_ids)
    
    lawyer_db = DBLawyer(**lawyer_data)
    db.add(lawyer_db)
    db.commit()
    db.refresh(lawyer_db)
    
    return Lawyer.from_orm(lawyer_db)

@api_router.get("/lawyers", response_model=List[Lawyer])
async def get_lawyers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accessible_branches = get_accessible_branches(current_user, db)
    
    query = db.query(DBLawyer).filter(DBLawyer.is_active == True)
    
    if accessible_branches:
        query = query.filter(DBLawyer.branch_id.in_(accessible_branches))
    
    lawyers = query.all()
    return [Lawyer.from_orm(lawyer) for lawyer in lawyers]

@api_router.put("/lawyers/{lawyer_id}", response_model=Lawyer)
async def update_lawyer(
    lawyer_id: str,
    lawyer: LawyerUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update lawyers"
        )
    
    lawyer_db = db.query(DBLawyer).filter(DBLawyer.id == lawyer_id).first()
    if not lawyer_db:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    
    update_data = lawyer.dict(exclude_unset=True)
    if 'allowed_branch_ids' in update_data and update_data['allowed_branch_ids']:
        update_data['allowed_branch_ids'] = json.dumps(update_data['allowed_branch_ids'])
    
    for field, value in update_data.items():
        setattr(lawyer_db, field, value)
    
    lawyer_db.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lawyer_db)
    
    return Lawyer.from_orm(lawyer_db)

@api_router.delete("/lawyers/{lawyer_id}")
async def deactivate_lawyer(lawyer_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can deactivate lawyers"
        )
    
    lawyer = db.query(DBLawyer).filter(DBLawyer.id == lawyer_id).first()
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    
    lawyer.is_active = False
    lawyer.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Lawyer deactivated successfully"}

# Process endpoints
@api_router.post("/processes", response_model=Process)
async def create_process(process: ProcessCreate, db: Session = Depends(get_db)):
    # Verify client exists
    client = db.query(DBClient).filter(DBClient.id == process.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Verify lawyer exists if assigned
    if process.responsible_lawyer_id:
        lawyer = db.query(DBLawyer).filter(DBLawyer.id == process.responsible_lawyer_id).first()
        if not lawyer:
            raise HTTPException(status_code=404, detail="Lawyer not found")
    
    process_db = DBProcess(**process.dict())
    db.add(process_db)
    db.commit()
    db.refresh(process_db)
    
    return Process.from_orm(process_db)

@api_router.get("/processes", response_model=List[Process])
async def get_processes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accessible_branches = get_accessible_branches(current_user, db)
    
    query = db.query(DBProcess)
    
    # Branch filtering
    if accessible_branches:
        query = query.filter(DBProcess.branch_id.in_(accessible_branches))
    
    # Lawyer-specific filtering: lawyers can only see their assigned processes (unless admin)
    if current_user.role == UserRole.lawyer:
        lawyer = db.query(DBLawyer).filter(DBLawyer.email == current_user.email).first()
        if lawyer:
            query = query.filter(DBProcess.responsible_lawyer_id == lawyer.id)
    
    processes = query.all()
    return [Process.from_orm(process) for process in processes]

@api_router.get("/processes/{process_id}", response_model=Process)
async def get_process(process_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    process = db.query(DBProcess).filter(DBProcess.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    
    # Check access for lawyers
    if current_user.role == UserRole.lawyer:
        lawyer = db.query(DBLawyer).filter(DBLawyer.email == current_user.email).first()
        if lawyer and process.responsible_lawyer_id != lawyer.id:
            raise HTTPException(status_code=403, detail="Access denied to this process")
    
    return Process.from_orm(process)

@api_router.put("/processes/{process_id}", response_model=Process)
async def update_process(process_id: str, process_update: ProcessUpdate, db: Session = Depends(get_db)):
    process_db = db.query(DBProcess).filter(DBProcess.id == process_id).first()
    if not process_db:
        raise HTTPException(status_code=404, detail="Process not found")
    
    update_data = process_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(process_db, field, value)
    
    process_db.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(process_db)
    
    return Process.from_orm(process_db)

@api_router.delete("/processes/{process_id}")
async def delete_process(process_id: str, db: Session = Depends(get_db)):
    process = db.query(DBProcess).filter(DBProcess.id == process_id).first()
    if not process:
        raise HTTPException(status_code=404, detail="Processo não encontrado")
    
    # Check dependencies
    financial_count = db.query(DBFinancialTransaction).filter(DBFinancialTransaction.process_id == process_id).count()
    if financial_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Não é possível excluir este processo pois ele possui {financial_count} transação(ões) financeira(s) vinculada(s)."
        )
    
    db.delete(process)
    db.commit()
    
    return {"message": "Processo excluído com sucesso"}

# Financial endpoints
@api_router.post("/financial", response_model=FinancialTransaction)
async def create_financial_transaction(transaction: FinancialTransactionCreate, db: Session = Depends(get_db)):
    transaction_db = DBFinancialTransaction(**transaction.dict())
    db.add(transaction_db)
    db.commit()
    db.refresh(transaction_db)
    
    return FinancialTransaction.from_orm(transaction_db)

@api_router.get("/financial", response_model=List[FinancialTransaction])
async def get_financial_transactions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check financial access
    if not check_financial_access(current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado aos dados financeiros"
        )
    
    accessible_branches = get_accessible_branches(current_user, db)
    
    query = db.query(DBFinancialTransaction)
    
    if accessible_branches:
        query = query.filter(DBFinancialTransaction.branch_id.in_(accessible_branches))
    
    transactions = query.all()
    return [FinancialTransaction.from_orm(transaction) for transaction in transactions]

@api_router.put("/financial/{transaction_id}", response_model=FinancialTransaction)
async def update_financial_transaction(
    transaction_id: str, 
    transaction_update: FinancialTransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not check_financial_access(current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado aos dados financeiros"
        )
    
    transaction_db = db.query(DBFinancialTransaction).filter(DBFinancialTransaction.id == transaction_id).first()
    if not transaction_db:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    update_data = transaction_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(transaction_db, field, value)
    
    transaction_db.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(transaction_db)
    
    return FinancialTransaction.from_orm(transaction_db)

@api_router.delete("/financial/{transaction_id}")
async def delete_financial_transaction(transaction_id: str, db: Session = Depends(get_db)):
    transaction = db.query(DBFinancialTransaction).filter(DBFinancialTransaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transação financeira não encontrada")
    
    if transaction.status == TransactionStatus.pago:
        raise HTTPException(
            status_code=400,
            detail="Não é possível excluir uma transação que já foi paga."
        )
    
    db.delete(transaction)
    db.commit()
    
    return {"message": "Transação financeira excluída com sucesso"}

# Contract endpoints
@api_router.post("/contracts", response_model=Contract)
async def create_contract(contract: ContractCreate, db: Session = Depends(get_db)):
    # Verify client exists
    client = db.query(DBClient).filter(DBClient.id == contract.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Generate contract number
    contract_number = get_next_contract_number(contract.branch_id, db)
    
    contract_data = contract.dict()
    contract_data['contract_number'] = contract_number
    
    contract_db = DBContract(**contract_data)
    db.add(contract_db)
    db.commit()
    db.refresh(contract_db)
    
    return Contract.from_orm(contract_db)

@api_router.get("/contracts", response_model=List[Contract])
async def get_contracts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accessible_branches = get_accessible_branches(current_user, db)
    
    query = db.query(DBContract)
    
    if accessible_branches:
        query = query.filter(DBContract.branch_id.in_(accessible_branches))
    
    contracts = query.all()
    return [Contract.from_orm(contract) for contract in contracts]

@api_router.get("/contracts/{contract_id}", response_model=Contract)
async def get_contract(contract_id: str, db: Session = Depends(get_db)):
    contract = db.query(DBContract).filter(DBContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return Contract.from_orm(contract)

# Task endpoints
@api_router.post("/tasks", response_model=Task)
async def create_task(task: TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify lawyer exists
    lawyer = db.query(DBLawyer).filter(DBLawyer.id == task.assigned_lawyer_id).first()
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    
    task_db = DBTask(**task.dict())
    db.add(task_db)
    db.commit()
    db.refresh(task_db)
    
    return Task.from_orm(task_db)

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accessible_branches = get_accessible_branches(current_user, db)
    
    query = db.query(DBTask)
    
    # Branch filtering
    if accessible_branches:
        query = query.filter(DBTask.branch_id.in_(accessible_branches))
    
    # Lawyer-specific filtering: lawyers can only see their assigned tasks
    if current_user.role == UserRole.lawyer:
        lawyer = db.query(DBLawyer).filter(DBLawyer.email == current_user.email).first()
        if lawyer:
            query = query.filter(DBTask.assigned_lawyer_id == lawyer.id)
    
    tasks = query.all()
    return [Task.from_orm(task) for task in tasks]

@api_router.get("/tasks/my-agenda")
async def get_my_agenda(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get tasks for the current user's agenda"""
    if current_user.role != UserRole.lawyer:
        raise HTTPException(status_code=403, detail="Only lawyers can access agenda")
    
    lawyer = db.query(DBLawyer).filter(DBLawyer.email == current_user.email).first()
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer profile not found")
    
    # Get tasks for the next 30 days
    start_date = datetime.now()
    end_date = start_date + timedelta(days=30)
    
    tasks = db.query(DBTask).filter(
        DBTask.assigned_lawyer_id == lawyer.id,
        DBTask.due_date >= start_date,
        DBTask.due_date <= end_date,
        DBTask.status != "completed"
    ).order_by(DBTask.due_date).all()
    
    return [Task.from_orm(task) for task in tasks]

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: TaskUpdate, db: Session = Depends(get_db)):
    task_db = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(task_db, field, value)
    
    task_db.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task_db)
    
    return Task.from_orm(task_db)

# Google Drive endpoints
@api_router.get("/google-drive/status")
async def get_google_drive_status(current_user: User = Depends(get_current_user)):
    """Check Google Drive integration status"""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can check Google Drive status"
        )
    
    is_configured = google_drive_service.is_configured()
    
    return {
        "configured": is_configured,
        "message": "Google Drive is configured and ready" if is_configured else "Google Drive needs to be configured"
    }

@api_router.get("/google-drive/auth-url")
async def get_google_drive_auth_url(current_user: User = Depends(get_current_user)):
    """Get Google Drive OAuth authorization URL"""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can configure Google Drive"
        )
    
    auth_url = google_drive_service.get_authorization_url()
    
    if not auth_url:
        raise HTTPException(
            status_code=400,
            detail="Failed to generate authorization URL. Check Google credentials file."
        )
    
    return {"authorization_url": auth_url}

@api_router.post("/google-drive/authorize")
async def authorize_google_drive(
    auth_request: GoogleDriveAuthRequest,
    current_user: User = Depends(get_current_user)
):
    """Complete Google Drive OAuth authorization"""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can configure Google Drive"
        )
    
    success = google_drive_service.exchange_code_for_token(auth_request.authorization_code)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to authorize Google Drive access"
        )
    
    return {"message": "Google Drive successfully configured"}

@api_router.post("/google-drive/generate-procuracao")
async def generate_procuracao(
    request: ProcuracaoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate power of attorney document and save to Google Drive"""
    
    # Get client data
    client = db.query(DBClient).filter(DBClient.id == request.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check access permissions
    accessible_branches = get_accessible_branches(current_user, db)
    if accessible_branches and client.branch_id not in accessible_branches:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this client"
        )
    
    # Get process data if provided
    process_data = None
    if request.process_id:
        process = db.query(DBProcess).filter(DBProcess.id == request.process_id).first()
        if not process:
            raise HTTPException(status_code=404, detail="Process not found")
        
        if accessible_branches and process.branch_id not in accessible_branches:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this process"
            )
        
        process_data = {
            'process_number': process.process_number,
            'type': process.type,
            'description': process.description
        }
    
    # Prepare client data for document generation
    client_data = {
        'name': client.name,
        'nationality': client.nationality,
        'civil_status': client.civil_status,
        'profession': client.profession,
        'cpf': client.cpf,
        'street': client.street,
        'number': client.number,
        'city': client.city,
        'district': client.district,
        'state': client.state,
        'complement': client.complement or ''
    }
    
    # Generate and save document
    try:
        drive_link = google_drive_service.generate_and_save_procuracao(client_data, process_data)
        
        if not drive_link:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate or save document. Check Google Drive configuration."
            )
        
        return {
            "message": "Procuração generated successfully",
            "drive_link": drive_link,
            "client_name": client.name,
            "process_number": process_data.get('process_number') if process_data else None
        }
        
    except Exception as e:
        logger.error(f"Error generating procuração: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating document: {str(e)}"
        )

@api_router.get("/google-drive/client-documents/{client_id}")
async def get_client_documents(
    client_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[DocumentInfo]:
    """Get list of documents for a client from Google Drive"""
    
    # Get client data
    client = db.query(DBClient).filter(DBClient.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check access permissions
    accessible_branches = get_accessible_branches(current_user, db)
    if accessible_branches and client.branch_id not in accessible_branches:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this client"
        )
    
    try:
        documents = google_drive_service.list_client_documents(client.name)
        
        return [
            DocumentInfo(
                id=doc['id'],
                name=doc['name'],
                created_time=doc['createdTime'],
                web_view_link=doc['webViewLink'],
                mime_type=doc['mimeType']
            )
            for doc in documents
        ]
        
    except Exception as e:
        logger.error(f"Error listing client documents: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving client documents"
        )

# Dashboard endpoint
@api_router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accessible_branches = get_accessible_branches(current_user, db)
    
    # Base filters
    client_filter = []
    process_filter = []
    transaction_filter = []
    
    if accessible_branches:
        client_filter.append(DBClient.branch_id.in_(accessible_branches))
        process_filter.append(DBProcess.branch_id.in_(accessible_branches))
        transaction_filter.append(DBFinancialTransaction.branch_id.in_(accessible_branches))
    
    # Count totals
    total_clients = db.query(DBClient).filter(*client_filter).count()
    total_processes = db.query(DBProcess).filter(*process_filter).count()
    
    # Financial data (only if user has access)
    total_revenue = 0
    total_expenses = 0
    pending_payments = 0
    overdue_payments = 0
    monthly_revenue = 0
    monthly_expenses = 0
    
    if check_financial_access(current_user, db):
        # Calculate totals
        revenue_result = db.query(func.sum(DBFinancialTransaction.value)).filter(
            DBFinancialTransaction.type == TransactionType.receita,
            *transaction_filter
        ).scalar()
        total_revenue = revenue_result or 0
        
        expenses_result = db.query(func.sum(DBFinancialTransaction.value)).filter(
            DBFinancialTransaction.type == TransactionType.despesa,
            *transaction_filter
        ).scalar()
        total_expenses = expenses_result or 0
        
        # Count payments
        pending_payments = db.query(DBFinancialTransaction).filter(
            DBFinancialTransaction.status == TransactionStatus.pendente,
            *transaction_filter
        ).count()
        
        overdue_payments = db.query(DBFinancialTransaction).filter(
            DBFinancialTransaction.status == TransactionStatus.vencido,
            *transaction_filter
        ).count()
        
        # Monthly calculations
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month_start = current_month_start + timedelta(days=32)
        next_month_start = next_month_start.replace(day=1)
        
        monthly_revenue_result = db.query(func.sum(DBFinancialTransaction.value)).filter(
            DBFinancialTransaction.type == TransactionType.receita,
            DBFinancialTransaction.due_date >= current_month_start,
            DBFinancialTransaction.due_date < next_month_start,
            *transaction_filter
        ).scalar()
        monthly_revenue = monthly_revenue_result or 0
        
        monthly_expenses_result = db.query(func.sum(DBFinancialTransaction.value)).filter(
            DBFinancialTransaction.type == TransactionType.despesa,
            DBFinancialTransaction.due_date >= current_month_start,
            DBFinancialTransaction.due_date < next_month_start,
            *transaction_filter
        ).scalar()
        monthly_expenses = monthly_expenses_result or 0
    
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

# Create tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    
    # Create session for setup
    db = SessionLocal()
    
    try:
        # Create default branches if they don't exist
        existing_branches = db.query(DBBranch).count()
        if existing_branches == 0:
            # Create default branches
            filial_caxias = DBBranch(
                name="GB Advocacia & N. Comin - Caxias do Sul",
                cnpj="12.345.678/0001-90",
                address="Rua Os Dezoito do Forte, 1234 - Centro, Caxias do Sul - RS",
                phone="(54) 3456-7890",
                email="caxias@gbadvocacia.com",
                responsible="Dr. Gustavo Batista"
            )
            
            filial_nova_prata = DBBranch(
                name="GB Advocacia & N. Comin - Nova Prata",
                cnpj="12.345.678/0002-01",
                address="Rua General Osório, 567 - Centro, Nova Prata - RS",
                phone="(54) 3242-1234",
                email="novaprata@gbadvocacia.com",
                responsible="Dra. Natália Comin"
            )
            
            db.add(filial_caxias)
            db.add(filial_nova_prata)
            db.commit()
            
            logging.info("Default branches created: Caxias do Sul and Nova Prata")
            
            # Create admin users for each branch
            admin_caxias = DBUser(
                username="admin_caxias",
                email="admin.caxias@gbadvocacia.com",
                full_name="Administrador Caxias do Sul",
                role=UserRole.admin,
                branch_id=filial_caxias.id,
                hashed_password=get_password_hash("admin123"),
                is_active=True
            )
            
            admin_nova_prata = DBUser(
                username="admin_novaprata",
                email="admin.novaprata@gbadvocacia.com",
                full_name="Administrador Nova Prata",
                role=UserRole.admin,
                branch_id=filial_nova_prata.id,
                hashed_password=get_password_hash("admin123"),
                is_active=True
            )
            
            db.add(admin_caxias)
            db.add(admin_nova_prata)
            db.commit()
            
            logging.info("Branch administrators created")
        
        # Create super admin if it doesn't exist
        existing_super_admin = db.query(DBUser).filter(
            DBUser.username == "admin",
            DBUser.branch_id.is_(None)
        ).first()
        
        if not existing_super_admin:
            super_admin_user = DBUser(
                username="admin",
                email="admin@gbadvocacia.com",
                full_name="Super Administrador GB Advocacia",
                role=UserRole.admin,
                branch_id=None,
                hashed_password=get_password_hash("admin123"),
                is_active=True
            )
            db.add(super_admin_user)
            db.commit()
            logging.info("Super admin user created: username=admin, password=admin123")
            
    finally:
        db.close()

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