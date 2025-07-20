#!/usr/bin/env python3
"""
Delete Endpoints Testing Suite for GB Advocacia & N. Comin
Tests specific delete endpoint corrections and lawyer management (admin only)
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
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://53e938c3-86a2-4897-b9ec-6e2704b6cfc4.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

class DeleteEndpointsTester:
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
        self.auth_token = None
        
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
    
    def authenticate_admin(self):
        """Authenticate as admin user"""
        print("\n=== Authenticating as Admin ===")
        
        # First, ensure admin user exists
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/create-admin")
            if response.status_code in [200, 400]:  # 400 means admin already exists
                print("✅ Admin user available")
            else:
                print(f"❌ Failed to create admin: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Exception creating admin: {str(e)}")
            return False
        
        # Login as admin
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                auth_response = response.json()
                self.auth_token = auth_response['access_token']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                self.log_test("Admin Authentication", True, f"Authenticated as admin user")
                return True
            else:
                self.log_test("Admin Authentication", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def setup_test_data(self):
        """Create test data for delete endpoint testing"""
        print("\n=== Setting Up Test Data ===")
        
        # Create a test client
        client_data = {
            "name": "João Silva Teste",
            "nationality": "Brasileira",
            "civil_status": "Solteiro",
            "profession": "Engenheiro",
            "cpf": "111.222.333-44",
            "address": {
                "street": "Rua Teste",
                "number": "100",
                "city": "São Paulo",
                "district": "Centro",
                "state": "SP",
                "complement": ""
            },
            "phone": "(11) 99999-0000",
            "client_type": "individual"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/clients", json=client_data)
            if response.status_code == 200:
                client = response.json()
                self.created_entities['clients'].append(client['id'])
                print(f"✅ Created test client: {client['id']}")
            else:
                print(f"❌ Failed to create client: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Exception creating client: {str(e)}")
            return False
        
        client_id = self.created_entities['clients'][0]
        
        # Create a test process
        process_data = {
            "client_id": client_id,
            "process_number": "0001111-22.2024.8.26.0100",
            "type": "Ação Teste",
            "status": "Em Andamento",
            "value": 10000.00,
            "description": "Processo de teste para validação de delete",
            "role": "creditor"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/processes", json=process_data)
            if response.status_code == 200:
                process = response.json()
                self.created_entities['processes'].append(process['id'])
                print(f"✅ Created test process: {process['id']}")
            else:
                print(f"❌ Failed to create process: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Exception creating process: {str(e)}")
            return False
        
        process_id = self.created_entities['processes'][0]
        
        # Create a test contract
        contract_data = {
            "client_id": client_id,
            "process_id": process_id,
            "value": 15000.00,
            "payment_conditions": "Pagamento em 3 parcelas",
            "installments": 3
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/contracts", json=contract_data)
            if response.status_code == 200:
                contract = response.json()
                self.created_entities['contracts'].append(contract['id'])
                print(f"✅ Created test contract: {contract['id']}")
            else:
                print(f"❌ Failed to create contract: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Exception creating contract: {str(e)}")
            return False
        
        # Create financial transactions (pending and paid)
        pending_transaction_data = {
            "client_id": client_id,
            "process_id": process_id,
            "type": "receita",
            "description": "Honorários pendentes",
            "value": 5000.00,
            "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "status": "pendente",
            "category": "Honorários"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/financial", json=pending_transaction_data)
            if response.status_code == 200:
                transaction = response.json()
                self.created_entities['financial_transactions'].append(transaction['id'])
                print(f"✅ Created pending transaction: {transaction['id']}")
            else:
                print(f"❌ Failed to create pending transaction: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Exception creating pending transaction: {str(e)}")
            return False
        
        # Create a paid transaction
        paid_transaction_data = {
            "client_id": client_id,
            "process_id": process_id,
            "type": "receita",
            "description": "Honorários pagos",
            "value": 3000.00,
            "due_date": (datetime.now() - timedelta(days=10)).isoformat(),
            "status": "pago",
            "payment_date": datetime.now().isoformat(),
            "category": "Honorários"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/financial", json=paid_transaction_data)
            if response.status_code == 200:
                transaction = response.json()
                self.created_entities['financial_transactions'].append(transaction['id'])
                print(f"✅ Created paid transaction: {transaction['id']}")
            else:
                print(f"❌ Failed to create paid transaction: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Exception creating paid transaction: {str(e)}")
            return False
        
        return True
    
    def test_client_delete_with_dependencies(self):
        """Test DELETE /api/clients/{client_id} with dependencies"""
        print("\n=== Testing Client Delete with Dependencies ===")
        
        if not self.created_entities['clients']:
            self.log_test("Client Delete Prerequisites", False, "No clients available for testing")
            return
        
        client_id = self.created_entities['clients'][0]
        
        # Try to delete client that has dependencies (processes, contracts, transactions)
        try:
            response = self.session.delete(f"{API_BASE_URL}/clients/{client_id}")
            if response.status_code == 400:
                error_message = response.json().get('detail', '')
                
                # Check if error message mentions specific dependencies
                has_processes = 'processo' in error_message.lower()
                has_contracts = 'contrato' in error_message.lower()
                has_transactions = 'transação' in error_message.lower() or 'financeira' in error_message.lower()
                
                if has_processes and has_contracts and has_transactions:
                    self.log_test("Client Delete Dependency Check", True, 
                                f"Correctly blocked deletion with specific message: {error_message}")
                else:
                    self.log_test("Client Delete Dependency Check", False, 
                                f"Message lacks specific dependency details: {error_message}")
            else:
                self.log_test("Client Delete Dependency Check", False, 
                            f"Expected 400 status, got {response.status_code}")
        except Exception as e:
            self.log_test("Client Delete Dependency Check", False, f"Exception: {str(e)}")
    
    def test_financial_transaction_delete_restrictions(self):
        """Test DELETE /api/financial/{transaction_id} for paid transactions"""
        print("\n=== Testing Financial Transaction Delete Restrictions ===")
        
        if len(self.created_entities['financial_transactions']) < 2:
            self.log_test("Financial Delete Prerequisites", False, "Need both pending and paid transactions")
            return
        
        # Test deleting pending transaction (should work)
        pending_transaction_id = self.created_entities['financial_transactions'][0]
        try:
            response = self.session.delete(f"{API_BASE_URL}/financial/{pending_transaction_id}")
            if response.status_code == 200:
                self.log_test("Delete Pending Transaction", True, "Successfully deleted pending transaction")
                # Remove from our tracking since it's deleted
                self.created_entities['financial_transactions'].remove(pending_transaction_id)
            else:
                self.log_test("Delete Pending Transaction", False, 
                            f"Expected 200, got {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Delete Pending Transaction", False, f"Exception: {str(e)}")
        
        # Test deleting paid transaction (should be blocked)
        if len(self.created_entities['financial_transactions']) > 0:
            paid_transaction_id = self.created_entities['financial_transactions'][0]  # Now the first remaining one
            try:
                response = self.session.delete(f"{API_BASE_URL}/financial/{paid_transaction_id}")
                if response.status_code == 400:
                    error_message = response.json().get('detail', '')
                    # The message "Não é possível excluir uma transação que já foi paga" contains "pago"
                    if 'pago' in error_message or 'paga' in error_message:
                        self.log_test("Delete Paid Transaction Block", True, 
                                    f"Correctly blocked paid transaction deletion: {error_message}")
                    else:
                        self.log_test("Delete Paid Transaction Block", False, 
                                    f"Error message not specific about paid status: {error_message}")
                else:
                    self.log_test("Delete Paid Transaction Block", False, 
                                f"Expected 400 status, got {response.status_code}")
            except Exception as e:
                self.log_test("Delete Paid Transaction Block", False, f"Exception: {str(e)}")
        else:
            self.log_test("Delete Paid Transaction Block", False, "No paid transaction available for testing")
    
    def test_process_delete_with_financial_transactions(self):
        """Test DELETE /api/processes/{process_id} with linked financial transactions"""
        print("\n=== Testing Process Delete with Financial Transactions ===")
        
        if not self.created_entities['processes']:
            self.log_test("Process Delete Prerequisites", False, "No processes available for testing")
            return
        
        process_id = self.created_entities['processes'][0]
        
        # Try to delete process that has linked financial transactions
        try:
            response = self.session.delete(f"{API_BASE_URL}/processes/{process_id}")
            if response.status_code == 400:
                error_message = response.json().get('detail', '')
                
                # Check if error message mentions financial transactions
                has_financial_mention = ('transação' in error_message.lower() or 
                                       'financeira' in error_message.lower())
                
                if has_financial_mention:
                    self.log_test("Process Delete Financial Block", True, 
                                f"Correctly blocked process deletion: {error_message}")
                else:
                    self.log_test("Process Delete Financial Block", False, 
                                f"Error message not specific about financial transactions: {error_message}")
            else:
                self.log_test("Process Delete Financial Block", False, 
                            f"Expected 400 status, got {response.status_code}")
        except Exception as e:
            self.log_test("Process Delete Financial Block", False, f"Exception: {str(e)}")
    
    def test_contract_delete(self):
        """Test DELETE /api/contracts/{contract_id}"""
        print("\n=== Testing Contract Delete ===")
        
        if not self.created_entities['contracts']:
            self.log_test("Contract Delete Prerequisites", False, "No contracts available for testing")
            return
        
        # Create a separate contract for deletion test
        client_id = self.created_entities['clients'][0]
        contract_data = {
            "client_id": client_id,
            "value": 5000.00,
            "payment_conditions": "Pagamento à vista",
            "installments": 1
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/contracts", json=contract_data)
            if response.status_code == 200:
                contract = response.json()
                contract_id = contract['id']
                
                # Now try to delete it
                delete_response = self.session.delete(f"{API_BASE_URL}/contracts/{contract_id}")
                if delete_response.status_code == 200:
                    self.log_test("Contract Delete", True, "Successfully deleted contract")
                elif delete_response.status_code == 405:
                    self.log_test("Contract Delete", False, 
                                "DELETE endpoint not implemented for contracts (405 Method Not Allowed)")
                else:
                    self.log_test("Contract Delete", False, 
                                f"Expected 200, got {delete_response.status_code}: {delete_response.text}")
            else:
                self.log_test("Contract Delete Setup", False, f"Failed to create test contract: {response.status_code}")
        except Exception as e:
            self.log_test("Contract Delete", False, f"Exception: {str(e)}")
    
    def test_lawyer_management_endpoints(self):
        """Test lawyer management endpoints (admin only)"""
        print("\n=== Testing Lawyer Management Endpoints (Admin Only) ===")
        
        # Test 1: GET /api/lawyers
        try:
            response = self.session.get(f"{API_BASE_URL}/lawyers")
            if response.status_code == 200:
                lawyers = response.json()
                self.log_test("Get Lawyers (Admin)", True, f"Retrieved {len(lawyers)} lawyers")
            else:
                self.log_test("Get Lawyers (Admin)", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Get Lawyers (Admin)", False, f"Exception: {str(e)}")
        
        # Test 2: POST /api/lawyers
        lawyer_data = {
            "full_name": "Dr. Carlos Eduardo Silva",
            "oab_number": "123456",
            "oab_state": "SP",
            "email": "carlos.silva@teste.com",
            "phone": "(11) 99999-1111",
            "specialization": "Direito Civil"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/lawyers", json=lawyer_data)
            if response.status_code == 200:
                lawyer = response.json()
                self.created_entities['lawyers'].append(lawyer['id'])
                self.log_test("Create Lawyer (Admin)", True, f"Created lawyer: {lawyer['full_name']}")
                
                # Verify required fields
                required_fields = ['id', 'full_name', 'oab_number', 'oab_state', 'email', 'phone']
                missing_fields = [field for field in required_fields if field not in lawyer]
                if missing_fields:
                    self.log_test("Lawyer Fields Validation", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Lawyer Fields Validation", True, "All required fields present")
            else:
                self.log_test("Create Lawyer (Admin)", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Create Lawyer (Admin)", False, f"Exception: {str(e)}")
        
        # Test 3: Test duplicate OAB validation
        duplicate_lawyer_data = {
            "full_name": "Dr. Maria Santos",
            "oab_number": "123456",  # Same OAB number
            "oab_state": "SP",       # Same state
            "email": "maria.santos@teste.com",
            "phone": "(11) 99999-2222",
            "specialization": "Direito Penal"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/lawyers", json=duplicate_lawyer_data)
            if response.status_code == 400:
                error_message = response.json().get('detail', '')
                if 'oab' in error_message.lower():
                    self.log_test("Duplicate OAB Validation", True, f"Correctly blocked duplicate OAB: {error_message}")
                else:
                    self.log_test("Duplicate OAB Validation", False, f"Error not specific about OAB: {error_message}")
            else:
                self.log_test("Duplicate OAB Validation", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Duplicate OAB Validation", False, f"Exception: {str(e)}")
        
        # Test 4: PUT /api/lawyers/{lawyer_id}
        if self.created_entities['lawyers']:
            lawyer_id = self.created_entities['lawyers'][0]
            update_data = {
                "full_name": "Dr. Carlos Eduardo Silva Junior",
                "oab_number": "123456",
                "oab_state": "SP",
                "email": "carlos.silva.jr@teste.com",
                "phone": "(11) 99999-3333",
                "specialization": "Direito Civil e Empresarial"
            }
            
            try:
                response = self.session.put(f"{API_BASE_URL}/lawyers/{lawyer_id}", json=update_data)
                if response.status_code == 200:
                    updated_lawyer = response.json()
                    if updated_lawyer['full_name'] == update_data['full_name']:
                        self.log_test("Update Lawyer (Admin)", True, "Lawyer updated successfully")
                    else:
                        self.log_test("Update Lawyer (Admin)", False, "Update data not reflected")
                else:
                    self.log_test("Update Lawyer (Admin)", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test("Update Lawyer (Admin)", False, f"Exception: {str(e)}")
        
        # Test 5: DELETE /api/lawyers/{lawyer_id} (soft delete)
        if self.created_entities['lawyers']:
            lawyer_id = self.created_entities['lawyers'][0]
            
            try:
                response = self.session.delete(f"{API_BASE_URL}/lawyers/{lawyer_id}")
                if response.status_code == 200:
                    self.log_test("Delete Lawyer (Admin)", True, "Lawyer deactivated successfully")
                    
                    # Verify lawyer is no longer in active list
                    get_response = self.session.get(f"{API_BASE_URL}/lawyers")
                    if get_response.status_code == 200:
                        active_lawyers = get_response.json()
                        deactivated_lawyer_ids = [l['id'] for l in active_lawyers if l['id'] == lawyer_id]
                        if not deactivated_lawyer_ids:
                            self.log_test("Lawyer Soft Delete Verification", True, "Deactivated lawyer not in active list")
                        else:
                            self.log_test("Lawyer Soft Delete Verification", False, "Deactivated lawyer still in active list")
                else:
                    self.log_test("Delete Lawyer (Admin)", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test("Delete Lawyer (Admin)", False, f"Exception: {str(e)}")
    
    def test_lawyer_endpoints_without_admin(self):
        """Test lawyer endpoints without admin authentication"""
        print("\n=== Testing Lawyer Endpoints Without Admin Auth ===")
        
        # Remove admin token temporarily
        original_auth = self.session.headers.get('Authorization')
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        
        # Test POST without auth
        lawyer_data = {
            "full_name": "Dr. Unauthorized Test",
            "oab_number": "999999",
            "oab_state": "RJ",
            "email": "unauthorized@teste.com",
            "phone": "(21) 99999-9999"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/lawyers", json=lawyer_data)
            if response.status_code in [401, 403]:  # Both are valid for unauthorized access
                self.log_test("Lawyer Create Without Auth", True, "Correctly blocked unauthorized access")
            else:
                self.log_test("Lawyer Create Without Auth", False, f"Expected 401/403, got {response.status_code}")
        except Exception as e:
            self.log_test("Lawyer Create Without Auth", False, f"Exception: {str(e)}")
        
        # Restore admin token
        if original_auth:
            self.session.headers['Authorization'] = original_auth
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n=== Cleaning Up Test Data ===")
        
        # Delete remaining financial transactions
        for transaction_id in self.created_entities['financial_transactions']:
            try:
                response = self.session.delete(f"{API_BASE_URL}/financial/{transaction_id}")
                if response.status_code == 200:
                    print(f"✅ Deleted transaction: {transaction_id}")
                else:
                    print(f"❌ Failed to delete transaction {transaction_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Exception deleting transaction {transaction_id}: {str(e)}")
        
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
        """Run all delete endpoint tests"""
        print(f"🚀 Starting Delete Endpoints Tests for GB Advocacia & N. Comin")
        print(f"📡 Backend URL: {API_BASE_URL}")
        print("=" * 80)
        
        # Authenticate as admin
        if not self.authenticate_admin():
            print("❌ Failed to authenticate as admin. Cannot proceed with tests.")
            return 0, 1, 1
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Cannot proceed with tests.")
            return 0, 1, 1
        
        try:
            # Run specific delete endpoint tests
            self.test_client_delete_with_dependencies()
            self.test_financial_transaction_delete_restrictions()
            self.test_process_delete_with_financial_transactions()
            self.test_contract_delete()
            
            # Run lawyer management tests
            self.test_lawyer_management_endpoints()
            self.test_lawyer_endpoints_without_admin()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Print final results
        print("\n" + "=" * 80)
        print("🏁 DELETE ENDPOINTS TEST RESULTS")
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
    """Main function to run delete endpoint tests"""
    tester = DeleteEndpointsTester()
    passed, failed, total = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()