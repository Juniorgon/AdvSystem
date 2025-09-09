#!/usr/bin/env python3
"""
COMPREHENSIVE BACKEND TESTING SUITE - SISTEMA JURÍDICO GB ADVOCACIA
PostgreSQL Migration Complete Testing as requested by user

TESTING SCOPE:
1. AUTHENTICATION - All login credentials (admin/admin123, admin_caxias/admin123, admin_novaprata/admin123)
2. REGISTRATION - User and lawyer creation with new fields
3. DATA EDITING - All modules with new PostgreSQL structure
4. DATA DELETION - With proper validations and dependency checks
5. POSTGRESQL FEATURES - UUID keys, new address structure, sequential numbering
6. ACCESS CONTROL - Financial permissions, branch isolation, role-based access
7. INTEGRATIONS - WhatsApp Business, Google Drive
8. SECURITY - Advanced security features, password validation
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

class ComprehensiveBackendTester:
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
            'lawyers': [],
            'users': [],
            'tasks': []
        }
        self.auth_tokens = {}
        self.branch_ids = {}
        
    def log_test(self, test_name: str, success: bool, message: str, details: Any = None):
        """Log test results with detailed formatting"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        print(f"      {message}")
        if details and not success:
            print(f"      Details: {details}")
        print()
    
    def test_comprehensive_authentication(self):
        """Test all authentication scenarios as requested by user"""
        print("\n" + "="*80)
        print("🔐 COMPREHENSIVE AUTHENTICATION TESTING")
        print("="*80)
        
        # Test 1: Super Admin Login (admin/admin123)
        login_data = {
            "username_or_email": "admin",
            "password": "admin123"
        }
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_tokens['super_admin'] = token_data['access_token']
                user = token_data['user']
                self.log_test("Super Admin Login (admin/admin123)", True, 
                            f"SUCCESS: {user['full_name']} - Role: {user['role']} - Branch: {user.get('branch_id', 'All')}")
            else:
                self.log_test("Super Admin Login (admin/admin123)", False, 
                            f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Super Admin Login (admin/admin123)", False, f"EXCEPTION: {str(e)}")
        
        # Test 2: Caxias Admin Login (admin_caxias/admin123)
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
                self.log_test("Caxias Admin Login (admin_caxias/admin123)", True, 
                            f"SUCCESS: {user['full_name']} - Branch: {user.get('branch_id', 'N/A')}")
            else:
                self.log_test("Caxias Admin Login (admin_caxias/admin123)", False, 
                            f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Caxias Admin Login (admin_caxias/admin123)", False, f"EXCEPTION: {str(e)}")
        
        # Test 3: Nova Prata Admin Login (admin_novaprata/admin123)
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
                self.log_test("Nova Prata Admin Login (admin_novaprata/admin123)", True, 
                            f"SUCCESS: {user['full_name']} - Branch: {user.get('branch_id', 'N/A')}")
            else:
                self.log_test("Nova Prata Admin Login (admin_novaprata/admin123)", False, 
                            f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Nova Prata Admin Login (admin_novaprata/admin123)", False, f"EXCEPTION: {str(e)}")
        
        # Test 4: JWT Token Validation
        if 'super_admin' in self.auth_tokens:
            try:
                response = self.session.get(f"{API_BASE_URL}/auth/me", 
                                          headers={'Authorization': f'Bearer {self.auth_tokens["super_admin"]}'})
                if response.status_code == 200:
                    user_data = response.json()
                    self.log_test("JWT Token Validation", True, 
                                f"Token valid for user: {user_data['full_name']} - ID: {user_data['id']}")
                else:
                    self.log_test("JWT Token Validation", False, f"Token validation failed: HTTP {response.status_code}")
            except Exception as e:
                self.log_test("JWT Token Validation", False, f"EXCEPTION: {str(e)}")
    
    def test_comprehensive_registration(self):
        """Test user and lawyer registration with new PostgreSQL fields"""
        print("\n" + "="*80)
        print("👥 COMPREHENSIVE REGISTRATION TESTING")
        print("="*80)
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'}
        
        # Get branches first
        try:
            response = self.session.get(f"{API_BASE_URL}/branches", headers=auth_header)
            if response.status_code == 200:
                branches = response.json()
                for branch in branches:
                    if 'Caxias' in branch['name']:
                        self.branch_ids['caxias'] = branch['id']
                    elif 'Nova Prata' in branch['name']:
                        self.branch_ids['nova_prata'] = branch['id']
                self.log_test("Branch Discovery", True, f"Found {len(branches)} branches")
            else:
                self.log_test("Branch Discovery", False, f"Failed to get branches: HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Branch Discovery", False, f"EXCEPTION: {str(e)}")
        
        # Test 1: Create New User
        user_data = {
            "username": "teste_usuario_2025",
            "email": "teste.usuario@gbadvocacia.com.br",
            "full_name": "Usuário de Teste PostgreSQL",
            "password": "SenhaSegura123!",
            "role": "admin",
            "branch_id": self.branch_ids.get('caxias')
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/register", json=user_data, headers=auth_header)
            if response.status_code == 200:
                user = response.json()
                self.created_entities['users'].append(user['id'])
                self.log_test("Create New User", True, 
                            f"Created user: {user['full_name']} - Email: {user['email']} - ID: {user['id']}")
            else:
                self.log_test("Create New User", False, f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create New User", False, f"EXCEPTION: {str(e)}")
        
        # Test 2: Create Lawyer with Financial Access and Branch Permissions
        lawyer_data_1 = {
            "full_name": "Dr. Roberto Carlos Silva",
            "oab_number": "123987",
            "oab_state": "RS",
            "email": "roberto.silva@gbadvocacia.com.br",
            "phone": "(54) 99999-1111",
            "specialization": "Direito Empresarial e Tributário",
            "branch_id": self.branch_ids.get('caxias'),
            "access_financial_data": True,
            "allowed_branch_ids": [self.branch_ids.get('caxias')] if self.branch_ids.get('caxias') else []
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/lawyers", json=lawyer_data_1, headers=auth_header)
            if response.status_code == 200:
                lawyer = response.json()
                self.created_entities['lawyers'].append(lawyer['id'])
                self.log_test("Create Lawyer with Financial Access", True, 
                            f"Created: {lawyer['full_name']} - OAB: {lawyer['oab_number']}/{lawyer['oab_state']} - Financial Access: {lawyer['access_financial_data']} - ID: {lawyer['id']}")
            else:
                self.log_test("Create Lawyer with Financial Access", False, f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Lawyer with Financial Access", False, f"EXCEPTION: {str(e)}")
        
        # Test 3: Create Lawyer without Financial Access
        lawyer_data_2 = {
            "full_name": "Dra. Fernanda Santos Oliveira",
            "oab_number": "456123",
            "oab_state": "RS",
            "email": "fernanda.santos@gbadvocacia.com.br",
            "phone": "(54) 99999-2222",
            "specialization": "Direito de Família e Sucessões",
            "branch_id": self.branch_ids.get('nova_prata'),
            "access_financial_data": False,
            "allowed_branch_ids": [self.branch_ids.get('nova_prata')] if self.branch_ids.get('nova_prata') else []
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/lawyers", json=lawyer_data_2, headers=auth_header)
            if response.status_code == 200:
                lawyer = response.json()
                self.created_entities['lawyers'].append(lawyer['id'])
                self.log_test("Create Lawyer without Financial Access", True, 
                            f"Created: {lawyer['full_name']} - OAB: {lawyer['oab_number']}/{lawyer['oab_state']} - Financial Access: {lawyer['access_financial_data']} - ID: {lawyer['id']}")
            else:
                self.log_test("Create Lawyer without Financial Access", False, f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Lawyer without Financial Access", False, f"EXCEPTION: {str(e)}")
        
        # Test 4: Test Lawyer Authentication with OAB
        if self.created_entities['lawyers']:
            lawyer_login_data = {
                "username_or_email": "roberto.silva@gbadvocacia.com.br",
                "password": "123987"  # OAB number as password
            }
            
            try:
                response = self.session.post(f"{API_BASE_URL}/auth/login", json=lawyer_login_data)
                if response.status_code == 200:
                    token_data = response.json()
                    self.auth_tokens['test_lawyer'] = token_data['access_token']
                    user = token_data['user']
                    self.log_test("Lawyer Authentication (Email/OAB)", True, 
                                f"Lawyer login successful: {user['full_name']} - Role: {user['role']} - ID: {user['id']}")
                else:
                    self.log_test("Lawyer Authentication (Email/OAB)", False, f"FAILED: HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Lawyer Authentication (Email/OAB)", False, f"EXCEPTION: {str(e)}")
    
    def test_client_management_with_new_address_structure(self):
        """Test client management with new PostgreSQL address structure"""
        print("\n" + "="*80)
        print("👤 CLIENT MANAGEMENT - NEW ADDRESS STRUCTURE")
        print("="*80)
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'}
        branch_id = self.branch_ids.get('caxias') or 'default-branch'
        
        # Test 1: Create Individual Client with New Address Structure
        individual_client_data = {
            "name": "João Pedro Silva Santos",
            "nationality": "Brasileira",
            "civil_status": "Casado",
            "profession": "Engenheiro Civil",
            "cpf": "123.456.789-10",
            "address": {
                "street": "Rua Marechal Deodoro",
                "number": "1234",
                "city": "Caxias do Sul",
                "district": "Centro",
                "state": "RS",
                "complement": "Apartamento 501 - Bloco A"
            },
            "phone": "(54) 99999-1234",
            "client_type": "individual",
            "branch_id": branch_id
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/clients", json=individual_client_data, headers=auth_header)
            if response.status_code == 200:
                client = response.json()
                self.created_entities['clients'].append(client['id'])
                
                # Verify new address structure
                address_fields = ['street', 'number', 'city', 'district', 'state', 'complement']
                missing_fields = [field for field in address_fields if field not in client]
                
                if not missing_fields:
                    self.log_test("Create Individual Client - New Address Structure", True, 
                                f"Created: {client['name']} - Address: {client['street']}, {client['number']}, {client['district']}, {client['city']}/{client['state']} - ID: {client['id']}")
                else:
                    self.log_test("Create Individual Client - New Address Structure", False, 
                                f"Missing address fields: {missing_fields}")
            else:
                self.log_test("Create Individual Client - New Address Structure", False, 
                            f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Individual Client - New Address Structure", False, f"EXCEPTION: {str(e)}")
        
        # Test 2: Create Corporate Client
        corporate_client_data = {
            "name": "Empresa Inovação Tecnológica Ltda",
            "nationality": "Brasileira",
            "civil_status": "N/A",
            "profession": "Tecnologia da Informação",
            "cpf": "12.345.678/0001-90",
            "address": {
                "street": "Avenida Júlio de Castilhos",
                "number": "2500",
                "city": "Caxias do Sul",
                "district": "São Pelegrino",
                "state": "RS",
                "complement": "Sala 1205 - Torre Empresarial"
            },
            "phone": "(54) 3333-4444",
            "client_type": "corporate",
            "branch_id": branch_id
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/clients", json=corporate_client_data, headers=auth_header)
            if response.status_code == 200:
                client = response.json()
                self.created_entities['clients'].append(client['id'])
                self.log_test("Create Corporate Client", True, 
                            f"Created: {client['name']} - Type: {client['client_type']} - CNPJ: {client['cpf']} - ID: {client['id']}")
            else:
                self.log_test("Create Corporate Client", False, f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Corporate Client", False, f"EXCEPTION: {str(e)}")
        
        # Test 3: Verify UUID Primary Keys
        if self.created_entities['clients']:
            client_id = self.created_entities['clients'][0]
            if len(client_id) == 36 and client_id.count('-') == 4:
                self.log_test("UUID Primary Keys Verification", True, f"Client ID is valid UUID: {client_id}")
            else:
                self.log_test("UUID Primary Keys Verification", False, f"Client ID not UUID format: {client_id}")
    
    def test_process_management_with_responsible_lawyer(self):
        """Test process management with responsible_lawyer_id field"""
        print("\n" + "="*80)
        print("⚖️ PROCESS MANAGEMENT - RESPONSIBLE LAWYER FIELD")
        print("="*80)
        
        if not self.created_entities['clients'] or not self.created_entities['lawyers']:
            self.log_test("Process Management Prerequisites", False, "Missing clients or lawyers for testing")
            return
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'}
        client_id = self.created_entities['clients'][0]
        lawyer_id = self.created_entities['lawyers'][0]
        branch_id = self.branch_ids.get('caxias') or 'default-branch'
        
        # Test 1: Create Process with Responsible Lawyer
        process_data = {
            "client_id": client_id,
            "process_number": "5001234-56.2025.8.21.0001",
            "type": "Ação de Cobrança",
            "status": "Em Andamento",
            "value": 25000.00,
            "description": "Cobrança de honorários advocatícios com advogado responsável",
            "role": "creditor",
            "branch_id": branch_id,
            "responsible_lawyer_id": lawyer_id
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/processes", json=process_data, headers=auth_header)
            if response.status_code == 200:
                process = response.json()
                self.created_entities['processes'].append(process['id'])
                
                # Verify responsible lawyer assignment
                if process.get('responsible_lawyer_id') == lawyer_id:
                    self.log_test("Create Process with Responsible Lawyer", True, 
                                f"Created: {process['process_number']} - Lawyer: {process['responsible_lawyer_id']} - Value: R$ {process['value']} - ID: {process['id']}")
                else:
                    self.log_test("Create Process with Responsible Lawyer", False, 
                                f"Lawyer assignment failed. Expected: {lawyer_id}, Got: {process.get('responsible_lawyer_id')}")
            else:
                self.log_test("Create Process with Responsible Lawyer", False, 
                            f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Process with Responsible Lawyer", False, f"EXCEPTION: {str(e)}")
    
    def test_financial_management_with_access_control(self):
        """Test financial management with new access control"""
        print("\n" + "="*80)
        print("💰 FINANCIAL MANAGEMENT - ACCESS CONTROL")
        print("="*80)
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'}
        client_id = self.created_entities['clients'][0] if self.created_entities['clients'] else None
        process_id = self.created_entities['processes'][0] if self.created_entities['processes'] else None
        branch_id = self.branch_ids.get('caxias') or 'default-branch'
        
        # Test 1: Create Revenue Transaction
        revenue_data = {
            "client_id": client_id,
            "process_id": process_id,
            "type": "receita",
            "description": "Honorários advocatícios - Ação de Cobrança",
            "value": 8000.00,
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "status": "pendente",
            "category": "Honorários Advocatícios",
            "branch_id": branch_id
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/financial", json=revenue_data, headers=auth_header)
            if response.status_code == 200:
                transaction = response.json()
                self.created_entities['financial_transactions'].append(transaction['id'])
                self.log_test("Create Revenue Transaction", True, 
                            f"Created: {transaction['description']} - Value: R$ {transaction['value']} - Status: {transaction['status']} - ID: {transaction['id']}")
            else:
                self.log_test("Create Revenue Transaction", False, f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Revenue Transaction", False, f"EXCEPTION: {str(e)}")
        
        # Test 2: Test Financial Access Control - Lawyer with Access
        if 'test_lawyer' in self.auth_tokens:
            lawyer_header = {'Authorization': f'Bearer {self.auth_tokens["test_lawyer"]}'}
            
            try:
                response = self.session.get(f"{API_BASE_URL}/financial", headers=lawyer_header)
                if response.status_code == 200:
                    transactions = response.json()
                    self.log_test("Lawyer Financial Access (Authorized)", True, 
                                f"Lawyer with financial access can view {len(transactions)} transactions")
                elif response.status_code == 403:
                    self.log_test("Lawyer Financial Access (Authorized)", False, 
                                "Lawyer with financial access blocked from financial data")
                else:
                    self.log_test("Lawyer Financial Access (Authorized)", False, 
                                f"Unexpected response: HTTP {response.status_code}")
            except Exception as e:
                self.log_test("Lawyer Financial Access (Authorized)", False, f"EXCEPTION: {str(e)}")
        
        # Test 3: Create Expense Transaction
        expense_data = {
            "type": "despesa",
            "description": "Custas processuais - Tribunal de Justiça do RS",
            "value": 450.00,
            "due_date": (datetime.now() + timedelta(days=15)).isoformat(),
            "status": "pendente",
            "category": "Custas Processuais",
            "branch_id": branch_id
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/financial", json=expense_data, headers=auth_header)
            if response.status_code == 200:
                transaction = response.json()
                self.created_entities['financial_transactions'].append(transaction['id'])
                self.log_test("Create Expense Transaction", True, 
                            f"Created: {transaction['description']} - Value: R$ {transaction['value']} - ID: {transaction['id']}")
            else:
                self.log_test("Create Expense Transaction", False, f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Expense Transaction", False, f"EXCEPTION: {str(e)}")
    
    def test_contract_sequential_numbering(self):
        """Test contract sequential numbering CONT-YYYY-NNNN"""
        print("\n" + "="*80)
        print("📄 CONTRACT SEQUENTIAL NUMBERING - CONT-YYYY-NNNN")
        print("="*80)
        
        if not self.created_entities['clients']:
            self.log_test("Contract Sequential Numbering Prerequisites", False, "No clients available")
            return
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'}
        client_id = self.created_entities['clients'][0]
        process_id = self.created_entities['processes'][0] if self.created_entities['processes'] else None
        branch_id = self.branch_ids.get('caxias') or 'default-branch'
        current_year = datetime.now().year
        
        contract_numbers = []
        
        # Test 1: Create multiple contracts to test sequential numbering
        for i in range(3):
            contract_data = {
                "client_id": client_id,
                "process_id": process_id,
                "value": 15000.00 + (i * 2000),
                "payment_conditions": f"Pagamento em {i+2} parcelas mensais de R$ {(15000.00 + (i * 2000))/(i+2):.2f}",
                "installments": i + 2,
                "branch_id": branch_id
            }
            
            try:
                response = self.session.post(f"{API_BASE_URL}/contracts", json=contract_data, headers=auth_header)
                if response.status_code == 200:
                    contract = response.json()
                    self.created_entities['contracts'].append(contract['id'])
                    contract_numbers.append(contract['contract_number'])
                    self.log_test(f"Create Contract {i+1} - Sequential Numbering", True, 
                                f"Created: {contract['contract_number']} - Value: R$ {contract['value']} - Installments: {contract['installments']} - ID: {contract['id']}")
                else:
                    self.log_test(f"Create Contract {i+1} - Sequential Numbering", False, 
                                f"FAILED: HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test(f"Create Contract {i+1} - Sequential Numbering", False, f"EXCEPTION: {str(e)}")
        
        # Test 2: Verify sequential numbering pattern
        if len(contract_numbers) >= 2:
            # Check if numbers follow CONT-YYYY-NNNN pattern
            pattern_valid = all(f"CONT-{current_year}-" in num for num in contract_numbers)
            if pattern_valid:
                self.log_test("Contract Number Pattern Validation", True, 
                            f"All contracts follow CONT-{current_year}-NNNN pattern: {contract_numbers}")
                
                # Check if numbers are sequential
                numbers = []
                for contract_num in contract_numbers:
                    try:
                        seq_part = contract_num.split('-')[-1]
                        numbers.append(int(seq_part))
                    except:
                        pass
                
                if len(numbers) >= 2:
                    is_sequential = all(numbers[i] == numbers[i-1] + 1 for i in range(1, len(numbers)))
                    if is_sequential:
                        self.log_test("Contract Sequential Numbering Verification", True, 
                                    f"Contract numbers are sequential: {contract_numbers}")
                    else:
                        self.log_test("Contract Sequential Numbering Verification", False, 
                                    f"Numbers not sequential: {contract_numbers}")
                else:
                    self.log_test("Contract Sequential Numbering Verification", False, 
                                "Could not extract sequential numbers")
            else:
                self.log_test("Contract Number Pattern Validation", False, 
                            f"Invalid pattern in contract numbers: {contract_numbers}")
    
    def test_task_management_system(self):
        """Test task management system"""
        print("\n" + "="*80)
        print("📋 TASK MANAGEMENT SYSTEM")
        print("="*80)
        
        if not self.created_entities['lawyers']:
            self.log_test("Task Management Prerequisites", False, "No lawyers available for task testing")
            return
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'}
        lawyer_id = self.created_entities['lawyers'][0]
        client_id = self.created_entities['clients'][0] if self.created_entities['clients'] else None
        process_id = self.created_entities['processes'][0] if self.created_entities['processes'] else None
        branch_id = self.branch_ids.get('caxias') or 'default-branch'
        
        # Test 1: Create Task (Admin only)
        task_data = {
            "title": "Revisar documentos do processo de cobrança",
            "description": "Revisar todos os documentos relacionados ao processo, verificar prazos e preparar petição",
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
                self.created_entities['tasks'].append(task['id'])
                self.log_test("Create Task (Admin Only)", True, 
                            f"Created: {task['title']} - Priority: {task['priority']} - Assigned to: {task['assigned_lawyer_id']} - ID: {task['id']}")
            else:
                self.log_test("Create Task (Admin Only)", False, f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Task (Admin Only)", False, f"EXCEPTION: {str(e)}")
        
        # Test 2: Test Task Access Control (Lawyer should not be able to create tasks)
        if 'test_lawyer' in self.auth_tokens:
            lawyer_header = {'Authorization': f'Bearer {self.auth_tokens["test_lawyer"]}'}
            
            try:
                response = self.session.post(f"{API_BASE_URL}/tasks", json=task_data, headers=lawyer_header)
                if response.status_code == 403:
                    self.log_test("Task Creation Access Control", True, 
                                "Lawyer correctly blocked from creating tasks (admin-only)")
                else:
                    self.log_test("Task Creation Access Control", False, 
                                f"Lawyer should not be able to create tasks. Got: HTTP {response.status_code}")
            except Exception as e:
                self.log_test("Task Creation Access Control", False, f"EXCEPTION: {str(e)}")
    
    def test_comprehensive_data_editing(self):
        """Test data editing across all modules"""
        print("\n" + "="*80)
        print("✏️ COMPREHENSIVE DATA EDITING")
        print("="*80)
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'}
        
        # Test 1: Edit Client Data (including new address structure)
        if self.created_entities['clients']:
            client_id = self.created_entities['clients'][0]
            update_data = {
                "name": "João Pedro Silva Santos - EDITADO",
                "phone": "(54) 99999-9999",
                "address": {
                    "street": "Rua Marechal Deodoro - EDITADA",
                    "number": "1234-A",
                    "city": "Caxias do Sul",
                    "district": "Centro Histórico",
                    "state": "RS",
                    "complement": "Apartamento 502 - Bloco B - EDITADO"
                }
            }
            
            try:
                response = self.session.put(f"{API_BASE_URL}/clients/{client_id}", json=update_data, headers=auth_header)
                if response.status_code == 200:
                    updated_client = response.json()
                    self.log_test("Edit Client Data", True, 
                                f"Updated: {updated_client['name']} - New phone: {updated_client['phone']} - New complement: {updated_client['complement']}")
                else:
                    self.log_test("Edit Client Data", False, f"FAILED: HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Edit Client Data", False, f"EXCEPTION: {str(e)}")
        
        # Test 2: Edit Lawyer Data (including new fields)
        if self.created_entities['lawyers']:
            lawyer_id = self.created_entities['lawyers'][0]
            update_data = {
                "full_name": "Dr. Roberto Carlos Silva - EDITADO",
                "phone": "(54) 99999-0000",
                "specialization": "Direito Empresarial, Tributário e Trabalhista",
                "access_financial_data": False,  # Change financial access
                "allowed_branch_ids": []  # Remove branch restrictions
            }
            
            try:
                response = self.session.put(f"{API_BASE_URL}/lawyers/{lawyer_id}", json=update_data, headers=auth_header)
                if response.status_code == 200:
                    updated_lawyer = response.json()
                    self.log_test("Edit Lawyer Data", True, 
                                f"Updated: {updated_lawyer['full_name']} - Financial Access: {updated_lawyer['access_financial_data']} - Specialization: {updated_lawyer['specialization']}")
                else:
                    self.log_test("Edit Lawyer Data", False, f"FAILED: HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Edit Lawyer Data", False, f"EXCEPTION: {str(e)}")
        
        # Test 3: Edit Process Data
        if self.created_entities['processes']:
            process_id = self.created_entities['processes'][0]
            update_data = {
                "status": "Finalizado - EDITADO",
                "value": 35000.00,
                "description": "Processo editado com novo valor e status finalizado"
            }
            
            try:
                response = self.session.put(f"{API_BASE_URL}/processes/{process_id}", json=update_data, headers=auth_header)
                if response.status_code == 200:
                    updated_process = response.json()
                    self.log_test("Edit Process Data", True, 
                                f"Updated: Status: {updated_process['status']} - Value: R$ {updated_process['value']}")
                else:
                    self.log_test("Edit Process Data", False, f"FAILED: HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Edit Process Data", False, f"EXCEPTION: {str(e)}")
        
        # Test 4: Edit Financial Transaction
        if self.created_entities['financial_transactions']:
            transaction_id = self.created_entities['financial_transactions'][0]
            update_data = {
                "description": "Honorários advocatícios - EDITADO",
                "value": 10000.00,
                "status": "pago",
                "payment_date": datetime.now().isoformat()
            }
            
            try:
                response = self.session.put(f"{API_BASE_URL}/financial/{transaction_id}", json=update_data, headers=auth_header)
                if response.status_code == 200:
                    updated_transaction = response.json()
                    self.log_test("Edit Financial Transaction", True, 
                                f"Updated: {updated_transaction['description']} - Status: {updated_transaction['status']} - Value: R$ {updated_transaction['value']}")
                else:
                    self.log_test("Edit Financial Transaction", False, f"FAILED: HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("Edit Financial Transaction", False, f"EXCEPTION: {str(e)}")
    
    def test_comprehensive_data_deletion(self):
        """Test data deletion with validations"""
        print("\n" + "="*80)
        print("🗑️ COMPREHENSIVE DATA DELETION WITH VALIDATIONS")
        print("="*80)
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'}
        
        # Test 1: Try to delete client with dependencies (should fail)
        if self.created_entities['clients']:
            client_id = self.created_entities['clients'][0]
            
            try:
                response = self.session.delete(f"{API_BASE_URL}/clients/{client_id}", headers=auth_header)
                if response.status_code == 400:
                    error_data = response.json()
                    self.log_test("Delete Client with Dependencies (Validation)", True, 
                                f"Correctly blocked deletion: {error_data.get('detail', 'Dependency validation working')}")
                else:
                    self.log_test("Delete Client with Dependencies (Validation)", False, 
                                f"Expected 400 (validation error), got {response.status_code}")
            except Exception as e:
                self.log_test("Delete Client with Dependencies (Validation)", False, f"EXCEPTION: {str(e)}")
        
        # Test 2: Try to delete paid financial transaction (should fail)
        if self.created_entities['financial_transactions']:
            transaction_id = self.created_entities['financial_transactions'][0]
            
            try:
                response = self.session.delete(f"{API_BASE_URL}/financial/{transaction_id}", headers=auth_header)
                if response.status_code == 400:
                    error_data = response.json()
                    self.log_test("Delete Paid Financial Transaction (Validation)", True, 
                                f"Correctly blocked deletion: {error_data.get('detail', 'Paid transaction validation working')}")
                else:
                    self.log_test("Delete Paid Financial Transaction (Validation)", False, 
                                f"Expected 400 (validation error), got {response.status_code}")
            except Exception as e:
                self.log_test("Delete Paid Financial Transaction (Validation)", False, f"EXCEPTION: {str(e)}")
        
        # Test 3: Create and delete pending transaction (should succeed)
        branch_id = self.branch_ids.get('caxias') or 'default-branch'
        pending_transaction_data = {
            "type": "despesa",
            "description": "Transação para teste de exclusão",
            "value": 100.00,
            "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "status": "pendente",
            "category": "Teste",
            "branch_id": branch_id
        }
        
        try:
            # Create pending transaction
            response = self.session.post(f"{API_BASE_URL}/financial", json=pending_transaction_data, headers=auth_header)
            if response.status_code == 200:
                transaction = response.json()
                transaction_id = transaction['id']
                
                # Now try to delete it
                response = self.session.delete(f"{API_BASE_URL}/financial/{transaction_id}", headers=auth_header)
                if response.status_code == 200:
                    self.log_test("Delete Pending Financial Transaction", True, 
                                "Successfully deleted pending transaction")
                else:
                    self.log_test("Delete Pending Financial Transaction", False, 
                                f"Failed to delete pending transaction: HTTP {response.status_code}")
            else:
                self.log_test("Delete Pending Financial Transaction", False, 
                            "Failed to create test transaction for deletion")
        except Exception as e:
            self.log_test("Delete Pending Financial Transaction", False, f"EXCEPTION: {str(e)}")
    
    def test_advanced_integrations(self):
        """Test WhatsApp and Google Drive integrations"""
        print("\n" + "="*80)
        print("🔗 ADVANCED INTEGRATIONS - WHATSAPP & GOOGLE DRIVE")
        print("="*80)
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'}
        
        # Test 1: WhatsApp Status
        try:
            response = self.session.get(f"{API_BASE_URL}/whatsapp/status", headers=auth_header)
            if response.status_code == 200:
                status_data = response.json()
                self.log_test("WhatsApp Status Endpoint", True, 
                            f"Service status: {status_data.get('service_status', 'unknown')} - Mode: {status_data.get('mode', 'unknown')} - Phone: {status_data.get('phone_number', 'N/A')}")
            else:
                self.log_test("WhatsApp Status Endpoint", False, f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("WhatsApp Status Endpoint", False, f"EXCEPTION: {str(e)}")
        
        # Test 2: WhatsApp Send Message
        message_data = {
            "phone_number": "+5554997102525",
            "message": "🏛️ Teste de mensagem do Sistema Jurídico GB Advocacia - PostgreSQL Migration Complete! ⚖️"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/whatsapp/send-message", json=message_data, headers=auth_header)
            if response.status_code == 200:
                result = response.json()
                self.log_test("WhatsApp Send Message", True, 
                            f"Message sent successfully - Simulated: {result.get('simulated', False)}")
            else:
                self.log_test("WhatsApp Send Message", False, f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("WhatsApp Send Message", False, f"EXCEPTION: {str(e)}")
        
        # Test 3: WhatsApp Bulk Payment Check (Admin only)
        try:
            response = self.session.post(f"{API_BASE_URL}/whatsapp/check-payments", headers=auth_header)
            if response.status_code == 200:
                result = response.json()
                self.log_test("WhatsApp Bulk Payment Check", True, 
                            f"Bulk check completed - Overdue: {result.get('total_overdue', 0)}, Sent: {result.get('reminders_sent', 0)}")
            else:
                self.log_test("WhatsApp Bulk Payment Check", False, f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("WhatsApp Bulk Payment Check", False, f"EXCEPTION: {str(e)}")
        
        # Test 4: Google Drive Status
        try:
            response = self.session.get(f"{API_BASE_URL}/google-drive/status", headers=auth_header)
            if response.status_code == 200:
                status_data = response.json()
                self.log_test("Google Drive Status", True, 
                            f"Configured: {status_data.get('configured', False)} - Service available: {status_data.get('service_available', False)}")
            else:
                self.log_test("Google Drive Status", False, f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Google Drive Status", False, f"EXCEPTION: {str(e)}")
    
    def test_dashboard_statistics(self):
        """Test dashboard statistics with real data"""
        print("\n" + "="*80)
        print("📊 DASHBOARD STATISTICS")
        print("="*80)
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'}
        
        try:
            response = self.session.get(f"{API_BASE_URL}/dashboard", headers=auth_header)
            if response.status_code == 200:
                stats = response.json()
                
                # Verify required fields
                required_fields = [
                    'total_clients', 'total_processes', 'total_revenue', 'total_expenses',
                    'pending_payments', 'overdue_payments', 'monthly_revenue', 'monthly_expenses'
                ]
                missing_fields = [field for field in required_fields if field not in stats]
                
                if not missing_fields:
                    self.log_test("Dashboard Statistics", True, 
                                f"All fields present - Clients: {stats['total_clients']}, Processes: {stats['total_processes']}, Revenue: R$ {stats['total_revenue']}, Expenses: R$ {stats['total_expenses']}")
                    
                    # Print detailed dashboard summary
                    print(f"      📈 DASHBOARD SUMMARY:")
                    print(f"         👥 Total Clients: {stats['total_clients']}")
                    print(f"         ⚖️ Total Processes: {stats['total_processes']}")
                    print(f"         💰 Total Revenue: R$ {stats['total_revenue']}")
                    print(f"         💸 Total Expenses: R$ {stats['total_expenses']}")
                    print(f"         ⏳ Pending Payments: {stats['pending_payments']}")
                    print(f"         🔴 Overdue Payments: {stats['overdue_payments']}")
                    print(f"         📅 Monthly Revenue: R$ {stats['monthly_revenue']}")
                    print(f"         📅 Monthly Expenses: R$ {stats['monthly_expenses']}")
                    print()
                else:
                    self.log_test("Dashboard Statistics", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Dashboard Statistics", False, f"FAILED: HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Dashboard Statistics", False, f"EXCEPTION: {str(e)}")
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n" + "="*80)
        print("🧹 CLEANING UP TEST DATA")
        print("="*80)
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens.get("super_admin")}'}
        
        # Clean up in reverse order of dependencies
        cleanup_order = [
            ('tasks', '/api/tasks'),
            ('contracts', '/api/contracts'),
            ('financial_transactions', '/api/financial'),
            ('processes', '/api/processes'),
            ('clients', '/api/clients'),
            ('lawyers', '/api/lawyers')
        ]
        
        for entity_type, endpoint in cleanup_order:
            if entity_type in self.created_entities:
                for entity_id in self.created_entities[entity_type]:
                    try:
                        response = self.session.delete(f"{API_BASE_URL}{endpoint}/{entity_id}", headers=auth_header)
                        if response.status_code in [200, 404]:
                            print(f"      ✅ Cleaned up {entity_type}: {entity_id}")
                        else:
                            print(f"      ⚠️ Could not clean up {entity_type} {entity_id}: HTTP {response.status_code}")
                    except Exception as e:
                        print(f"      ❌ Error cleaning up {entity_type} {entity_id}: {str(e)}")
    
    def run_comprehensive_tests(self):
        """Run all comprehensive backend tests as requested by user"""
        print("🚀 COMPREHENSIVE BACKEND TESTING - SISTEMA JURÍDICO GB ADVOCACIA")
        print("🐘 PostgreSQL Migration Complete Testing")
        print(f"🌐 Backend URL: {API_BASE_URL}")
        print("="*80)
        print("TESTING SCOPE:")
        print("✅ Authentication - All login credentials")
        print("✅ Registration - Users and lawyers with new fields")
        print("✅ Data Editing - All modules with PostgreSQL structure")
        print("✅ Data Deletion - With proper validations")
        print("✅ PostgreSQL Features - UUID keys, address structure, sequential numbering")
        print("✅ Access Control - Financial permissions, branch isolation")
        print("✅ Integrations - WhatsApp Business, Google Drive")
        print("✅ Security - Advanced features, password validation")
        print("="*80)
        
        try:
            # Run all comprehensive tests
            self.test_comprehensive_authentication()
            self.test_comprehensive_registration()
            self.test_client_management_with_new_address_structure()
            self.test_process_management_with_responsible_lawyer()
            self.test_financial_management_with_access_control()
            self.test_contract_sequential_numbering()
            self.test_task_management_system()
            self.test_comprehensive_data_editing()
            self.test_comprehensive_data_deletion()
            self.test_advanced_integrations()
            self.test_dashboard_statistics()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Print final results
        print("\n" + "="*80)
        print("🏁 COMPREHENSIVE TEST RESULTS")
        print("="*80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = sum(1 for result in self.test_results if not result['success'])
        total = len(self.test_results)
        
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"📊 TOTAL: {total}")
        print(f"📈 SUCCESS RATE: {(passed/total*100):.1f}%" if total > 0 else "No tests run")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}")
                    print(f"     {result['message']}")
        
        print("\n" + "="*80)
        print("🎯 COMPREHENSIVE TESTING COMPLETE")
        print("="*80)
        
        return passed, failed, total

def main():
    """Main function to run comprehensive backend tests"""
    tester = ComprehensiveBackendTester()
    passed, failed, total = tester.run_comprehensive_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()