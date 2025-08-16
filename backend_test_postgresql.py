#!/usr/bin/env python3
"""
PostgreSQL Migration Testing Suite for GB Advocacia & N. Comin
Tests the new PostgreSQL structure and specific features requested in the review
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

class PostgreSQLTester:
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
            'tasks': []
        }
        self.auth_tokens = {}
        self.branch_ids = {}
        
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
    
    def test_postgresql_migration_basic_endpoints(self):
        """Test 1: PostgreSQL Migration - Basic endpoints functionality"""
        print("\n=== Testing PostgreSQL Migration - Basic Endpoints ===")
        
        # Test basic endpoints without authentication
        endpoints_to_test = [
            ("/auth/login", "POST", {"username_or_email": "admin", "password": "admin123"}),
        ]
        
        for endpoint, method, data in endpoints_to_test:
            try:
                if method == "POST":
                    response = self.session.post(f"{API_BASE_URL}{endpoint}", json=data)
                else:
                    response = self.session.get(f"{API_BASE_URL}{endpoint}")
                
                if response.status_code in [200, 201]:
                    self.log_test(f"PostgreSQL Endpoint {endpoint}", True, f"Endpoint responding correctly")
                    if endpoint == "/auth/login" and response.status_code == 200:
                        token_data = response.json()
                        self.auth_tokens['admin'] = token_data['access_token']
                else:
                    self.log_test(f"PostgreSQL Endpoint {endpoint}", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test(f"PostgreSQL Endpoint {endpoint}", False, f"Exception: {str(e)}")
    
    def test_admin_login(self):
        """Test 2: Login with admin/admin123"""
        print("\n=== Testing Admin Login ===")
        
        login_data = {
            "username_or_email": "admin",
            "password": "admin123"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_tokens['admin'] = token_data['access_token']
                user = token_data['user']
                self.log_test("Admin Login", True, f"Successfully logged in as: {user['full_name']}")
                
                # Verify admin role
                if user.get('role') == 'admin':
                    self.log_test("Admin Role Verification", True, "User has correct admin role")
                else:
                    self.log_test("Admin Role Verification", False, f"Expected 'admin', got '{user.get('role')}'")
                    
                # Get branches for later use
                self.get_branches()
                
            else:
                self.log_test("Admin Login", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
    
    def get_branches(self):
        """Get available branches"""
        if 'admin' not in self.auth_tokens:
            return
            
        try:
            response = self.session.get(f"{API_BASE_URL}/branches", 
                                      headers={'Authorization': f'Bearer {self.auth_tokens["admin"]}'})
            if response.status_code == 200:
                branches = response.json()
                for branch in branches:
                    if 'Caxias do Sul' in branch['name']:
                        self.branch_ids['caxias'] = branch['id']
                    elif 'Nova Prata' in branch['name']:
                        self.branch_ids['nova_prata'] = branch['id']
                self.log_test("Get Branches", True, f"Retrieved {len(branches)} branches")
            else:
                self.log_test("Get Branches", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Get Branches", False, f"Exception: {str(e)}")
    
    def test_client_creation_new_address_structure(self):
        """Test 3: Client creation with new PostgreSQL address structure"""
        print("\n=== Testing Client Creation with New Address Structure ===")
        
        if not self.branch_ids:
            self.log_test("Client Creation Prerequisites", False, "No branch IDs available")
            return
        
        branch_id = self.branch_ids.get('caxias') or list(self.branch_ids.values())[0]
        
        # Test creating client with new address structure
        client_data = {
            "name": "João Silva Empresário",
            "nationality": "Brasileira",
            "civil_status": "Casado",
            "profession": "Empresário",
            "cpf": "123.456.789-10",
            "address": {
                "street": "Rua Marechal Deodoro",
                "number": "456",
                "city": "Caxias do Sul",
                "district": "Centro",
                "state": "RS",
                "complement": "Sala 201"
            },
            "phone": "(54) 99876-5432",
            "client_type": "individual",
            "branch_id": branch_id
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/clients", json=client_data)
            if response.status_code == 200:
                client = response.json()
                self.created_entities['clients'].append(client['id'])
                self.log_test("Create Client with New Address Structure", True, f"Created client: {client['name']}")
                
                # Verify address fields are properly stored
                address_fields = ['street', 'number', 'city', 'district', 'state', 'complement']
                missing_fields = [field for field in address_fields if field not in client or not client[field]]
                if not missing_fields:
                    self.log_test("Address Structure Validation", True, "All address fields properly stored")
                else:
                    self.log_test("Address Structure Validation", False, f"Missing address fields: {missing_fields}")
                    
                # Verify client type
                if client.get('client_type') == 'individual':
                    self.log_test("Client Type Validation", True, "Client type correctly stored")
                else:
                    self.log_test("Client Type Validation", False, f"Expected 'individual', got '{client.get('client_type')}'")
                    
            else:
                self.log_test("Create Client with New Address Structure", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Client with New Address Structure", False, f"Exception: {str(e)}")
    
    def test_contract_sequential_numbering(self):
        """Test 4: Contract system with sequential numbering (CONT-2025-0001, etc.)"""
        print("\n=== Testing Contract Sequential Numbering System ===")
        
        if not self.created_entities['clients']:
            self.log_test("Contract Numbering Prerequisites", False, "No clients available")
            return
        
        client_id = self.created_entities['clients'][0]
        branch_id = self.branch_ids.get('caxias') or list(self.branch_ids.values())[0]
        current_year = datetime.now().year
        
        # Create multiple contracts to test sequential numbering
        contract_numbers = []
        
        for i in range(3):
            contract_data = {
                "client_id": client_id,
                "value": 15000.00 + (i * 2500),
                "payment_conditions": f"Pagamento em {i+2} parcelas mensais",
                "installments": i + 2,
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
        
        # Verify sequential numbering pattern
        if len(contract_numbers) >= 2:
            # Check CONT-YYYY-NNNN pattern
            pattern_valid = all(f"CONT-{current_year}-" in num for num in contract_numbers)
            if pattern_valid:
                self.log_test("Contract Number Pattern", True, f"All contracts follow CONT-{current_year}-NNNN pattern")
                
                # Extract and verify sequential numbers
                numbers = []
                for contract_num in contract_numbers:
                    try:
                        seq_part = contract_num.split('-')[-1]
                        numbers.append(int(seq_part))
                    except:
                        pass
                
                if len(numbers) >= 2:
                    # Check if numbers are sequential (allowing for existing contracts)
                    is_increasing = all(numbers[i] > numbers[i-1] for i in range(1, len(numbers)))
                    if is_increasing:
                        self.log_test("Contract Sequential Numbering", True, f"Contract numbers are sequential: {contract_numbers}")
                    else:
                        self.log_test("Contract Sequential Numbering", False, f"Numbers not sequential: {contract_numbers}")
                else:
                    self.log_test("Contract Sequential Numbering", False, "Could not extract sequential numbers")
            else:
                self.log_test("Contract Number Pattern", False, f"Invalid pattern: {contract_numbers}")
        else:
            self.log_test("Contract Sequential Numbering", False, "Not enough contracts created")
    
    def test_lawyer_system_new_fields(self):
        """Test 5: Lawyer system with access_financial_data and allowed_branch_ids"""
        print("\n=== Testing Lawyer System with New Fields ===")
        
        if 'admin' not in self.auth_tokens:
            self.log_test("Lawyer System Prerequisites", False, "No admin authentication")
            return
        
        if not self.branch_ids:
            self.log_test("Lawyer System Prerequisites", False, "No branch IDs available")
            return
        
        branch_id = self.branch_ids.get('caxias') or list(self.branch_ids.values())[0]
        auth_header = {'Authorization': f'Bearer {self.auth_tokens["admin"]}'}
        
        # Test 1: Create lawyer with financial access
        lawyer_with_access_data = {
            "full_name": "Dr. Carlos Mendes",
            "oab_number": "987654",
            "oab_state": "RS",
            "email": "carlos.mendes@gbadvocacia.com",
            "phone": "(54) 99888-7777",
            "specialization": "Direito Empresarial",
            "branch_id": branch_id,
            "access_financial_data": True,
            "allowed_branch_ids": [branch_id]
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/lawyers", 
                                       json=lawyer_with_access_data, 
                                       headers=auth_header)
            if response.status_code == 200:
                lawyer = response.json()
                self.created_entities['lawyers'].append(lawyer['id'])
                self.log_test("Create Lawyer with Financial Access", True, f"Created lawyer: {lawyer['full_name']}")
                
                # Verify new fields
                if lawyer.get('access_financial_data') == True:
                    self.log_test("Lawyer Financial Access Field", True, "access_financial_data correctly set to True")
                else:
                    self.log_test("Lawyer Financial Access Field", False, f"Expected True, got {lawyer.get('access_financial_data')}")
                
                if lawyer.get('allowed_branch_ids'):
                    self.log_test("Lawyer Branch IDs Field", True, "allowed_branch_ids field present")
                else:
                    self.log_test("Lawyer Branch IDs Field", False, "allowed_branch_ids field missing")
                    
            else:
                self.log_test("Create Lawyer with Financial Access", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Lawyer with Financial Access", False, f"Exception: {str(e)}")
        
        # Test 2: Create lawyer without financial access
        lawyer_without_access_data = {
            "full_name": "Dra. Ana Paula Santos",
            "oab_number": "456789",
            "oab_state": "RS",
            "email": "ana.santos@gbadvocacia.com",
            "phone": "(54) 99777-6666",
            "specialization": "Direito de Família",
            "branch_id": branch_id,
            "access_financial_data": False,
            "allowed_branch_ids": [branch_id]
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/lawyers", 
                                       json=lawyer_without_access_data, 
                                       headers=auth_header)
            if response.status_code == 200:
                lawyer = response.json()
                self.created_entities['lawyers'].append(lawyer['id'])
                self.log_test("Create Lawyer without Financial Access", True, f"Created lawyer: {lawyer['full_name']}")
                
                # Verify restricted access
                if lawyer.get('access_financial_data') == False:
                    self.log_test("Lawyer Restricted Financial Access", True, "access_financial_data correctly set to False")
                else:
                    self.log_test("Lawyer Restricted Financial Access", False, f"Expected False, got {lawyer.get('access_financial_data')}")
                    
            else:
                self.log_test("Create Lawyer without Financial Access", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Lawyer without Financial Access", False, f"Exception: {str(e)}")
    
    def test_process_system_responsible_lawyer(self):
        """Test 6: Process system with responsible_lawyer_id field"""
        print("\n=== Testing Process System with Responsible Lawyer ===")
        
        if not self.created_entities['clients'] or not self.created_entities['lawyers']:
            self.log_test("Process System Prerequisites", False, "Missing clients or lawyers")
            return
        
        client_id = self.created_entities['clients'][0]
        lawyer_id = self.created_entities['lawyers'][0]
        branch_id = self.branch_ids.get('caxias') or list(self.branch_ids.values())[0]
        
        # Create process with responsible lawyer
        process_data = {
            "client_id": client_id,
            "process_number": "0001234-56.2025.8.26.0300",
            "type": "Ação de Cobrança",
            "status": "Em Andamento",
            "value": 30000.00,
            "description": "Processo com advogado responsável designado",
            "role": "creditor",
            "branch_id": branch_id,
            "responsible_lawyer_id": lawyer_id
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/processes", json=process_data)
            if response.status_code == 200:
                process = response.json()
                self.created_entities['processes'].append(process['id'])
                self.log_test("Create Process with Responsible Lawyer", True, f"Created process: {process['process_number']}")
                
                # Verify lawyer assignment
                if process.get('responsible_lawyer_id') == lawyer_id:
                    self.log_test("Process Lawyer Assignment", True, "Process correctly assigned to lawyer")
                else:
                    self.log_test("Process Lawyer Assignment", False, "Process not correctly assigned to lawyer")
                    
            else:
                self.log_test("Create Process with Responsible Lawyer", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Process with Responsible Lawyer", False, f"Exception: {str(e)}")
    
    def test_financial_access_control(self):
        """Test 7: Financial access control for lawyers"""
        print("\n=== Testing Financial Access Control ===")
        
        if len(self.created_entities['lawyers']) < 2:
            self.log_test("Financial Access Control Prerequisites", False, "Need at least 2 lawyers")
            return
        
        # Login as lawyer with financial access
        lawyer_with_access_email = "carlos.mendes@gbadvocacia.com"
        lawyer_with_access_oab = "987654"
        
        login_data = {
            "username_or_email": lawyer_with_access_email,
            "password": lawyer_with_access_oab
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_tokens['lawyer_with_access'] = token_data['access_token']
                self.log_test("Login Lawyer with Financial Access", True, "Successfully logged in")
                
                # Test financial data access
                auth_header = {'Authorization': f'Bearer {self.auth_tokens["lawyer_with_access"]}'}
                financial_response = self.session.get(f"{API_BASE_URL}/financial", headers=auth_header)
                
                if financial_response.status_code == 200:
                    self.log_test("Lawyer Financial Data Access", True, "Lawyer with access can view financial data")
                else:
                    self.log_test("Lawyer Financial Data Access", False, f"HTTP {financial_response.status_code}")
                    
            else:
                self.log_test("Login Lawyer with Financial Access", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Login Lawyer with Financial Access", False, f"Exception: {str(e)}")
        
        # Login as lawyer without financial access
        lawyer_without_access_email = "ana.santos@gbadvocacia.com"
        lawyer_without_access_oab = "456789"
        
        login_data = {
            "username_or_email": lawyer_without_access_email,
            "password": lawyer_without_access_oab
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_tokens['lawyer_without_access'] = token_data['access_token']
                self.log_test("Login Lawyer without Financial Access", True, "Successfully logged in")
                
                # Test financial data access (should be blocked)
                auth_header = {'Authorization': f'Bearer {self.auth_tokens["lawyer_without_access"]}'}
                financial_response = self.session.get(f"{API_BASE_URL}/financial", headers=auth_header)
                
                if financial_response.status_code == 403:
                    self.log_test("Restricted Lawyer Financial Access Block", True, "Correctly blocked access to financial data")
                else:
                    self.log_test("Restricted Lawyer Financial Access Block", False, f"Expected 403, got {financial_response.status_code}")
                    
            else:
                self.log_test("Login Lawyer without Financial Access", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Login Lawyer without Financial Access", False, f"Exception: {str(e)}")
    
    def test_task_system(self):
        """Test 8: Task system creation and listing"""
        print("\n=== Testing Task System ===")
        
        if not self.created_entities['lawyers'] or not self.created_entities['clients']:
            self.log_test("Task System Prerequisites", False, "Missing lawyers or clients")
            return
        
        lawyer_id = self.created_entities['lawyers'][0]
        client_id = self.created_entities['clients'][0]
        process_id = self.created_entities['processes'][0] if self.created_entities['processes'] else None
        branch_id = self.branch_ids.get('caxias') or list(self.branch_ids.values())[0]
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens["admin"]}'}
        
        # Create task
        task_data = {
            "title": "Revisar documentação do cliente",
            "description": "Revisar todos os documentos fornecidos pelo cliente para o processo",
            "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
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
                self.log_test("Create Task", True, f"Created task: {task['title']}")
                
                # Verify task fields
                required_fields = ['id', 'title', 'due_date', 'priority', 'status', 'assigned_lawyer_id']
                missing_fields = [field for field in required_fields if field not in task]
                if not missing_fields:
                    self.log_test("Task Fields Validation", True, "All required task fields present")
                else:
                    self.log_test("Task Fields Validation", False, f"Missing fields: {missing_fields}")
                    
            else:
                self.log_test("Create Task", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Task", False, f"Exception: {str(e)}")
        
        # Test task listing
        try:
            response = self.session.get(f"{API_BASE_URL}/tasks", headers=auth_header)
            if response.status_code == 200:
                tasks = response.json()
                self.log_test("List Tasks", True, f"Retrieved {len(tasks)} tasks")
            else:
                self.log_test("List Tasks", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("List Tasks", False, f"Exception: {str(e)}")
    
    def test_dashboard_statistics(self):
        """Test 9: Dashboard statistics functionality"""
        print("\n=== Testing Dashboard Statistics ===")
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens["admin"]}'}
        
        try:
            response = self.session.get(f"{API_BASE_URL}/dashboard", headers=auth_header)
            if response.status_code == 200:
                stats = response.json()
                self.log_test("Get Dashboard Statistics", True, "Retrieved dashboard statistics")
                
                # Verify required fields
                required_fields = [
                    'total_clients', 'total_processes', 'total_revenue', 'total_expenses',
                    'pending_payments', 'overdue_payments', 'monthly_revenue', 'monthly_expenses'
                ]
                missing_fields = [field for field in required_fields if field not in stats]
                if not missing_fields:
                    self.log_test("Dashboard Fields Validation", True, "All required dashboard fields present")
                else:
                    self.log_test("Dashboard Fields Validation", False, f"Missing fields: {missing_fields}")
                
                # Print dashboard summary
                print(f"\n📊 Dashboard Summary:")
                print(f"   Total Clients: {stats.get('total_clients', 0)}")
                print(f"   Total Processes: {stats.get('total_processes', 0)}")
                print(f"   Total Revenue: R$ {stats.get('total_revenue', 0)}")
                print(f"   Total Expenses: R$ {stats.get('total_expenses', 0)}")
                print(f"   Pending Payments: {stats.get('pending_payments', 0)}")
                print(f"   Overdue Payments: {stats.get('overdue_payments', 0)}")
                
            else:
                self.log_test("Get Dashboard Statistics", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Get Dashboard Statistics", False, f"Exception: {str(e)}")
    
    def test_branch_permissions(self):
        """Test 10: Branch permissions - users only see data from allowed branches"""
        print("\n=== Testing Branch Permissions ===")
        
        # Test with admin (should see all data)
        if 'admin' in self.auth_tokens:
            auth_header = {'Authorization': f'Bearer {self.auth_tokens["admin"]}'}
            
            try:
                response = self.session.get(f"{API_BASE_URL}/clients", headers=auth_header)
                if response.status_code == 200:
                    clients = response.json()
                    self.log_test("Admin Branch Access", True, f"Admin can see {len(clients)} clients from all branches")
                else:
                    self.log_test("Admin Branch Access", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("Admin Branch Access", False, f"Exception: {str(e)}")
        
        # Test with lawyer (should see only their branch data)
        if 'lawyer_with_access' in self.auth_tokens:
            auth_header = {'Authorization': f'Bearer {self.auth_tokens["lawyer_with_access"]}'}
            
            try:
                response = self.session.get(f"{API_BASE_URL}/clients", headers=auth_header)
                if response.status_code == 200:
                    clients = response.json()
                    # Verify all clients belong to lawyer's allowed branches
                    lawyer_branch_id = self.branch_ids.get('caxias')
                    if lawyer_branch_id:
                        branch_filtered = all(client.get('branch_id') == lawyer_branch_id for client in clients)
                        if branch_filtered:
                            self.log_test("Lawyer Branch Filtering", True, f"Lawyer sees only branch-specific clients: {len(clients)}")
                        else:
                            self.log_test("Lawyer Branch Filtering", False, "Lawyer sees clients from other branches")
                    else:
                        self.log_test("Lawyer Branch Filtering", True, f"Lawyer sees {len(clients)} clients (branch filtering active)")
                else:
                    self.log_test("Lawyer Branch Filtering", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("Lawyer Branch Filtering", False, f"Exception: {str(e)}")
    
    def run_postgresql_tests(self):
        """Run all PostgreSQL migration tests"""
        print("🐘 Starting PostgreSQL Migration Tests")
        print("=" * 80)
        
        try:
            # Run tests in order
            self.test_postgresql_migration_basic_endpoints()
            self.test_admin_login()
            self.test_client_creation_new_address_structure()
            self.test_contract_sequential_numbering()
            self.test_lawyer_system_new_fields()
            self.test_process_system_responsible_lawyer()
            self.test_financial_access_control()
            self.test_task_system()
            self.test_dashboard_statistics()
            self.test_branch_permissions()
            
        except Exception as e:
            print(f"❌ Critical error during testing: {str(e)}")
        
        return self.test_results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🐘 POSTGRESQL MIGRATION TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['message']}")
        
        print(f"\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"   - {result['test']}: {result['message']}")

def main():
    """Main test execution"""
    tester = PostgreSQLTester()
    
    try:
        results = tester.run_postgresql_tests()
        tester.print_summary()
        
        # Return appropriate exit code
        failed_tests = sum(1 for result in results if not result['success'])
        return 0 if failed_tests == 0 else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Critical error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)