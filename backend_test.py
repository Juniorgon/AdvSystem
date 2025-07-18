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
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://24f1403a-bc3b-4496-bd05-3323ddc4dbee.preview.emergentagent.com')
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
            'contracts': []
        }
        
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
            "client_type": "individual"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/clients", json=individual_client_data)
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
            "client_type": "corporate"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/clients", json=corporate_client_data)
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
            response = self.session.get(f"{API_BASE_URL}/clients")
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
            "role": "creditor"
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
            "role": "debtor"
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
            "category": "Honorários"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/financial", json=revenue_data)
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
            "category": "Custas Processuais"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/financial", json=expense_data)
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
            "category": "Honorários"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/financial", json=overdue_data)
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
            "installments": 5
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
            "installments": 1
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
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n=== Cleaning Up Test Data ===")
        
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
    
    def run_all_tests(self):
        """Run all backend API tests"""
        print(f"🚀 Starting Backend API Tests for GB Advocacia & N. Comin")
        print(f"📡 Backend URL: {API_BASE_URL}")
        print("=" * 80)
        
        try:
            # Test all APIs
            self.test_client_management_api()
            self.test_process_management_api()
            self.test_financial_transaction_api()
            self.test_contract_management_api()
            self.test_dashboard_statistics_api()
            self.test_data_relationships()
            
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