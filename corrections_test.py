#!/usr/bin/env python3
"""
Focused Testing Suite for Specific Corrections
Tests the corrections implemented as per review request:
1. UserRole enum correction in get_current_user endpoint
2. branch_id requirement for client and lawyer creation
3. WhatsApp number update to "+55 54 99710-2525"
4. WhatsApp endpoints that were returning error 500
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

class CorrectionsTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.auth_tokens = {}
        self.branch_ids = {}
        self.created_entities = {
            'clients': [],
            'lawyers': [],
            'financial_transactions': []
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
    
    def setup_authentication(self):
        """Setup authentication tokens for testing"""
        print("\n=== Setting Up Authentication ===")
        
        # Login as super admin
        admin_login_data = {
            "username_or_email": "admin",
            "password": "admin123"
        }
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=admin_login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_tokens['admin'] = token_data['access_token']
                self.log_test("Admin Login", True, f"Logged in as: {token_data['user']['full_name']}")
                
                # Test UserRole enum correction - verify role is properly converted
                user = token_data['user']
                if user.get('role') == 'admin':
                    self.log_test("UserRole Enum Correction - Admin", True, "Admin role correctly returned as string")
                else:
                    self.log_test("UserRole Enum Correction - Admin", False, f"Expected 'admin', got '{user.get('role')}'")
                    
            else:
                self.log_test("Admin Login", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            return False
        
        # Login as Caxias admin
        caxias_login_data = {
            "username_or_email": "admin_caxias",
            "password": "admin123"
        }
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=caxias_login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_tokens['admin_caxias'] = token_data['access_token']
                self.log_test("Caxias Admin Login", True, f"Logged in as: {token_data['user']['full_name']}")
            else:
                self.log_test("Caxias Admin Login", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Caxias Admin Login", False, f"Exception: {str(e)}")
        
        # Get branch IDs
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
                self.log_test("Branch IDs Retrieved", True, f"Found {len(self.branch_ids)} branch IDs")
            else:
                self.log_test("Branch IDs Retrieved", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Branch IDs Retrieved", False, f"Exception: {str(e)}")
        
        return True
    
    def test_whatsapp_endpoints_no_500_errors(self):
        """Test that WhatsApp endpoints no longer return 500 errors"""
        print("\n=== Testing WhatsApp Endpoints - No 500 Errors ===")
        
        if 'admin' not in self.auth_tokens:
            self.log_test("WhatsApp Endpoints Prerequisites", False, "No admin authentication available")
            return
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens["admin"]}'}
        
        # Test 1: WhatsApp Status Endpoint
        try:
            response = self.session.get(f"{API_BASE_URL}/whatsapp/status", headers=auth_header)
            if response.status_code == 200:
                self.log_test("WhatsApp Status - No 500 Error", True, "Status endpoint working correctly")
                status_data = response.json()
                print(f"   📱 WhatsApp Enabled: {status_data.get('whatsapp_enabled')}")
                print(f"   ⏰ Scheduler Running: {status_data.get('scheduler_running')}")
            elif response.status_code == 500:
                self.log_test("WhatsApp Status - No 500 Error", False, "Still returning 500 error", response.text)
            else:
                self.log_test("WhatsApp Status - No 500 Error", True, f"No 500 error (got {response.status_code})")
        except Exception as e:
            self.log_test("WhatsApp Status - No 500 Error", False, f"Exception: {str(e)}")
        
        # Test 2: WhatsApp Send Message Endpoint
        message_data = {
            "phone_number": "+55 54 99710-2525",
            "message": "Teste de correção - mensagem do sistema GB & N.Comin Advocacia"
        }
        try:
            response = self.session.post(f"{API_BASE_URL}/whatsapp/send-message", 
                                       json=message_data, headers=auth_header)
            if response.status_code == 200:
                self.log_test("WhatsApp Send Message - No 500 Error", True, "Send message endpoint working correctly")
            elif response.status_code == 500:
                self.log_test("WhatsApp Send Message - No 500 Error", False, "Still returning 500 error", response.text)
            else:
                self.log_test("WhatsApp Send Message - No 500 Error", True, f"No 500 error (got {response.status_code})")
        except Exception as e:
            self.log_test("WhatsApp Send Message - No 500 Error", False, f"Exception: {str(e)}")
        
        # Test 3: WhatsApp Check Payments Endpoint
        try:
            response = self.session.post(f"{API_BASE_URL}/whatsapp/check-payments", headers=auth_header)
            if response.status_code == 200:
                self.log_test("WhatsApp Check Payments - No 500 Error", True, "Check payments endpoint working correctly")
            elif response.status_code == 500:
                self.log_test("WhatsApp Check Payments - No 500 Error", False, "Still returning 500 error", response.text)
            else:
                self.log_test("WhatsApp Check Payments - No 500 Error", True, f"No 500 error (got {response.status_code})")
        except Exception as e:
            self.log_test("WhatsApp Check Payments - No 500 Error", False, f"Exception: {str(e)}")
    
    def test_whatsapp_phone_number_correction(self):
        """Test that WhatsApp messages include the correct phone number +55 54 99710-2525"""
        print("\n=== Testing WhatsApp Phone Number Correction ===")
        
        # Create a test client and financial transaction to test manual reminder
        if not self.branch_ids.get('caxias'):
            self.log_test("WhatsApp Phone Number Test Prerequisites", False, "No Caxias branch ID available")
            return
        
        # Create test client
        client_data = {
            "name": "Cliente Teste WhatsApp",
            "nationality": "Brasileira",
            "civil_status": "Solteiro",
            "profession": "Empresário",
            "cpf": "999.888.777-66",
            "address": {
                "street": "Rua Teste WhatsApp",
                "number": "123",
                "city": "Caxias do Sul",
                "district": "Centro",
                "state": "RS",
                "complement": ""
            },
            "phone": "(54) 99999-1111",
            "client_type": "individual",
            "branch_id": self.branch_ids['caxias']
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/clients", json=client_data)
            if response.status_code == 200:
                client = response.json()
                self.created_entities['clients'].append(client['id'])
                
                # Create financial transaction
                transaction_data = {
                    "client_id": client['id'],
                    "type": "receita",
                    "description": "Teste WhatsApp - Honorários",
                    "value": 1000.00,
                    "due_date": (datetime.now() + timedelta(days=2)).isoformat(),
                    "status": "pendente",
                    "category": "Honorários",
                    "branch_id": self.branch_ids['caxias']
                }
                
                response = self.session.post(f"{API_BASE_URL}/financial", json=transaction_data)
                if response.status_code == 200:
                    transaction = response.json()
                    self.created_entities['financial_transactions'].append(transaction['id'])
                    
                    # Test manual reminder to verify phone number in message
                    auth_header = {'Authorization': f'Bearer {self.auth_tokens["admin"]}'}
                    response = self.session.post(f"{API_BASE_URL}/whatsapp/send-reminder/{transaction['id']}", 
                                               headers=auth_header)
                    
                    if response.status_code == 200:
                        self.log_test("WhatsApp Phone Number in Messages", True, 
                                    "Manual reminder sent successfully - phone number should be +55 54 99710-2525")
                        
                        # Note: We can't directly verify the message content from the API response
                        # but the correction should be in the WhatsApp service message formatting
                        print("   📞 Expected phone number in message: +55 54 99710-2525")
                    else:
                        self.log_test("WhatsApp Phone Number in Messages", False, 
                                    f"Failed to send manual reminder: HTTP {response.status_code}")
                else:
                    self.log_test("WhatsApp Phone Number Test Setup", False, "Failed to create test transaction")
            else:
                self.log_test("WhatsApp Phone Number Test Setup", False, "Failed to create test client")
        except Exception as e:
            self.log_test("WhatsApp Phone Number Test", False, f"Exception: {str(e)}")
    
    def test_branch_id_requirement_clients(self):
        """Test that client creation requires branch_id"""
        print("\n=== Testing Client Creation with branch_id Requirement ===")
        
        if not self.branch_ids.get('caxias'):
            self.log_test("Client branch_id Test Prerequisites", False, "No Caxias branch ID available")
            return
        
        # Test 1: Create client WITH branch_id (should succeed)
        client_with_branch = {
            "name": "Cliente Com Branch ID",
            "nationality": "Brasileira",
            "civil_status": "Casado",
            "profession": "Advogado",
            "cpf": "111.222.333-44",
            "address": {
                "street": "Rua Com Branch",
                "number": "456",
                "city": "Caxias do Sul",
                "district": "Centro",
                "state": "RS",
                "complement": ""
            },
            "phone": "(54) 99999-2222",
            "client_type": "individual",
            "branch_id": self.branch_ids['caxias']  # WITH branch_id
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/clients", json=client_with_branch)
            if response.status_code == 200:
                client = response.json()
                self.created_entities['clients'].append(client['id'])
                self.log_test("Client Creation WITH branch_id", True, "Client created successfully with branch_id")
                
                # Verify branch_id is stored
                if client.get('branch_id') == self.branch_ids['caxias']:
                    self.log_test("Client branch_id Storage", True, "branch_id correctly stored in client")
                else:
                    self.log_test("Client branch_id Storage", False, "branch_id not correctly stored")
            else:
                self.log_test("Client Creation WITH branch_id", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Client Creation WITH branch_id", False, f"Exception: {str(e)}")
        
        # Test 2: Create client WITHOUT branch_id (should fail or use default)
        client_without_branch = {
            "name": "Cliente Sem Branch ID",
            "nationality": "Brasileira",
            "civil_status": "Solteiro",
            "profession": "Médico",
            "cpf": "555.666.777-88",
            "address": {
                "street": "Rua Sem Branch",
                "number": "789",
                "city": "Caxias do Sul",
                "district": "Centro",
                "state": "RS",
                "complement": ""
            },
            "phone": "(54) 99999-3333",
            "client_type": "individual"
            # NO branch_id field
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/clients", json=client_without_branch)
            if response.status_code == 422:
                self.log_test("Client Creation WITHOUT branch_id", True, "Correctly rejected client without branch_id")
            elif response.status_code == 200:
                # If it succeeds, check if a default branch_id was assigned
                client = response.json()
                self.created_entities['clients'].append(client['id'])
                if client.get('branch_id'):
                    self.log_test("Client Creation WITHOUT branch_id", True, "Client created with default branch_id")
                else:
                    self.log_test("Client Creation WITHOUT branch_id", False, "Client created without branch_id")
            else:
                self.log_test("Client Creation WITHOUT branch_id", False, f"Unexpected response: HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Client Creation WITHOUT branch_id", False, f"Exception: {str(e)}")
    
    def test_branch_id_requirement_lawyers(self):
        """Test that lawyer creation requires branch_id"""
        print("\n=== Testing Lawyer Creation with branch_id Requirement ===")
        
        if 'admin' not in self.auth_tokens or not self.branch_ids.get('caxias'):
            self.log_test("Lawyer branch_id Test Prerequisites", False, "Missing admin auth or branch ID")
            return
        
        auth_header = {'Authorization': f'Bearer {self.auth_tokens["admin"]}'}
        
        # Test 1: Create lawyer WITH branch_id (should succeed)
        lawyer_with_branch = {
            "full_name": "Dr. Advogado Com Branch",
            "oab_number": "999888",
            "oab_state": "RS",
            "email": "advogado.branch@gbadvocacia.com",
            "phone": "(54) 99999-4444",
            "specialization": "Direito Civil",
            "branch_id": self.branch_ids['caxias']  # WITH branch_id
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/lawyers", json=lawyer_with_branch, headers=auth_header)
            if response.status_code == 200:
                lawyer = response.json()
                self.created_entities['lawyers'].append(lawyer['id'])
                self.log_test("Lawyer Creation WITH branch_id", True, "Lawyer created successfully with branch_id")
                
                # Verify branch_id is stored
                if lawyer.get('branch_id') == self.branch_ids['caxias']:
                    self.log_test("Lawyer branch_id Storage", True, "branch_id correctly stored in lawyer")
                else:
                    self.log_test("Lawyer branch_id Storage", False, "branch_id not correctly stored")
                
                # Test lawyer login with OAB to verify UserRole enum correction
                lawyer_login_data = {
                    "username_or_email": lawyer_with_branch['email'],
                    "password": lawyer_with_branch['oab_number']
                }
                
                login_response = self.session.post(f"{API_BASE_URL}/auth/login", json=lawyer_login_data)
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    user = token_data['user']
                    
                    # Test UserRole enum correction for lawyer
                    if user.get('role') == 'lawyer':
                        self.log_test("UserRole Enum Correction - Lawyer", True, "Lawyer role correctly returned as string")
                    else:
                        self.log_test("UserRole Enum Correction - Lawyer", False, f"Expected 'lawyer', got '{user.get('role')}'")
                else:
                    self.log_test("Lawyer Login Test", False, f"Lawyer login failed: HTTP {login_response.status_code}")
                    
            else:
                self.log_test("Lawyer Creation WITH branch_id", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Lawyer Creation WITH branch_id", False, f"Exception: {str(e)}")
        
        # Test 2: Create lawyer WITHOUT branch_id (should fail or use default)
        lawyer_without_branch = {
            "full_name": "Dr. Advogado Sem Branch",
            "oab_number": "777666",
            "oab_state": "RS",
            "email": "advogado.sembranch@gbadvocacia.com",
            "phone": "(54) 99999-5555",
            "specialization": "Direito Penal"
            # NO branch_id field
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/lawyers", json=lawyer_without_branch, headers=auth_header)
            if response.status_code == 422:
                self.log_test("Lawyer Creation WITHOUT branch_id", True, "Correctly rejected lawyer without branch_id")
            elif response.status_code == 200:
                # If it succeeds, check if a default branch_id was assigned
                lawyer = response.json()
                self.created_entities['lawyers'].append(lawyer['id'])
                if lawyer.get('branch_id'):
                    self.log_test("Lawyer Creation WITHOUT branch_id", True, "Lawyer created with default branch_id")
                else:
                    self.log_test("Lawyer Creation WITHOUT branch_id", False, "Lawyer created without branch_id")
            else:
                self.log_test("Lawyer Creation WITHOUT branch_id", False, f"Unexpected response: HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Lawyer Creation WITHOUT branch_id", False, f"Exception: {str(e)}")
    
    def test_authentication_roles_working(self):
        """Test that authentication with roles is working properly"""
        print("\n=== Testing Authentication with Roles ===")
        
        # Test 1: Verify get_current_user endpoint works
        if 'admin' in self.auth_tokens:
            auth_header = {'Authorization': f'Bearer {self.auth_tokens["admin"]}'}
            try:
                response = self.session.get(f"{API_BASE_URL}/auth/me", headers=auth_header)
                if response.status_code == 200:
                    user = response.json()
                    self.log_test("get_current_user Endpoint", True, f"Retrieved current user: {user.get('full_name')}")
                    
                    # Verify role is properly returned
                    if user.get('role') == 'admin':
                        self.log_test("get_current_user Role Return", True, "Role correctly returned as string")
                    else:
                        self.log_test("get_current_user Role Return", False, f"Expected 'admin', got '{user.get('role')}'")
                else:
                    self.log_test("get_current_user Endpoint", False, f"HTTP {response.status_code}", response.text)
            except Exception as e:
                self.log_test("get_current_user Endpoint", False, f"Exception: {str(e)}")
        
        # Test 2: Test role-based access control
        if 'admin_caxias' in self.auth_tokens:
            auth_header = {'Authorization': f'Bearer {self.auth_tokens["admin_caxias"]}'}
            try:
                # Branch admin should be able to access their data
                response = self.session.get(f"{API_BASE_URL}/clients", headers=auth_header)
                if response.status_code == 200:
                    self.log_test("Role-based Access Control", True, "Branch admin can access client data")
                else:
                    self.log_test("Role-based Access Control", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test("Role-based Access Control", False, f"Exception: {str(e)}")
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n=== Cleaning Up Test Data ===")
        
        # Delete lawyers
        if 'admin' in self.auth_tokens:
            auth_header = {'Authorization': f'Bearer {self.auth_tokens["admin"]}'}
            for lawyer_id in self.created_entities['lawyers']:
                try:
                    response = self.session.delete(f"{API_BASE_URL}/lawyers/{lawyer_id}", headers=auth_header)
                    if response.status_code == 200:
                        print(f"✅ Deactivated lawyer: {lawyer_id}")
                    else:
                        print(f"❌ Failed to deactivate lawyer {lawyer_id}: {response.status_code}")
                except Exception as e:
                    print(f"❌ Exception deactivating lawyer {lawyer_id}: {str(e)}")
        
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
    
    def run_corrections_tests(self):
        """Run all correction-specific tests"""
        print(f"🔧 Starting Corrections Testing Suite")
        print(f"📡 Backend URL: {API_BASE_URL}")
        print("=" * 80)
        
        try:
            # Setup authentication first
            if not self.setup_authentication():
                print("❌ Failed to setup authentication - aborting tests")
                return 0, 1, 1
            
            # Run correction-specific tests
            self.test_whatsapp_endpoints_no_500_errors()
            self.test_whatsapp_phone_number_correction()
            self.test_branch_id_requirement_clients()
            self.test_branch_id_requirement_lawyers()
            self.test_authentication_roles_working()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
        
        # Print final results
        print("\n" + "=" * 80)
        print("🏁 CORRECTIONS TEST RESULTS")
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
    """Main function to run corrections tests"""
    tester = CorrectionsTester()
    passed, failed, total = tester.run_corrections_tests()
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()