#!/usr/bin/env python3
"""
Backend API Testing Suite for GB Advocacia & N. Comin Cash Control System
Tests all backend APIs: Client Management, Process Management, Financial Transactions, Contracts, and Dashboard
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://legalflow-4.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.created_entities = {
            'clients': [],
            'processes': [],
            'financial_transactions': [],
            'contracts': [],
            'lawyers': []
        }
        self.auth_tokens = {}  # Store auth tokens for different users
        self.branch_ids = {}  # Store branch IDs
        
    def log_test(self, test_name: str, success: bool, message: str, details: Any = None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_client_management_api(self):
        """Test Client Management API - CRUD operations with address management"""
        print("\n=== Testing Client Management API ===")
        
        # Get a branch_id for client creation (use Caxias branch if available)
        branch_id = self.branch_ids.get('caxias') if self.branch_ids else None
        if not branch_id:
            # Try to get branches and use the first one
            try:
                if 'super_admin' in self.auth_tokens:
                    response = self.session.get(f"{API_BASE_URL}/branches", 
                                              headers={'Authorization': f'Bearer {self.auth_tokens["super_admin"]}'})
                    if response.status_code == 200:
                        branches = response.json()
                        if branches:
                            branch_id = branches[0]['id']
            except:
                pass
        
        if not branch_id:
            self.log_test("Client Management Prerequisites", False, "No branch_id available for client creation")
            return
        
        # Test 1: Create Individual Client
        individual_client_data = {
            "name": "Maria Silva Santos",
            "nationality": "Brasileira",
            "civil_status": "Casada",
            "profession": "Empresária",
            "cpf": "123.456.789-01",
            "address": {
                "street": "Rua das Flores",
                "number": "123",
                "city": "São Paulo",
                "district": "Centro",
                "state": "SP",
                "complement": "Apto 45"
            },
            "phone": "(11) 99999-1234",
            "client_type": "individual",
            "branch_id": branch_id
        }
        
        try:
            headers = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'} if 'super_admin' in self.auth_tokens else {}
            response = self.session.post(f"{API_BASE_URL}/clients", json=individual_client_data, headers=headers)
            if response.status_code == 200:
                client = response.json()
                self.created_entities['clients'].append(client['id'])
                self.log_test("Create Individual Client", True, f"Created client with ID: {client['id']}")
                
                # Verify required fields
                required_fields = ['id', 'name', 'cpf', 'address', 'client_type', 'created_at']
                missing_fields = [field for field in required_fields if field not in client]
                if missing_fields:
                    self.log_test("Client Fields Validation", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Client Fields Validation", True, "All required fields present")
            else:
                self.log_test("Create Individual Client", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Individual Client", False, f"Exception: {str(e)}")
        
        # Test 2: Create Corporate Client
        corporate_client_data = {
            "name": "Empresa ABC Ltda",
            "nationality": "Brasileira",
            "civil_status": "N/A",
            "profession": "Comércio",
            "cpf": "12.345.678/0001-90",
            "address": {
                "street": "Av. Paulista",
                "number": "1000",
                "city": "São Paulo",
                "district": "Bela Vista",
                "state": "SP",
                "complement": "Sala 1001"
            },
            "phone": "(11) 3333-4444",
            "client_type": "corporate",
            "branch_id": branch_id
        }
        
        try:
            headers = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'} if 'super_admin' in self.auth_tokens else {}
            response = self.session.post(f"{API_BASE_URL}/clients", json=corporate_client_data, headers=headers)
            if response.status_code == 200:
                client = response.json()
                self.created_entities['clients'].append(client['id'])
                self.log_test("Create Corporate Client", True, f"Created corporate client with ID: {client['id']}")
            else:
                self.log_test("Create Corporate Client", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Corporate Client", False, f"Exception: {str(e)}")
        
        # Test 3: Get All Clients
        try:
            headers = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'} if 'super_admin' in self.auth_tokens else {}
            response = self.session.get(f"{API_BASE_URL}/clients", headers=headers)
            if response.status_code == 200:
                clients = response.json()
                self.log_test("Get All Clients", True, f"Retrieved {len(clients)} clients")
                
                # Verify our created clients are in the list
                created_ids = set(self.created_entities['clients'])
                retrieved_ids = set(client['id'] for client in clients)
                if created_ids.issubset(retrieved_ids):
                    self.log_test("Verify Created Clients in List", True, "All created clients found in list")
                else:
                    missing = created_ids - retrieved_ids
                    self.log_test("Verify Created Clients in List", False, f"Missing clients: {missing}")
            else:
                self.log_test("Get All Clients", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Get All Clients", False, f"Exception: {str(e)}")
        
        # Test 4: Get Single Client
        if self.created_entities['clients']:
            client_id = self.created_entities['clients'][0]
            try:
                response = self.session.get(f"{API_BASE_URL}/clients/{client_id}")
                if response.status_code == 200:
                    client = response.json()
                    self.log_test("Get Single Client", True, f"Retrieved client: {client['name']}")
                else:
                    self.log_test("Get Single Client", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Get Single Client", False, f"Exception: {str(e)}")
        
        # Test 5: Update Client
        if self.created_entities['clients']:
            client_id = self.created_entities['clients'][0]
            update_data = {
                "phone": "(11) 88888-5555",
                "address": {
                    "street": "Rua das Flores",
                    "number": "123",
                    "city": "São Paulo",
                    "district": "Centro",
                    "state": "SP",
                    "complement": "Apto 46"  # Changed complement
                }
            }
            try:
                response = self.session.put(f"{API_BASE_URL}/clients/{client_id}", json=update_data)
                if response.status_code == 200:
                    updated_client = response.json()
                    if updated_client['phone'] == update_data['phone']:
                        self.log_test("Update Client", True, "Client updated successfully")
                    else:
                        self.log_test("Update Client", False, "Update data not reflected")
                else:
                    self.log_test("Update Client", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Update Client", False, f"Exception: {str(e)}")
    
    def test_process_management_api(self):
        """Test Process Management API - CRUD operations with client linking"""
        print("\n=== Testing Process Management API ===")
        
        if not self.created_entities['clients']:
            self.log_test("Process Management Prerequisites", False, "No clients available for process testing")
            return
        
        client_id = self.created_entities['clients'][0]
        
        # Test 1: Create Process
        process_data = {
            "client_id": client_id,
            "process_number": "0001234-56.2024.8.26.0100",
            "type": "Ação de Cobrança",
            "status": "Em Andamento",
            "value": 15000.00,
            "description": "Cobrança de honorários advocatícios",
            "role": "creditor",
            "branch_id": self.branch_ids.get('caxias') or client_id  # Use branch_id if available
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/processes", json=process_data)
            if response.status_code == 200:
                process = response.json()
                self.created_entities['processes'].append(process['id'])
                self.log_test("Create Process", True, f"Created process with ID: {process['id']}")
                
                # Verify client linking
                if process['client_id'] == client_id:
                    self.log_test("Process Client Linking", True, "Process correctly linked to client")
                else:
                    self.log_test("Process Client Linking", False, "Process not linked to correct client")
            else:
                self.log_test("Create Process", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Process", False, f"Exception: {str(e)}")
        
        # Test 2: Create Process with Invalid Client
        invalid_process_data = {
            "client_id": "invalid-client-id",
            "process_number": "0001234-56.2024.8.26.0101",
            "type": "Ação de Cobrança",
            "status": "Em Andamento",
            "value": 10000.00,
            "description": "Test process with invalid client",
            "role": "debtor",
            "branch_id": self.branch_ids.get('caxias') or "some-branch-id"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/processes", json=invalid_process_data)
            if response.status_code == 404:
                self.log_test("Process Invalid Client Validation", True, "Correctly rejected invalid client ID")
            else:
                self.log_test("Process Invalid Client Validation", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Process Invalid Client Validation", False, f"Exception: {str(e)}")
        
        # Test 3: Get All Processes
        try:
            response = self.session.get(f"{API_BASE_URL}/processes")
            if response.status_code == 200:
                processes = response.json()
                self.log_test("Get All Processes", True, f"Retrieved {len(processes)} processes")
            else:
                self.log_test("Get All Processes", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Get All Processes", False, f"Exception: {str(e)}")
        
        # Test 4: Get Client Processes
        try:
            response = self.session.get(f"{API_BASE_URL}/clients/{client_id}/processes")
            if response.status_code == 200:
                client_processes = response.json()
                self.log_test("Get Client Processes", True, f"Retrieved {len(client_processes)} processes for client")
                
                # Verify all processes belong to the client
                all_belong_to_client = all(p['client_id'] == client_id for p in client_processes)
                if all_belong_to_client:
                    self.log_test("Client Process Filtering", True, "All processes belong to correct client")
                else:
                    self.log_test("Client Process Filtering", False, "Some processes don't belong to client")
            else:
                self.log_test("Get Client Processes", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Get Client Processes", False, f"Exception: {str(e)}")
        
        # Test 5: Update Process
        if self.created_entities['processes']:
            process_id = self.created_entities['processes'][0]
            update_data = {
                "status": "Finalizado",
                "value": 18000.00
            }
            try:
                response = self.session.put(f"{API_BASE_URL}/processes/{process_id}", json=update_data)
                if response.status_code == 200:
                    updated_process = response.json()
                    if updated_process['status'] == "Finalizado" and updated_process['value'] == 18000.00:
                        self.log_test("Update Process", True, "Process updated successfully")
                    else:
                        self.log_test("Update Process", False, "Update data not reflected")
                else:
                    self.log_test("Update Process", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Update Process", False, f"Exception: {str(e)}")
    
    def test_financial_transaction_api(self):
        """Test Financial Transaction API - Revenue/expense tracking"""
        print("\n=== Testing Financial Transaction API ===")
        
        client_id = self.created_entities['clients'][0] if self.created_entities['clients'] else None
        process_id = self.created_entities['processes'][0] if self.created_entities['processes'] else None
        
        # Test 1: Create Revenue Transaction
        revenue_data = {
            "client_id": client_id,
            "process_id": process_id,
            "type": "receita",
            "description": "Honorários advocatícios - Ação de Cobrança",
            "value": 5000.00,
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "status": "pendente",
            "category": "Honorários",
            "branch_id": self.branch_ids.get('caxias') or client_id  # Use branch_id if available
        }
        
        try:
            headers = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'} if 'super_admin' in self.auth_tokens else {}
            response = self.session.post(f"{API_BASE_URL}/financial", json=revenue_data, headers=headers)
            if response.status_code == 200:
                transaction = response.json()
                self.created_entities['financial_transactions'].append(transaction['id'])
                self.log_test("Create Revenue Transaction", True, f"Created revenue transaction: {transaction['id']}")
            else:
                self.log_test("Create Revenue Transaction", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Revenue Transaction", False, f"Exception: {str(e)}")
        
        # Test 2: Create Expense Transaction
        expense_data = {
            "type": "despesa",
            "description": "Custas processuais - Tribunal de Justiça",
            "value": 250.00,
            "due_date": (datetime.now() + timedelta(days=15)).isoformat(),
            "status": "pendente",
            "category": "Custas Processuais",
            "branch_id": self.branch_ids.get('caxias') or "some-branch-id"
        }
        
        try:
            headers = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'} if 'super_admin' in self.auth_tokens else {}
            response = self.session.post(f"{API_BASE_URL}/financial", json=expense_data, headers=headers)
            if response.status_code == 200:
                transaction = response.json()
                self.created_entities['financial_transactions'].append(transaction['id'])
                self.log_test("Create Expense Transaction", True, f"Created expense transaction: {transaction['id']}")
            else:
                self.log_test("Create Expense Transaction", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Expense Transaction", False, f"Exception: {str(e)}")
        
        # Test 3: Create Overdue Transaction
        overdue_data = {
            "type": "receita",
            "description": "Honorários em atraso",
            "value": 3000.00,
            "due_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "status": "vencido",
            "category": "Honorários",
            "branch_id": self.branch_ids.get('caxias') or "some-branch-id"
        }
        
        try:
            headers = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'} if 'super_admin' in self.auth_tokens else {}
            response = self.session.post(f"{API_BASE_URL}/financial", json=overdue_data, headers=headers)
            if response.status_code == 200:
                transaction = response.json()
                self.created_entities['financial_transactions'].append(transaction['id'])
                self.log_test("Create Overdue Transaction", True, f"Created overdue transaction: {transaction['id']}")
            else:
                self.log_test("Create Overdue Transaction", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Overdue Transaction", False, f"Exception: {str(e)}")
        
        # Test 4: Get All Financial Transactions
        try:
            response = self.session.get(f"{API_BASE_URL}/financial")
            if response.status_code == 200:
                transactions = response.json()
                self.log_test("Get All Financial Transactions", True, f"Retrieved {len(transactions)} transactions")
                
                # Verify transaction types
                revenue_count = sum(1 for t in transactions if t['type'] == 'receita')
                expense_count = sum(1 for t in transactions if t['type'] == 'despesa')
                self.log_test("Transaction Type Verification", True, f"Found {revenue_count} revenue, {expense_count} expense transactions")
            else:
                self.log_test("Get All Financial Transactions", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Get All Financial Transactions", False, f"Exception: {str(e)}")
        
        # Test 5: Update Transaction Status (Mark as Paid)
        if self.created_entities['financial_transactions']:
            transaction_id = self.created_entities['financial_transactions'][0]
            update_data = {
                "status": "pago",
                "payment_date": datetime.now().isoformat()
            }
            try:
                response = self.session.put(f"{API_BASE_URL}/financial/{transaction_id}", json=update_data)
                if response.status_code == 200:
                    updated_transaction = response.json()
                    if updated_transaction['status'] == "pago":
                        self.log_test("Update Transaction Status", True, "Transaction marked as paid")
                    else:
                        self.log_test("Update Transaction Status", False, "Status update not reflected")
                else:
                    self.log_test("Update Transaction Status", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Update Transaction Status", False, f"Exception: {str(e)}")
    
    def test_contract_management_api(self):
        """Test Contract Management API - Contract management with installments"""
        print("\n=== Testing Contract Management API ===")
        
        if not self.created_entities['clients']:
            self.log_test("Contract Management Prerequisites", False, "No clients available for contract testing")
            return
        
        client_id = self.created_entities['clients'][0]
        process_id = self.created_entities['processes'][0] if self.created_entities['processes'] else None
        
        # Test 1: Create Contract
        contract_data = {
            "client_id": client_id,
            "process_id": process_id,
            "value": 25000.00,
            "payment_conditions": "Pagamento em 5 parcelas mensais de R$ 5.000,00",
            "installments": 5,
            "branch_id": self.branch_ids.get('caxias') or client_id  # Use branch_id if available
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/contracts", json=contract_data)
            if response.status_code == 200:
                contract = response.json()
                self.created_entities['contracts'].append(contract['id'])
                self.log_test("Create Contract", True, f"Created contract with ID: {contract['id']}")
                
                # Verify contract fields
                if contract['value'] == 25000.00 and contract['installments'] == 5:
                    self.log_test("Contract Data Validation", True, "Contract data correctly stored")
                else:
                    self.log_test("Contract Data Validation", False, "Contract data mismatch")
            else:
                self.log_test("Create Contract", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Contract", False, f"Exception: {str(e)}")
        
        # Test 2: Create Contract with Invalid Client
        invalid_contract_data = {
            "client_id": "invalid-client-id",
            "value": 10000.00,
            "payment_conditions": "Pagamento à vista",
            "installments": 1,
            "branch_id": self.branch_ids.get('caxias') or "some-branch-id"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/contracts", json=invalid_contract_data)
            if response.status_code == 404:
                self.log_test("Contract Invalid Client Validation", True, "Correctly rejected invalid client ID")
            else:
                self.log_test("Contract Invalid Client Validation", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Contract Invalid Client Validation", False, f"Exception: {str(e)}")
        
        # Test 3: Get All Contracts
        try:
            response = self.session.get(f"{API_BASE_URL}/contracts")
            if response.status_code == 200:
                contracts = response.json()
                self.log_test("Get All Contracts", True, f"Retrieved {len(contracts)} contracts")
            else:
                self.log_test("Get All Contracts", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Get All Contracts", False, f"Exception: {str(e)}")
        
        # Test 4: Get Client Contracts
        try:
            response = self.session.get(f"{API_BASE_URL}/clients/{client_id}/contracts")
            if response.status_code == 200:
                client_contracts = response.json()
                self.log_test("Get Client Contracts", True, f"Retrieved {len(client_contracts)} contracts for client")
                
                # Verify all contracts belong to the client
                all_belong_to_client = all(c['client_id'] == client_id for c in client_contracts)
                if all_belong_to_client:
                    self.log_test("Client Contract Filtering", True, "All contracts belong to correct client")
                else:
                    self.log_test("Client Contract Filtering", False, "Some contracts don't belong to client")
            else:
                self.log_test("Get Client Contracts", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Get Client Contracts", False, f"Exception: {str(e)}")
    
    def test_dashboard_statistics_api(self):
        """Test Dashboard Statistics API - Real-time metrics and KPIs"""
        print("\n=== Testing Dashboard Statistics API ===")
        
        try:
            response = self.session.get(f"{API_BASE_URL}/dashboard")
            if response.status_code == 200:
                stats = response.json()
                self.log_test("Get Dashboard Statistics", True, "Retrieved dashboard statistics")
                
                # Verify required fields
                required_fields = [
                    'total_clients', 'total_processes', 'total_revenue', 'total_expenses',
                    'pending_payments', 'overdue_payments', 'monthly_revenue', 'monthly_expenses'
                ]
                missing_fields = [field for field in required_fields if field not in stats]
                if missing_fields:
                    self.log_test("Dashboard Fields Validation", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Dashboard Fields Validation", True, "All required dashboard fields present")
                
                # Verify data types and logical values
                if isinstance(stats['total_clients'], int) and stats['total_clients'] >= 0:
                    self.log_test("Dashboard Client Count", True, f"Total clients: {stats['total_clients']}")
                else:
                    self.log_test("Dashboard Client Count", False, f"Invalid client count: {stats['total_clients']}")
                
                if isinstance(stats['total_revenue'], (int, float)) and stats['total_revenue'] >= 0:
                    self.log_test("Dashboard Revenue Calculation", True, f"Total revenue: R$ {stats['total_revenue']}")
                else:
                    self.log_test("Dashboard Revenue Calculation", False, f"Invalid revenue: {stats['total_revenue']}")
                
                if isinstance(stats['total_expenses'], (int, float)) and stats['total_expenses'] >= 0:
                    self.log_test("Dashboard Expense Calculation", True, f"Total expenses: R$ {stats['total_expenses']}")
                else:
                    self.log_test("Dashboard Expense Calculation", False, f"Invalid expenses: {stats['total_expenses']}")
                
                # Verify pending and overdue payments are non-negative integers
                if isinstance(stats['pending_payments'], int) and stats['pending_payments'] >= 0:
                    self.log_test("Dashboard Pending Payments", True, f"Pending payments: {stats['pending_payments']}")
                else:
                    self.log_test("Dashboard Pending Payments", False, f"Invalid pending payments: {stats['pending_payments']}")
                
                if isinstance(stats['overdue_payments'], int) and stats['overdue_payments'] >= 0:
                    self.log_test("Dashboard Overdue Payments", True, f"Overdue payments: {stats['overdue_payments']}")
                else:
                    self.log_test("Dashboard Overdue Payments", False, f"Invalid overdue payments: {stats['overdue_payments']}")
                
                # Print summary for verification
                print(f"\n📊 Dashboard Summary:")
                print(f"   Clients: {stats['total_clients']}")
                print(f"   Processes: {stats['total_processes']}")
                print(f"   Total Revenue: R$ {stats['total_revenue']}")
                print(f"   Total Expenses: R$ {stats['total_expenses']}")
                print(f"   Pending Payments: {stats['pending_payments']}")
                print(f"   Overdue Payments: {stats['overdue_payments']}")
                print(f"   Monthly Revenue: R$ {stats['monthly_revenue']}")
                print(f"   Monthly Expenses: R$ {stats['monthly_expenses']}")
                
            else:
                self.log_test("Get Dashboard Statistics", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Get Dashboard Statistics", False, f"Exception: {str(e)}")
    
    def test_data_relationships(self):
        """Test relationships between entities"""
        print("\n=== Testing Data Relationships ===")
        
        if not all([self.created_entities['clients'], self.created_entities['processes'], 
                   self.created_entities['financial_transactions']]):
            self.log_test("Relationship Testing Prerequisites", False, "Missing entities for relationship testing")
            return
        
        client_id = self.created_entities['clients'][0]
        
        # Test client-process relationship
        try:
            response = self.session.get(f"{API_BASE_URL}/clients/{client_id}/processes")
            if response.status_code == 200:
                processes = response.json()
                if processes:
                    self.log_test("Client-Process Relationship", True, f"Client has {len(processes)} linked processes")
                else:
                    self.log_test("Client-Process Relationship", False, "No processes found for client")
            else:
                self.log_test("Client-Process Relationship", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Client-Process Relationship", False, f"Exception: {str(e)}")
        
        # Test client-contract relationship
        try:
            response = self.session.get(f"{API_BASE_URL}/clients/{client_id}/contracts")
            if response.status_code == 200:
                contracts = response.json()
                if contracts:
                    self.log_test("Client-Contract Relationship", True, f"Client has {len(contracts)} linked contracts")
                else:
                    self.log_test("Client-Contract Relationship", False, "No contracts found for client")
            else:
                self.log_test("Client-Contract Relationship", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Client-Contract Relationship", False, f"Exception: {str(e)}")
    
    def test_multi_branch_system(self):
        """Test Multi-Branch System - Branches, Authentication, and User Management"""
        print("\n=== Testing Multi-Branch System ===")
        
        # Test 1: Verify default branches were created
        try:
            response = self.session.get(f"{API_BASE_URL}/branches")
            if response.status_code == 401:
                # Need authentication, let's first login as super admin
                self.login_super_admin()
                response = self.session.get(f"{API_BASE_URL}/branches", 
                                          headers={'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'})
            
            if response.status_code == 200:
                branches = response.json()
                self.log_test("Get Branches Endpoint", True, f"Retrieved {len(branches)} branches")
                
                # Check for specific branches
                branch_names = [branch['name'] for branch in branches]
                caxias_found = any('Caxias do Sul' in name for name in branch_names)
                nova_prata_found = any('Nova Prata' in name for name in branch_names)
                
                if caxias_found and nova_prata_found:
                    self.log_test("Default Branches Created", True, "Found Caxias do Sul and Nova Prata branches")
                    # Store branch IDs for later use
                    for branch in branches:
                        if 'Caxias do Sul' in branch['name']:
                            self.branch_ids['caxias'] = branch['id']
                        elif 'Nova Prata' in branch['name']:
                            self.branch_ids['nova_prata'] = branch['id']
                else:
                    self.log_test("Default Branches Created", False, f"Missing expected branches. Found: {branch_names}")
                
                # Verify branch structure
                if branches:
                    branch = branches[0]
                    required_fields = ['id', 'name', 'cnpj', 'address', 'phone', 'email', 'responsible']
                    missing_fields = [field for field in required_fields if field not in branch]
                    if missing_fields:
                        self.log_test("Branch Structure Validation", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_test("Branch Structure Validation", True, "All required branch fields present")
            else:
                self.log_test("Get Branches Endpoint", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Get Branches Endpoint", False, f"Exception: {str(e)}")
    
    def login_super_admin(self):
        """Login as super admin"""
        login_data = {
            "username_or_email": "admin",
            "password": "admin123"
        }
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_tokens['super_admin'] = token_data['access_token']
                self.log_test("Super Admin Login", True, f"Logged in as: {token_data['user']['full_name']}")
                return True
            else:
                self.log_test("Super Admin Login", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Super Admin Login", False, f"Exception: {str(e)}")
            return False
    
    def test_branch_admin_authentication(self):
        """Test branch admin authentication"""
        print("\n=== Testing Branch Admin Authentication ===")
        
        # Test 1: Login as Caxias Admin
        caxias_login_data = {
            "username_or_email": "admin_caxias",
            "password": "admin123"
        }
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=caxias_login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_tokens['admin_caxias'] = token_data['access_token']
                user = token_data['user']
                self.log_test("Caxias Admin Login", True, f"Logged in as: {user['full_name']}")
                
                # Verify branch association
                if user.get('branch_id'):
                    self.log_test("Caxias Admin Branch Association", True, f"Admin linked to branch: {user['branch_id']}")
                else:
                    self.log_test("Caxias Admin Branch Association", False, "Admin not linked to any branch")
            else:
                self.log_test("Caxias Admin Login", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Caxias Admin Login", False, f"Exception: {str(e)}")
        
        # Test 2: Login as Nova Prata Admin
        nova_prata_login_data = {
            "username_or_email": "admin_novaprata",
            "password": "admin123"
        }
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=nova_prata_login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_tokens['admin_novaprata'] = token_data['access_token']
                user = token_data['user']
                self.log_test("Nova Prata Admin Login", True, f"Logged in as: {user['full_name']}")
                
                # Verify branch association
                if user.get('branch_id'):
                    self.log_test("Nova Prata Admin Branch Association", True, f"Admin linked to branch: {user['branch_id']}")
                else:
                    self.log_test("Nova Prata Admin Branch Association", False, "Admin not linked to any branch")
            else:
                self.log_test("Nova Prata Admin Login", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Nova Prata Admin Login", False, f"Exception: {str(e)}")
        
        # Test 3: Test email login (should work with email instead of username)
        email_login_data = {
            "username_or_email": "admin.caxias@gbadvocacia.com",
            "password": "admin123"
        }
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=email_login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.log_test("Email-based Login", True, f"Successfully logged in using email")
            else:
                self.log_test("Email-based Login", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Email-based Login", False, f"Exception: {str(e)}")
    
    def test_lawyer_management_and_authentication(self):
        """Test lawyer creation and authentication with OAB and new fields"""
        print("\n=== Testing Lawyer Management and Authentication ===")
        
        # Ensure we have super admin token
        if 'super_admin' not in self.auth_tokens:
            self.login_super_admin()
        
        if not self.branch_ids:
            # Get branches first
            response = self.session.get(f"{API_BASE_URL}/branches", 
                                      headers={'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'})
            if response.status_code == 200:
                branches = response.json()
                for branch in branches:
                    if 'Caxias do Sul' in branch['name']:
                        self.branch_ids['caxias'] = branch['id']
                    elif 'Nova Prata' in branch['name']:
                        self.branch_ids['nova_prata'] = branch['id']
        
        # Test 1: Create a test lawyer with new fields
        if self.branch_ids.get('caxias'):
            lawyer_data = {
                "full_name": "Dr. João Silva Advocacia",
                "oab_number": "123456",
                "oab_state": "RS",
                "email": "joao.silva@gbadvocacia.com",
                "phone": "(54) 99999-8888",
                "specialization": "Direito Civil",
                "branch_id": self.branch_ids['caxias'],
                "access_financial_data": True,
                "allowed_branch_ids": [self.branch_ids['caxias']]
            }
            
            try:
                response = self.session.post(f"{API_BASE_URL}/lawyers", 
                                           json=lawyer_data,
                                           headers={'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'})
                if response.status_code == 200:
                    lawyer = response.json()
                    self.created_entities['lawyers'].append(lawyer['id'])
                    self.log_test("Create Test Lawyer with New Fields", True, f"Created lawyer: {lawyer['full_name']}")
                    
                    # Verify new fields
                    if lawyer.get('access_financial_data') == True:
                        self.log_test("Lawyer Financial Access Field", True, "access_financial_data field correctly set")
                    else:
                        self.log_test("Lawyer Financial Access Field", False, f"Expected True, got {lawyer.get('access_financial_data')}")
                    
                    # Test 2: Login as lawyer using email/OAB
                    lawyer_login_data = {
                        "username_or_email": lawyer_data['email'],
                        "password": lawyer_data['oab_number']  # OAB number as password
                    }
                    
                    try:
                        login_response = self.session.post(f"{API_BASE_URL}/auth/login", json=lawyer_login_data)
                        if login_response.status_code == 200:
                            token_data = login_response.json()
                            self.auth_tokens['test_lawyer'] = token_data['access_token']
                            user = token_data['user']
                            self.log_test("Lawyer Login (Email/OAB)", True, f"Lawyer logged in: {user['full_name']}")
                            
                            # Verify lawyer role and branch association
                            if user.get('role') == 'lawyer':
                                self.log_test("Lawyer Role Verification", True, "User has correct lawyer role")
                            else:
                                self.log_test("Lawyer Role Verification", False, f"Expected 'lawyer', got '{user.get('role')}'")
                            
                            if user.get('branch_id') == self.branch_ids['caxias']:
                                self.log_test("Lawyer Branch Association", True, "Lawyer correctly associated with branch")
                            else:
                                self.log_test("Lawyer Branch Association", False, "Lawyer not correctly associated with branch")
                        else:
                            self.log_test("Lawyer Login (Email/OAB)", False, f"HTTP {login_response.status_code}", login_response.text)
                    except Exception as e:
                        self.log_test("Lawyer Login (Email/OAB)", False, f"Exception: {str(e)}")
                        
                else:
                    self.log_test("Create Test Lawyer with New Fields", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Create Test Lawyer with New Fields", False, f"Exception: {str(e)}")
        
        # Test 3: Create lawyer with restricted financial access
        if self.branch_ids.get('nova_prata'):
            restricted_lawyer_data = {
                "full_name": "Dra. Maria Santos",
                "oab_number": "654321",
                "oab_state": "RS",
                "email": "maria.santos@gbadvocacia.com",
                "phone": "(54) 99999-7777",
                "specialization": "Direito Trabalhista",
                "branch_id": self.branch_ids['nova_prata'],
                "access_financial_data": False,
                "allowed_branch_ids": [self.branch_ids['nova_prata']]
            }
            
            try:
                response = self.session.post(f"{API_BASE_URL}/lawyers", 
                                           json=restricted_lawyer_data,
                                           headers={'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'})
                if response.status_code == 200:
                    lawyer = response.json()
                    self.created_entities['lawyers'].append(lawyer['id'])
                    self.log_test("Create Restricted Lawyer", True, f"Created restricted lawyer: {lawyer['full_name']}")
                    
                    # Verify restricted access
                    if lawyer.get('access_financial_data') == False:
                        self.log_test("Lawyer Restricted Financial Access", True, "access_financial_data correctly set to False")
                    else:
                        self.log_test("Lawyer Restricted Financial Access", False, f"Expected False, got {lawyer.get('access_financial_data')}")
                    
                    # Login as restricted lawyer
                    restricted_login_data = {
                        "username_or_email": restricted_lawyer_data['email'],
                        "password": restricted_lawyer_data['oab_number']
                    }
                    
                    try:
                        login_response = self.session.post(f"{API_BASE_URL}/auth/login", json=restricted_login_data)
                        if login_response.status_code == 200:
                            token_data = login_response.json()
                            self.auth_tokens['restricted_lawyer'] = token_data['access_token']
                            self.log_test("Restricted Lawyer Login", True, f"Restricted lawyer logged in successfully")
                        else:
                            self.log_test("Restricted Lawyer Login", False, f"HTTP {login_response.status_code}", login_response.text)
                    except Exception as e:
                        self.log_test("Restricted Lawyer Login", False, f"Exception: {str(e)}")
                        
                else:
                    self.log_test("Create Restricted Lawyer", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Create Restricted Lawyer", False, f"Exception: {str(e)}")
        else:
            self.log_test("Create Test Lawyer", False, "No Caxias branch ID available")
    
    def test_branch_data_isolation(self):
        """Test that branch data is properly isolated"""
        print("\n=== Testing Branch Data Isolation ===")
        
        # This test would verify that users can only see data from their own branch
        # For now, we'll test that the branch system is working by creating entities with branch_id
        
        if not self.branch_ids:
            self.log_test("Branch Data Isolation", False, "No branch IDs available for testing")
            return
        
        # Test creating a client with branch_id
        if self.branch_ids.get('caxias'):
            client_data = {
                "name": "Cliente Teste Caxias",
                "nationality": "Brasileira",
                "civil_status": "Solteiro",
                "profession": "Engenheiro",
                "cpf": "111.222.333-44",
                "address": {
                    "street": "Rua Teste",
                    "number": "100",
                    "city": "Caxias do Sul",
                    "district": "Centro",
                    "state": "RS",
                    "complement": ""
                },
                "phone": "(54) 99999-0000",
                "client_type": "individual",
                "branch_id": self.branch_ids['caxias']
            }
            
            try:
                response = self.session.post(f"{API_BASE_URL}/clients", json=client_data)
                if response.status_code == 200:
                    client = response.json()
                    self.created_entities['clients'].append(client['id'])
                    
                    # Verify branch_id is stored
                    if client.get('branch_id') == self.branch_ids['caxias']:
                        self.log_test("Client Branch Association", True, "Client correctly associated with branch")
                    else:
                        self.log_test("Client Branch Association", False, "Client not correctly associated with branch")
                else:
                    self.log_test("Client Branch Association", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Client Branch Association", False, f"Exception: {str(e)}")
    
    def cleanup_multi_branch_data(self):
        """Clean up multi-branch test data"""
        print("\n=== Cleaning Up Multi-Branch Test Data ===")
        
        # Delete test lawyers
        if 'super_admin' in self.auth_tokens:
            for lawyer_id in self.created_entities['lawyers']:
                try:
                    response = self.session.delete(f"{API_BASE_URL}/lawyers/{lawyer_id}",
                                                 headers={'Authorization': f'Bearer {self.auth_tokens["super_admin"]}'})
                    if response.status_code == 200:
                        print(f"✅ Deactivated lawyer: {lawyer_id}")
                    else:
                        print(f"❌ Failed to deactivate lawyer {lawyer_id}: {response.status_code}")
                except Exception as e:
                    print(f"❌ Exception deactivating lawyer {lawyer_id}: {str(e)}")
    
    def run_multi_branch_tests(self):
        """Run all multi-branch system tests"""
        print(f"🏢 Starting Multi-Branch System Tests")
        print("=" * 80)
        
        try:
            # Test multi-branch functionality
            self.test_multi_branch_system()
            self.test_branch_admin_authentication()
            self.test_lawyer_management_and_authentication()
            self.test_branch_data_isolation()
            
        finally:
            # Cleanup multi-branch data
            self.cleanup_multi_branch_data()
        
        return self.test_results
    
    def test_task_management_api(self):
        """Test Task Management API - New task system functionality"""
        print("\n=== Testing Task Management API ===")
        
        # Ensure we have authentication and lawyers
        if 'super_admin' not in self.auth_tokens:
            self.login_super_admin()
        
        if not self.created_entities['lawyers']:
            self.log_test("Task Management Prerequisites", False, "No lawyers available for task testing")
            return
        
        lawyer_id = self.created_entities['lawyers'][0]
        client_id = self.created_entities['clients'][0] if self.created_entities['clients'] else None
        process_id = self.created_entities['processes'][0] if self.created_entities['processes'] else None
        branch_id = self.branch_ids.get('caxias') or "some-branch-id"
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens["super_admin"]}'}
        
        # Test 1: Create Task
        task_data = {
            "title": "Revisar documentos do processo",
            "description": "Revisar todos os documentos relacionados ao processo de cobrança",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "priority": "high",
            "status": "pending",
            "assigned_lawyer_id": lawyer_id,
            "client_id": client_id,
            "process_id": process_id,
            "branch_id": branch_id
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/tasks", json=task_data, headers=auth_header)
            if response.status_code == 200:
                task = response.json()
                self.created_entities.setdefault('tasks', []).append(task['id'])
                self.log_test("Create Task", True, f"Created task: {task['title']}")
                
                # Verify task fields
                required_fields = ['id', 'title', 'due_date', 'priority', 'status', 'assigned_lawyer_id']
                missing_fields = [field for field in required_fields if field not in task]
                if missing_fields:
                    self.log_test("Task Fields Validation", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Task Fields Validation", True, "All required task fields present")
            else:
                self.log_test("Create Task", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Task", False, f"Exception: {str(e)}")
        
        # Test 2: Get All Tasks
        try:
            response = self.session.get(f"{API_BASE_URL}/tasks", headers=auth_header)
            if response.status_code == 200:
                tasks = response.json()
                self.log_test("Get All Tasks", True, f"Retrieved {len(tasks)} tasks")
            else:
                self.log_test("Get All Tasks", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Get All Tasks", False, f"Exception: {str(e)}")
        
        # Test 3: Get Lawyer's Agenda (if lawyer is logged in)
        if 'test_lawyer' in self.auth_tokens:
            lawyer_header = {'Authorization': f'Bearer {self.auth_tokens["test_lawyer"]}'}
            try:
                response = self.session.get(f"{API_BASE_URL}/tasks/my-agenda", headers=lawyer_header)
                if response.status_code == 200:
                    agenda_tasks = response.json()
                    self.log_test("Get Lawyer Agenda", True, f"Retrieved {len(agenda_tasks)} agenda tasks")
                else:
                    self.log_test("Get Lawyer Agenda", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Get Lawyer Agenda", False, f"Exception: {str(e)}")
        
        # Test 4: Update Task Status
        if hasattr(self, 'created_entities') and 'tasks' in self.created_entities and self.created_entities['tasks']:
            task_id = self.created_entities['tasks'][0]
            update_data = {
                "status": "in_progress",
                "priority": "medium"
            }
            try:
                response = self.session.put(f"{API_BASE_URL}/tasks/{task_id}", json=update_data, headers=auth_header)
                if response.status_code == 200:
                    updated_task = response.json()
                    if updated_task['status'] == "in_progress":
                        self.log_test("Update Task Status", True, "Task status updated successfully")
                    else:
                        self.log_test("Update Task Status", False, "Status update not reflected")
                else:
                    self.log_test("Update Task Status", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Update Task Status", False, f"Exception: {str(e)}")
    
    def test_contract_sequential_numbering(self):
        """Test Contract Sequential Numbering System"""
        print("\n=== Testing Contract Sequential Numbering ===")
        
        if not self.created_entities['clients']:
            self.log_test("Contract Numbering Prerequisites", False, "No clients available for contract testing")
            return
        
        client_id = self.created_entities['clients'][0]
        branch_id = self.branch_ids.get('caxias') or client_id
        
        # Test 1: Create multiple contracts and verify sequential numbering
        contract_numbers = []
        current_year = datetime.now().year
        
        for i in range(3):
            contract_data = {
                "client_id": client_id,
                "value": 10000.00 + (i * 1000),
                "payment_conditions": f"Pagamento em {i+1} parcelas",
                "installments": i + 1,
                "branch_id": branch_id
            }
            
            try:
                response = self.session.post(f"{API_BASE_URL}/contracts", json=contract_data)
                if response.status_code == 200:
                    contract = response.json()
                    self.created_entities['contracts'].append(contract['id'])
                    contract_numbers.append(contract['contract_number'])
                    self.log_test(f"Create Contract {i+1}", True, f"Created contract: {contract['contract_number']}")
                else:
                    self.log_test(f"Create Contract {i+1}", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test(f"Create Contract {i+1}", False, f"Exception: {str(e)}")
        
        # Test 2: Verify sequential numbering pattern
        if len(contract_numbers) >= 2:
            # Check if numbers follow CONT-YYYY-NNNN pattern
            pattern_valid = all(f"CONT-{current_year}-" in num for num in contract_numbers)
            if pattern_valid:
                self.log_test("Contract Number Pattern", True, f"All contracts follow CONT-{current_year}-NNNN pattern")
                
                # Check if numbers are sequential
                numbers = []
                for contract_num in contract_numbers:
                    try:
                        # Extract the sequential number part
                        seq_part = contract_num.split('-')[-1]
                        numbers.append(int(seq_part))
                    except:
                        pass
                
                if len(numbers) >= 2:
                    is_sequential = all(numbers[i] == numbers[i-1] + 1 for i in range(1, len(numbers)))
                    if is_sequential:
                        self.log_test("Contract Sequential Numbering", True, f"Contract numbers are sequential: {contract_numbers}")
                    else:
                        self.log_test("Contract Sequential Numbering", False, f"Numbers not sequential: {contract_numbers}")
                else:
                    self.log_test("Contract Sequential Numbering", False, "Could not extract sequential numbers")
            else:
                self.log_test("Contract Number Pattern", False, f"Invalid pattern in contract numbers: {contract_numbers}")
        else:
            self.log_test("Contract Sequential Numbering", False, "Not enough contracts created to test sequencing")
    
    def test_financial_access_control(self):
        """Test Financial Access Control based on lawyer permissions"""
        print("\n=== Testing Financial Access Control ===")
        
        # Test with restricted lawyer (access_financial_data=false)
        if 'restricted_lawyer' in self.auth_tokens:
            restricted_header = {'Authorization': f'Bearer {self.auth_tokens["restricted_lawyer"]}'}
            
            try:
                response = self.session.get(f"{API_BASE_URL}/financial", headers=restricted_header)
                if response.status_code == 403:
                    self.log_test("Restricted Lawyer Financial Access", True, "Correctly blocked access to financial data")
                else:
                    self.log_test("Restricted Lawyer Financial Access", False, f"Expected 403, got {response.status_code}")
            except Exception as e:
                self.log_test("Restricted Lawyer Financial Access", False, f"Exception: {str(e)}")
            
            # Test dashboard access (should show financial data as 0 or restricted)
            try:
                response = self.session.get(f"{API_BASE_URL}/dashboard", headers=restricted_header)
                if response.status_code == 200:
                    dashboard = response.json()
                    # For restricted lawyers, financial data should be 0 or restricted
                    if dashboard.get('total_revenue', 0) == 0 and dashboard.get('total_expenses', 0) == 0:
                        self.log_test("Restricted Lawyer Dashboard Access", True, "Dashboard shows restricted financial data")
                    else:
                        self.log_test("Restricted Lawyer Dashboard Access", False, "Dashboard shows financial data to restricted lawyer")
                else:
                    self.log_test("Restricted Lawyer Dashboard Access", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Restricted Lawyer Dashboard Access", False, f"Exception: {str(e)}")
        
        # Test with lawyer that has financial access
        if 'test_lawyer' in self.auth_tokens:
            lawyer_header = {'Authorization': f'Bearer {self.auth_tokens["test_lawyer"]}'}
            
            try:
                response = self.session.get(f"{API_BASE_URL}/financial", headers=lawyer_header)
                if response.status_code == 200:
                    self.log_test("Authorized Lawyer Financial Access", True, "Lawyer with financial access can view financial data")
                else:
                    self.log_test("Authorized Lawyer Financial Access", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Authorized Lawyer Financial Access", False, f"Exception: {str(e)}")
    
    def test_process_lawyer_assignment(self):
        """Test Process Management with responsible_lawyer_id field"""
        print("\n=== Testing Process Lawyer Assignment ===")
        
        if not self.created_entities['clients'] or not self.created_entities['lawyers']:
            self.log_test("Process Lawyer Assignment Prerequisites", False, "Missing clients or lawyers for testing")
            return
        
        client_id = self.created_entities['clients'][0]
        lawyer_id = self.created_entities['lawyers'][0]
        branch_id = self.branch_ids.get('caxias') or client_id
        
        # Test 1: Create Process with responsible lawyer
        process_data = {
            "client_id": client_id,
            "process_number": "0001234-56.2024.8.26.0200",
            "type": "Ação Trabalhista",
            "status": "Em Andamento",
            "value": 25000.00,
            "description": "Ação trabalhista com advogado responsável",
            "role": "creditor",
            "branch_id": branch_id,
            "responsible_lawyer_id": lawyer_id
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/processes", json=process_data)
            if response.status_code == 200:
                process = response.json()
                self.created_entities['processes'].append(process['id'])
                self.log_test("Create Process with Lawyer Assignment", True, f"Created process with lawyer: {process['id']}")
                
                # Verify lawyer assignment
                if process.get('responsible_lawyer_id') == lawyer_id:
                    self.log_test("Process Lawyer Assignment Verification", True, "Process correctly assigned to lawyer")
                else:
                    self.log_test("Process Lawyer Assignment Verification", False, "Process not correctly assigned to lawyer")
            else:
                self.log_test("Create Process with Lawyer Assignment", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Process with Lawyer Assignment", False, f"Exception: {str(e)}")
        
        # Test 2: Test lawyer can only see their assigned processes
        if 'test_lawyer' in self.auth_tokens:
            lawyer_header = {'Authorization': f'Bearer {self.auth_tokens["test_lawyer"]}'}
            
            try:
                response = self.session.get(f"{API_BASE_URL}/processes", headers=lawyer_header)
                if response.status_code == 200:
                    processes = response.json()
                    # Check if all processes belong to the lawyer
                    lawyer_processes = [p for p in processes if p.get('responsible_lawyer_id') == lawyer_id]
                    if len(lawyer_processes) == len(processes):
                        self.log_test("Lawyer Process Filtering", True, f"Lawyer sees only assigned processes: {len(processes)}")
                    else:
                        self.log_test("Lawyer Process Filtering", False, f"Lawyer sees unassigned processes: {len(processes)} total, {len(lawyer_processes)} assigned")
                else:
                    self.log_test("Lawyer Process Filtering", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Lawyer Process Filtering", False, f"Exception: {str(e)}")

    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n=== Cleaning Up Test Data ===")
        
        # Delete tasks
        if hasattr(self, 'created_entities') and 'tasks' in self.created_entities:
            for task_id in self.created_entities['tasks']:
                try:
                    response = self.session.delete(f"{API_BASE_URL}/tasks/{task_id}")
                    if response.status_code == 200:
                        print(f"✅ Deleted task: {task_id}")
                    else:
                        print(f"❌ Failed to delete task {task_id}: {response.status_code}")
                except Exception as e:
                    print(f"❌ Exception deleting task {task_id}: {str(e)}")
        
        # Delete contracts
        for contract_id in self.created_entities['contracts']:
            try:
                response = self.session.delete(f"{API_BASE_URL}/contracts/{contract_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted contract: {contract_id}")
                else:
                    print(f"❌ Failed to delete contract {contract_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Exception deleting contract {contract_id}: {str(e)}")
        
        # Delete financial transactions
        for transaction_id in self.created_entities['financial_transactions']:
            try:
                response = self.session.delete(f"{API_BASE_URL}/financial/{transaction_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted transaction: {transaction_id}")
                else:
                    print(f"❌ Failed to delete transaction {transaction_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Exception deleting transaction {transaction_id}: {str(e)}")
        
        # Delete processes
        for process_id in self.created_entities['processes']:
            try:
                response = self.session.delete(f"{API_BASE_URL}/processes/{process_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted process: {process_id}")
                else:
                    print(f"❌ Failed to delete process {process_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Exception deleting process {process_id}: {str(e)}")
        
        # Delete clients
        for client_id in self.created_entities['clients']:
            try:
                response = self.session.delete(f"{API_BASE_URL}/clients/{client_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted client: {client_id}")
                else:
                    print(f"❌ Failed to delete client {client_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Exception deleting client {client_id}: {str(e)}")
    
    def test_whatsapp_integration_api(self):
        """Test WhatsApp Business Integration API - Payment reminders and messaging"""
        print("\n=== Testing WhatsApp Business Integration API ===")
        
        # Ensure we have authentication
        if 'super_admin' not in self.auth_tokens:
            self.login_super_admin()
        
        if not self.auth_tokens.get('super_admin'):
            self.log_test("WhatsApp Integration Prerequisites", False, "No admin authentication available")
            return
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens["super_admin"]}'}
        
        # Test 1: Get WhatsApp Status
        try:
            response = self.session.get(f"{API_BASE_URL}/whatsapp/status", headers=auth_header)
            if response.status_code == 200:
                status_data = response.json()
                self.log_test("WhatsApp Status Endpoint", True, "Retrieved WhatsApp service status")
                
                # Verify status structure
                required_fields = ['whatsapp_enabled', 'scheduler_running', 'jobs']
                missing_fields = [field for field in required_fields if field not in status_data]
                if missing_fields:
                    self.log_test("WhatsApp Status Structure", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("WhatsApp Status Structure", True, "All required status fields present")
                    
                # Log status details
                print(f"   📱 WhatsApp Enabled: {status_data.get('whatsapp_enabled')}")
                print(f"   ⏰ Scheduler Running: {status_data.get('scheduler_running')}")
                print(f"   📋 Jobs Count: {len(status_data.get('jobs', []))}")
                
                # Verify scheduler jobs
                jobs = status_data.get('jobs', [])
                if jobs:
                    job_names = [job.get('name', '') for job in jobs]
                    expected_jobs = ['Verificação diária de pagamentos', 'Verificação vespertina de pagamentos']
                    jobs_found = [name for name in expected_jobs if any(name in job_name for job_name in job_names)]
                    
                    if len(jobs_found) >= 2:
                        self.log_test("WhatsApp Scheduler Jobs", True, f"Found payment verification jobs: {len(jobs_found)}")
                    else:
                        self.log_test("WhatsApp Scheduler Jobs", False, f"Expected 2 jobs, found: {jobs_found}")
                else:
                    self.log_test("WhatsApp Scheduler Jobs", False, "No scheduler jobs found")
                    
            else:
                self.log_test("WhatsApp Status Endpoint", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("WhatsApp Status Endpoint", False, f"Exception: {str(e)}")
        
        # Test 2: Send Custom WhatsApp Message
        custom_message_data = {
            "phone_number": "(11) 99999-8888",
            "message": "Teste de mensagem personalizada do sistema GB & N.Comin Advocacia"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/whatsapp/send-message", 
                                       json=custom_message_data, headers=auth_header)
            if response.status_code == 200:
                message_result = response.json()
                self.log_test("WhatsApp Send Custom Message", True, "Custom message sent successfully")
                
                # Verify response structure
                if 'message' in message_result:
                    self.log_test("WhatsApp Message Response Structure", True, "Response contains success message")
                else:
                    self.log_test("WhatsApp Message Response Structure", False, "Response missing success message")
            else:
                self.log_test("WhatsApp Send Custom Message", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("WhatsApp Send Custom Message", False, f"Exception: {str(e)}")
        
        # Test 3: Send Manual Payment Reminder (requires transaction)
        if self.created_entities['financial_transactions']:
            transaction_id = self.created_entities['financial_transactions'][0]
            
            try:
                response = self.session.post(f"{API_BASE_URL}/whatsapp/send-reminder/{transaction_id}", 
                                           headers=auth_header)
                if response.status_code == 200:
                    reminder_result = response.json()
                    self.log_test("WhatsApp Manual Payment Reminder", True, "Manual payment reminder sent successfully")
                    
                    # Verify response structure
                    if 'message' in reminder_result:
                        self.log_test("WhatsApp Reminder Response Structure", True, "Response contains success message")
                    else:
                        self.log_test("WhatsApp Reminder Response Structure", False, "Response missing success message")
                else:
                    self.log_test("WhatsApp Manual Payment Reminder", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("WhatsApp Manual Payment Reminder", False, f"Exception: {str(e)}")
        else:
            self.log_test("WhatsApp Manual Payment Reminder", False, "No financial transactions available for testing")
        
        # Test 4: Trigger Payment Check (Admin only)
        try:
            response = self.session.post(f"{API_BASE_URL}/whatsapp/check-payments", headers=auth_header)
            if response.status_code == 200:
                check_result = response.json()
                self.log_test("WhatsApp Trigger Payment Check", True, "Payment check triggered successfully")
                
                # Verify response structure
                if 'message' in check_result:
                    self.log_test("WhatsApp Payment Check Response", True, "Response contains success message")
                else:
                    self.log_test("WhatsApp Payment Check Response", False, "Response missing success message")
            else:
                self.log_test("WhatsApp Trigger Payment Check", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("WhatsApp Trigger Payment Check", False, f"Exception: {str(e)}")
        
        # Test 5: Test Authentication Requirements (try with lawyer token if available)
        if 'test_lawyer' in self.auth_tokens:
            lawyer_header = {'Authorization': f'Bearer {self.auth_tokens["test_lawyer"]}'}
            
            try:
                # Lawyer should be able to access status
                response = self.session.get(f"{API_BASE_URL}/whatsapp/status", headers=lawyer_header)
                if response.status_code == 200:
                    self.log_test("WhatsApp Lawyer Access - Status", True, "Lawyer can access WhatsApp status")
                else:
                    self.log_test("WhatsApp Lawyer Access - Status", False, f"HTTP {response.status_code}")
                
                # Lawyer should NOT be able to trigger payment checks (admin only)
                response = self.session.post(f"{API_BASE_URL}/whatsapp/check-payments", headers=lawyer_header)
                if response.status_code == 403:
                    self.log_test("WhatsApp Admin-Only Access Control", True, "Correctly blocked lawyer from admin-only endpoint")
                else:
                    self.log_test("WhatsApp Admin-Only Access Control", False, f"Expected 403, got {response.status_code}")
                    
            except Exception as e:
                self.log_test("WhatsApp Authentication Tests", False, f"Exception: {str(e)}")
        
        # Test 6: Test Invalid Requests
        # Test with invalid transaction ID
        try:
            response = self.session.post(f"{API_BASE_URL}/whatsapp/send-reminder/invalid-id", 
                                       headers=auth_header)
            if response.status_code == 400:
                self.log_test("WhatsApp Invalid Transaction ID", True, "Correctly rejected invalid transaction ID")
            else:
                self.log_test("WhatsApp Invalid Transaction ID", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("WhatsApp Invalid Transaction ID", False, f"Exception: {str(e)}")
        
        # Test with missing message data
        try:
            response = self.session.post(f"{API_BASE_URL}/whatsapp/send-message", 
                                       json={"phone_number": "(11) 99999-8888"}, # Missing message
                                       headers=auth_header)
            if response.status_code == 400:
                self.log_test("WhatsApp Missing Message Data", True, "Correctly rejected incomplete message data")
            else:
                self.log_test("WhatsApp Missing Message Data", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("WhatsApp Missing Message Data", False, f"Exception: {str(e)}")

    def test_whatsapp_integration_fixes(self):
        """Test WhatsApp Integration Fixes - Focus on endpoints that were returning 404"""
        print("\n=== Testing WhatsApp Integration Fixes ===")
        
        # Ensure we have authentication
        if 'super_admin' not in self.auth_tokens:
            self.login_super_admin()
        
        admin_header = {'Authorization': f'Bearer {self.auth_tokens["super_admin"]}'}
        
        # Test 1: GET /api/whatsapp/status (should now work, not 404)
        try:
            response = self.session.get(f"{API_BASE_URL}/whatsapp/status", headers=admin_header)
            if response.status_code == 200:
                status_data = response.json()
                self.log_test("WhatsApp Status Endpoint Fix", True, f"Status endpoint accessible: {status_data.get('service_status', 'unknown')}")
                
                # Verify expected fields in response
                expected_fields = ['service_status', 'whatsapp_enabled', 'mode', 'phone_number', 'scheduler_jobs']
                missing_fields = [field for field in expected_fields if field not in status_data]
                if missing_fields:
                    self.log_test("WhatsApp Status Response Fields", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("WhatsApp Status Response Fields", True, "All expected status fields present")
                    
                # Verify scheduler info
                if 'scheduler_jobs' in status_data and len(status_data['scheduler_jobs']) >= 2:
                    self.log_test("WhatsApp Scheduler Jobs", True, f"Found {len(status_data['scheduler_jobs'])} scheduler jobs")
                else:
                    self.log_test("WhatsApp Scheduler Jobs", False, "Expected scheduler jobs not found")
                    
            elif response.status_code == 404:
                self.log_test("WhatsApp Status Endpoint Fix", False, "Still returning 404 - endpoint not found")
            else:
                self.log_test("WhatsApp Status Endpoint Fix", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("WhatsApp Status Endpoint Fix", False, f"Exception: {str(e)}")
        
        # Test 2: POST /api/whatsapp/send-message (should now work, not 404)
        message_data = {
            "phone_number": "+55 54 99710-2525",
            "message": "Teste de mensagem WhatsApp - Sistema GB Advocacia"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/whatsapp/send-message", json=message_data, headers=admin_header)
            if response.status_code == 200:
                result = response.json()
                self.log_test("WhatsApp Send Message Endpoint Fix", True, f"Message endpoint accessible: {result.get('success', False)}")
                
                # Verify response structure
                if result.get('success') and 'simulated' in result:
                    self.log_test("WhatsApp Message Response", True, f"Message sent (simulated: {result.get('simulated', False)})")
                else:
                    self.log_test("WhatsApp Message Response", False, "Unexpected response structure")
                    
            elif response.status_code == 404:
                self.log_test("WhatsApp Send Message Endpoint Fix", False, "Still returning 404 - endpoint not found")
            else:
                self.log_test("WhatsApp Send Message Endpoint Fix", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("WhatsApp Send Message Endpoint Fix", False, f"Exception: {str(e)}")
        
        # Test 3: POST /api/whatsapp/check-payments (admin-only bulk verification)
        try:
            response = self.session.post(f"{API_BASE_URL}/whatsapp/check-payments", headers=admin_header)
            if response.status_code == 200:
                result = response.json()
                self.log_test("WhatsApp Check Payments Endpoint Fix", True, f"Bulk check endpoint accessible")
                
                # Verify response structure
                expected_fields = ['checked_transactions', 'reminders_sent', 'simulated']
                if all(field in result for field in expected_fields):
                    self.log_test("WhatsApp Bulk Check Response", True, f"Checked {result.get('checked_transactions', 0)} transactions")
                else:
                    self.log_test("WhatsApp Bulk Check Response", False, "Missing expected response fields")
                    
            elif response.status_code == 404:
                self.log_test("WhatsApp Check Payments Endpoint Fix", False, "Still returning 404 - endpoint not found")
            else:
                self.log_test("WhatsApp Check Payments Endpoint Fix", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("WhatsApp Check Payments Endpoint Fix", False, f"Exception: {str(e)}")
        
        # Test 4: POST /api/whatsapp/send-reminder/{transaction_id} (manual payment reminder)
        # First create a transaction to test with
        if self.created_entities['financial_transactions']:
            transaction_id = self.created_entities['financial_transactions'][0]
            
            try:
                response = self.session.post(f"{API_BASE_URL}/whatsapp/send-reminder/{transaction_id}", headers=admin_header)
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("WhatsApp Send Reminder Endpoint Fix", True, f"Manual reminder endpoint accessible")
                    
                    # Verify response structure
                    expected_fields = ['success', 'client_name', 'phone_number', 'transaction_id']
                    if all(field in result for field in expected_fields):
                        self.log_test("WhatsApp Reminder Response", True, f"Reminder sent to {result.get('client_name', 'unknown')}")
                    else:
                        self.log_test("WhatsApp Reminder Response", False, "Missing expected response fields")
                        
                elif response.status_code == 404:
                    self.log_test("WhatsApp Send Reminder Endpoint Fix", False, "Still returning 404 - endpoint not found")
                else:
                    self.log_test("WhatsApp Send Reminder Endpoint Fix", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("WhatsApp Send Reminder Endpoint Fix", False, f"Exception: {str(e)}")
        else:
            self.log_test("WhatsApp Send Reminder Endpoint Fix", False, "No transaction available for testing")
        
        # Test 5: Test lawyer access (should work for status and send-message)
        if 'test_lawyer' in self.auth_tokens:
            lawyer_header = {'Authorization': f'Bearer {self.auth_tokens["test_lawyer"]}'}
            
            try:
                response = self.session.get(f"{API_BASE_URL}/whatsapp/status", headers=lawyer_header)
                if response.status_code == 200:
                    self.log_test("WhatsApp Lawyer Access - Status Fix", True, "Lawyers can access WhatsApp status")
                else:
                    self.log_test("WhatsApp Lawyer Access - Status Fix", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("WhatsApp Lawyer Access - Status Fix", False, f"Exception: {str(e)}")
            
            # Test lawyer cannot access admin-only bulk check
            try:
                response = self.session.post(f"{API_BASE_URL}/whatsapp/check-payments", headers=lawyer_header)
                if response.status_code == 403:
                    self.log_test("WhatsApp Lawyer Access Control Fix", True, "Lawyers correctly blocked from admin-only bulk check")
                else:
                    self.log_test("WhatsApp Lawyer Access Control Fix", False, f"Expected 403, got {response.status_code}")
            except Exception as e:
                self.log_test("WhatsApp Lawyer Access Control Fix", False, f"Exception: {str(e)}")

    def test_google_drive_integration_fixes(self):
        """Test Google Drive Integration Fixes - Focus on better error handling"""
        print("\n=== Testing Google Drive Integration Fixes ===")
        
        # Ensure we have authentication
        if 'super_admin' not in self.auth_tokens:
            self.login_super_admin()
        
        admin_header = {'Authorization': f'Bearer {self.auth_tokens["super_admin"]}'}
        
        # Test 1: GET /api/google-drive/status (should provide clear error about missing credentials)
        try:
            response = self.session.get(f"{API_BASE_URL}/google-drive/status", headers=admin_header)
            if response.status_code == 200:
                status_data = response.json()
                self.log_test("Google Drive Status Endpoint Fix", True, "Status endpoint accessible")
                
                # Verify expected fields in response
                expected_fields = ['configured', 'credentials_file_exists', 'service_available', 'message']
                missing_fields = [field for field in expected_fields if field not in status_data]
                if missing_fields:
                    self.log_test("Google Drive Status Response Fields", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Google Drive Status Response Fields", True, "All expected status fields present")
                
                # Verify clear error message about missing credentials
                if not status_data.get('configured', True):
                    message = status_data.get('message', '')
                    if 'google_credentials.json' in message.lower():
                        self.log_test("Google Drive Error Message Fix", True, "Clear error message about missing credentials file")
                    else:
                        self.log_test("Google Drive Error Message Fix", False, f"Unclear error message: {message}")
                else:
                    self.log_test("Google Drive Configuration Check", True, "Google Drive appears to be configured")
                    
            else:
                self.log_test("Google Drive Status Endpoint Fix", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Google Drive Status Endpoint Fix", False, f"Exception: {str(e)}")
        
        # Test 2: GET /api/google-drive/auth-url (should provide clear error about missing credentials)
        try:
            response = self.session.get(f"{API_BASE_URL}/google-drive/auth-url", headers=admin_header)
            if response.status_code == 400:
                error_data = response.json()
                error_detail = error_data.get('detail', '')
                if 'google_credentials.json' in error_detail.lower():
                    self.log_test("Google Drive Auth URL Error Handling Fix", True, "Clear error message about missing credentials file")
                else:
                    self.log_test("Google Drive Auth URL Error Handling Fix", False, f"Unclear error message: {error_detail}")
            elif response.status_code == 200:
                # If credentials exist, this should work
                auth_data = response.json()
                if 'authorization_url' in auth_data:
                    self.log_test("Google Drive Auth URL Generation", True, "Authorization URL generated successfully")
                else:
                    self.log_test("Google Drive Auth URL Generation", False, "Missing authorization_url in response")
            else:
                self.log_test("Google Drive Auth URL Error Handling Fix", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Google Drive Auth URL Error Handling Fix", False, f"Exception: {str(e)}")
        
        # Test 3: POST /api/google-drive/generate-procuracao (test error handling)
        if self.created_entities['clients']:
            client_id = self.created_entities['clients'][0]
            procuracao_data = {
                "client_id": client_id,
                "process_id": self.created_entities['processes'][0] if self.created_entities['processes'] else None
            }
            
            try:
                response = self.session.post(f"{API_BASE_URL}/google-drive/generate-procuracao", 
                                           json=procuracao_data, headers=admin_header)
                if response.status_code == 500:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'google' in error_detail.lower() or 'drive' in error_detail.lower():
                        self.log_test("Google Drive Document Generation Error Fix", True, "Clear error message about Google Drive configuration")
                    else:
                        self.log_test("Google Drive Document Generation Error Fix", False, f"Unclear error message: {error_detail}")
                elif response.status_code == 200:
                    # If credentials exist and configured, this should work
                    result = response.json()
                    if 'drive_link' in result:
                        self.log_test("Google Drive Document Generation", True, "Document generated successfully")
                    else:
                        self.log_test("Google Drive Document Generation", False, "Missing drive_link in response")
                else:
                    self.log_test("Google Drive Document Generation Error Fix", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Google Drive Document Generation Error Fix", False, f"Exception: {str(e)}")
        else:
            self.log_test("Google Drive Document Generation", False, "No client available for testing")
        
        # Test 4: GET /api/google-drive/client-documents/{client_id} (test error handling)
        if self.created_entities['clients']:
            client_id = self.created_entities['clients'][0]
            
            try:
                response = self.session.get(f"{API_BASE_URL}/google-drive/client-documents/{client_id}", headers=admin_header)
                if response.status_code == 500:
                    error_data = response.json()
                    error_detail = error_data.get('detail', '')
                    if 'google' in error_detail.lower() or 'drive' in error_detail.lower():
                        self.log_test("Google Drive Client Documents Error Fix", True, "Clear error message about Google Drive configuration")
                    else:
                        self.log_test("Google Drive Client Documents Error Fix", False, f"Unclear error message: {error_detail}")
                elif response.status_code == 200:
                    # If credentials exist and configured, this should work
                    documents = response.json()
                    if isinstance(documents, list):
                        self.log_test("Google Drive Client Documents", True, f"Retrieved {len(documents)} client documents")
                    else:
                        self.log_test("Google Drive Client Documents", False, "Invalid response format")
                else:
                    self.log_test("Google Drive Client Documents Error Fix", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Google Drive Client Documents Error Fix", False, f"Exception: {str(e)}")
        else:
            self.log_test("Google Drive Client Documents", False, "No client available for testing")
        
        # Test 5: Test admin-only access control
        if 'test_lawyer' in self.auth_tokens:
            lawyer_header = {'Authorization': f'Bearer {self.auth_tokens["test_lawyer"]}'}
            
            try:
                response = self.session.get(f"{API_BASE_URL}/google-drive/status", headers=lawyer_header)
                if response.status_code == 403:
                    self.log_test("Google Drive Access Control Fix", True, "Non-admin users correctly blocked from Google Drive endpoints")
                else:
                    self.log_test("Google Drive Access Control Fix", False, f"Expected 403, got {response.status_code}")
            except Exception as e:
                self.log_test("Google Drive Access Control Fix", False, f"Exception: {str(e)}")

    def run_integration_fixes_tests(self):
        """Run focused tests on WhatsApp and Google Drive integration fixes"""
        print(f"🔧 Starting Integration Fixes Tests for GB Advocacia System")
        print(f"🌐 Backend URL: {API_BASE_URL}")
        print("=" * 80)
        
        try:
            # Login as super admin first
            if not self.login_super_admin():
                print("❌ Failed to login as super admin. Cannot proceed with tests.")
                return self.test_results
            
            # Create minimal test data needed for integration tests
            self.test_client_management_api()  # Create clients
            self.test_financial_transaction_api()  # Create transactions for WhatsApp testing
            self.test_lawyer_management_and_authentication()  # Create lawyers for access control testing
            
            # Run integration fix tests
            self.test_whatsapp_integration_fixes()
            self.test_google_drive_integration_fixes()
            
            # Verify core database functionality still works
            self.test_dashboard_statistics_api()
            
        finally:
            # Cleanup created entities
            self.cleanup_test_data()
        
        # Print final results
        print("\n" + "=" * 80)
        print("🏁 INTEGRATION FIXES TEST RESULTS")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = sum(1 for result in self.test_results if not result['success'])
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total: {total}")
        print(f"📈 Success Rate: {(passed/total*100):.1f}%" if total > 0 else "No tests run")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['message']}")
        
        return self.test_results

    def run_all_tests(self):
        """Run all backend API tests including multi-branch system and WhatsApp integration"""
        print(f"🚀 Starting Backend API Tests for GB Advocacia & N. Comin")
        print(f"📡 Backend URL: {API_BASE_URL}")
        print("=" * 80)
        
        try:
            # First test multi-branch system (this sets up authentication)
            self.run_multi_branch_tests()
            
            # Then test all other APIs
            self.test_client_management_api()
            self.test_process_management_api()
            self.test_financial_transaction_api()
            self.test_contract_management_api()
            self.test_dashboard_statistics_api()
            self.test_data_relationships()
            
            # Test WhatsApp integration
            self.test_whatsapp_integration_api()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Print final results
        print("\n" + "=" * 80)
        print("🏁 FINAL TEST RESULTS")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = sum(1 for result in self.test_results if not result['success'])
        total = len(self.test_results)
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Total: {total}")
        print(f"📈 Success Rate: {(passed/total*100):.1f}%" if total > 0 else "No tests run")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['message']}")
        
        return passed, failed, total

def main():
    """Main function to run backend tests"""
    tester = BackendTester()
    passed, failed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()