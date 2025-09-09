from sqlalchemy import create_engine, Column, String, Boolean, Float, DateTime, Integer, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import os
from enum import Enum

# Database URL
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://advocacia_user:advocacia_pass@localhost/gb_advocacia_db')

# Create engine
engine = create_engine(DATABASE_URL)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()

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

class UserRole(str, Enum):
    admin = "admin"
    lawyer = "lawyer"
    secretary = "secretary"

# Database Models
class Branch(Base):
    __tablename__ = "branches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    cnpj = Column(String, unique=True, nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    responsible = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="branch")
    clients = relationship("Client", back_populates="branch")
    processes = relationship("Process", back_populates="branch")
    financial_transactions = relationship("FinancialTransaction", back_populates="branch")
    contracts = relationship("Contract", back_populates="branch")
    lawyers = relationship("Lawyer", back_populates="branch")

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    branch_id = Column(String, ForeignKey("branches.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branch = relationship("Branch", back_populates="users")

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    nationality = Column(String, nullable=False)
    civil_status = Column(String, nullable=False)
    profession = Column(String, nullable=False)
    cpf = Column(String, nullable=False)
    
    # Address fields
    street = Column(String, nullable=False)
    number = Column(String, nullable=False)
    city = Column(String, nullable=False)
    district = Column(String, nullable=False)
    state = Column(String, nullable=False)
    complement = Column(String, nullable=True)
    
    phone = Column(String, nullable=False)
    client_type = Column(SQLEnum(ClientType), nullable=False)
    branch_id = Column(String, ForeignKey("branches.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branch = relationship("Branch", back_populates="clients")
    processes = relationship("Process", back_populates="client")
    financial_transactions = relationship("FinancialTransaction", back_populates="client")
    contracts = relationship("Contract", back_populates="client")

class Lawyer(Base):
    __tablename__ = "lawyers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    oab_number = Column(String, nullable=False)
    oab_state = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=False)
    specialization = Column(String, nullable=True)
    branch_id = Column(String, ForeignKey("branches.id"), nullable=False)
    
    # New fields for enhanced permissions
    access_financial_data = Column(Boolean, default=True)  # Controls access to financial information
    allowed_branch_ids = Column(Text, nullable=True)  # JSON string of allowed branch IDs
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branch = relationship("Branch", back_populates="lawyers")
    assigned_processes = relationship("Process", back_populates="responsible_lawyer")

class Process(Base):
    __tablename__ = "processes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    process_number = Column(String, nullable=False)
    type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    role = Column(SQLEnum(ProcessRole), nullable=False)
    branch_id = Column(String, ForeignKey("branches.id"), nullable=False)
    
    # New field for lawyer assignment
    responsible_lawyer_id = Column(String, ForeignKey("lawyers.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branch = relationship("Branch", back_populates="processes")
    client = relationship("Client", back_populates="processes")
    responsible_lawyer = relationship("Lawyer", back_populates="assigned_processes")
    financial_transactions = relationship("FinancialTransaction", back_populates="process")
    contracts = relationship("Contract", back_populates="process")

class FinancialTransaction(Base):
    __tablename__ = "financial_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)
    process_id = Column(String, ForeignKey("processes.id"), nullable=True)
    type = Column(SQLEnum(TransactionType), nullable=False)
    description = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    due_date = Column(DateTime, nullable=False)
    payment_date = Column(DateTime, nullable=True)
    status = Column(SQLEnum(TransactionStatus), nullable=False)
    category = Column(String, nullable=False)
    branch_id = Column(String, ForeignKey("branches.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branch = relationship("Branch", back_populates="financial_transactions")
    client = relationship("Client", back_populates="financial_transactions")
    process = relationship("Process", back_populates="financial_transactions")

class Contract(Base):
    __tablename__ = "contracts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Sequential contract numbering
    contract_number = Column(String, unique=True, nullable=False)
    
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    process_id = Column(String, ForeignKey("processes.id"), nullable=True)
    value = Column(Float, nullable=False)
    payment_conditions = Column(String, nullable=False)
    installments = Column(Integer, nullable=False)
    branch_id = Column(String, ForeignKey("branches.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    branch = relationship("Branch", back_populates="contracts")
    client = relationship("Client", back_populates="contracts")
    process = relationship("Process", back_populates="contracts")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    priority = Column(String, default="medium")  # low, medium, high
    status = Column(String, default="pending")  # pending, in_progress, completed
    assigned_lawyer_id = Column(String, ForeignKey("lawyers.id"), nullable=False)
    client_id = Column(String, ForeignKey("clients.id"), nullable=True)
    process_id = Column(String, ForeignKey("processes.id"), nullable=True)
    branch_id = Column(String, ForeignKey("branches.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ContractNumberSequence(Base):
    __tablename__ = "contract_number_sequence"
    
    id = Column(Integer, primary_key=True)
    last_number = Column(Integer, default=0)
    year = Column(Integer, nullable=False)
    branch_id = Column(String, ForeignKey("branches.id"), nullable=False)

# Dependency to get database session
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)

def drop_tables():
    Base.metadata.drop_all(bind=engine)