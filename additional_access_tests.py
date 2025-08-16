#!/usr/bin/env python3
"""
Additional Access Control Tests - Specific scenarios from review request
"""

import requests
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://lawfirm-upgrade.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

class AdditionalAccessTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.auth_tokens = {}
        self.created_entities = {'lawyers': [], 'clients': [], 'processes': [], 'financial_transactions': []}
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
    
    def setup_test_environment(self):
        """Setup test environment with admin login and branches"""
        # Login as admin
        login_data = {"username_or_email": "admin", "password": "admin123"}
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_tokens['admin'] = token_data['access_token']
                self.log_test("Admin Login Setup", True, "Admin logged in successfully")
            else:
                self.log_test("Admin Login Setup", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin Login Setup", False, f"Exception: {str(e)}")
            return False
        
        # Get branches
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
                self.log_test("Branches Setup", True, f"Retrieved {len(branches)} branches")
                return True
            else:
                self.log_test("Branches Setup", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Branches Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_scenario_admin_total_access(self):
        """Test: Login como admin: total acesso"""
        print("\n=== Testing Admin Total Access Scenario ===")
        
        admin_header = {'Authorization': f'Bearer {self.auth_tokens["admin"]}'}
        
        # Test access to all major endpoints
        endpoints_to_test = [
            ("/clients", "GET"),
            ("/processes", "GET"),
            ("/financial", "GET"),
            ("/contracts", "GET"),
            ("/lawyers", "GET"),
            ("/dashboard", "GET"),
            ("/auth/permissions", "GET"),
            ("/security/report", "GET")
        ]
        
        accessible_endpoints = 0
        for endpoint, method in endpoints_to_test:
            try:
                if method == "GET":
                    response = self.session.get(f"{API_BASE_URL}{endpoint}", headers=admin_header)
                
                if response.status_code == 200:
                    accessible_endpoints += 1
                    self.log_test(f"Admin Access {endpoint}", True, f"Admin can access {endpoint}")
                else:
                    self.log_test(f"Admin Access {endpoint}", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Admin Access {endpoint}", False, f"Exception: {str(e)}")
        
        if accessible_endpoints >= 7:  # Should access most endpoints
            self.log_test("Admin Total Access", True, f"Admin has access to {accessible_endpoints}/{len(endpoints_to_test)} endpoints")
        else:
            self.log_test("Admin Total Access", False, f"Admin only has access to {accessible_endpoints}/{len(endpoints_to_test)} endpoints")
    
    def test_scenario_create_restricted_lawyer(self):
        """Test: Criar advogado com permissões limitadas"""
        print("\n=== Testing Create Restricted Lawyer Scenario ===")
        
        if not self.branch_ids.get('caxias'):
            self.log_test("Create Restricted Lawyer Prerequisites", False, "No branch available")
            return None
        
        # Generate unique identifiers
        unique_id = int(time.time()) % 1000000
        
        lawyer_data = {
            "full_name": "Dr. Advogado Limitado Teste",
            "oab_number": f"{unique_id}",
            "oab_state": "RS",
            "email": f"advogado.limitado.{unique_id}@gbadvocacia.com",
            "phone": "(54) 99999-1111",
            "specialization": "Direito Civil",
            "branch_id": self.branch_ids['caxias'],
            "access_financial_data": False,  # LIMITED: No financial access
            "allowed_branch_ids": [self.branch_ids['caxias']]  # LIMITED: Only one branch
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/lawyers", 
                                       json=lawyer_data,
                                       headers={'Authorization': f'Bearer {self.auth_tokens["admin"]}'})
            if response.status_code == 200:
                lawyer = response.json()
                self.created_entities['lawyers'].append(lawyer['id'])
                self.log_test("Create Restricted Lawyer", True, f"Created restricted lawyer: {lawyer['full_name']}")
                
                # Verify restrictions are applied
                if lawyer.get('access_financial_data') == False:
                    self.log_test("Financial Access Restriction Applied", True, "access_financial_data correctly set to False")
                else:
                    self.log_test("Financial Access Restriction Applied", False, f"Expected False, got {lawyer.get('access_financial_data')}")
                
                return lawyer
            else:
                self.log_test("Create Restricted Lawyer", False, f"HTTP {response.status_code}", response.text)
                return None
        except Exception as e:
            self.log_test("Create Restricted Lawyer", False, f"Exception: {str(e)}")
            return None
    
    def test_scenario_restricted_lawyer_login_and_test(self, lawyer):
        """Test: Login como advogado limitado e teste restrições"""
        print("\n=== Testing Restricted Lawyer Login and Restrictions ===")
        
        if not lawyer:
            self.log_test("Restricted Lawyer Login Prerequisites", False, "No lawyer data available")
            return
        
        # Login as restricted lawyer
        login_data = {
            "username_or_email": lawyer['email'],
            "password": lawyer['oab_number']
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_tokens['restricted_lawyer'] = token_data['access_token']
                self.log_test("Restricted Lawyer Login", True, f"Logged in as: {token_data['user']['full_name']}")
                
                restricted_header = {'Authorization': f'Bearer {self.auth_tokens["restricted_lawyer"]}'}
                
                # Test financial restrictions
                financial_endpoints = [
                    "/financial",
                    "/financial"  # Test both GET and POST would be here
                ]
                
                for endpoint in financial_endpoints:
                    try:
                        response = self.session.get(f"{API_BASE_URL}{endpoint}", headers=restricted_header)
                        if response.status_code == 403:
                            self.log_test(f"Financial Restriction {endpoint}", True, "Correctly blocked financial access")
                        else:
                            self.log_test(f"Financial Restriction {endpoint}", False, f"Expected 403, got {response.status_code}")
                    except Exception as e:
                        self.log_test(f"Financial Restriction {endpoint}", False, f"Exception: {str(e)}")
                
                # Test task creation restriction
                task_data = {
                    "title": "Tarefa Teste Restrita",
                    "description": "Teste de criação por advogado restrito",
                    "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
                    "priority": "medium",
                    "status": "pending",
                    "assigned_lawyer_id": lawyer['id'],
                    "branch_id": self.branch_ids.get('caxias', 'test-branch')
                }
                
                try:
                    response = self.session.post(f"{API_BASE_URL}/tasks", json=task_data, headers=restricted_header)
                    if response.status_code == 403:
                        self.log_test("Task Creation Restriction", True, "Correctly blocked task creation by lawyer")
                    else:
                        self.log_test("Task Creation Restriction", False, f"Expected 403, got {response.status_code}")
                except Exception as e:
                    self.log_test("Task Creation Restriction", False, f"Exception: {str(e)}")
                
                # Test that lawyer can still access basic endpoints
                basic_endpoints = ["/clients", "/processes", "/contracts"]
                accessible_basic = 0
                
                for endpoint in basic_endpoints:
                    try:
                        response = self.session.get(f"{API_BASE_URL}{endpoint}", headers=restricted_header)
                        if response.status_code == 200:
                            accessible_basic += 1
                            self.log_test(f"Basic Access {endpoint}", True, f"Lawyer can access {endpoint}")
                        else:
                            self.log_test(f"Basic Access {endpoint}", False, f"HTTP {response.status_code}")
                    except Exception as e:
                        self.log_test(f"Basic Access {endpoint}", False, f"Exception: {str(e)}")
                
                if accessible_basic >= 2:
                    self.log_test("Basic Endpoints Access", True, f"Lawyer can access {accessible_basic}/{len(basic_endpoints)} basic endpoints")
                else:
                    self.log_test("Basic Endpoints Access", False, f"Lawyer only has access to {accessible_basic}/{len(basic_endpoints)} basic endpoints")
                    
            else:
                self.log_test("Restricted Lawyer Login", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Restricted Lawyer Login", False, f"Exception: {str(e)}")
    
    def test_scenario_unauthorized_access_attempts(self):
        """Test: Teste tentativas de acesso não autorizado"""
        print("\n=== Testing Unauthorized Access Attempts ===")
        
        if 'restricted_lawyer' not in self.auth_tokens:
            self.log_test("Unauthorized Access Prerequisites", False, "No restricted lawyer token available")
            return
        
        restricted_header = {'Authorization': f'Bearer {self.auth_tokens["restricted_lawyer"]}'}
        
        # Test unauthorized endpoints for lawyers
        unauthorized_endpoints = [
            ("/lawyers", "GET", "Lawyer management"),
            ("/security/report", "GET", "Security reports"),
            ("/lawyers", "POST", "Lawyer creation")
        ]
        
        blocked_attempts = 0
        for endpoint, method, description in unauthorized_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{API_BASE_URL}{endpoint}", headers=restricted_header)
                elif method == "POST":
                    # Try to create a lawyer (should be blocked)
                    test_data = {
                        "full_name": "Test Unauthorized",
                        "oab_number": "999999",
                        "oab_state": "RS",
                        "email": "unauthorized@test.com",
                        "phone": "(54) 99999-9999",
                        "branch_id": self.branch_ids.get('caxias', 'test-branch')
                    }
                    response = self.session.post(f"{API_BASE_URL}{endpoint}", json=test_data, headers=restricted_header)
                
                if response.status_code == 403:
                    blocked_attempts += 1
                    self.log_test(f"Block Unauthorized {description}", True, f"Correctly blocked {method} {endpoint}")
                else:
                    self.log_test(f"Block Unauthorized {description}", False, f"Expected 403, got {response.status_code}")
            except Exception as e:
                self.log_test(f"Block Unauthorized {description}", False, f"Exception: {str(e)}")
        
        if blocked_attempts >= 2:
            self.log_test("Unauthorized Access Protection", True, f"Blocked {blocked_attempts}/{len(unauthorized_endpoints)} unauthorized attempts")
        else:
            self.log_test("Unauthorized Access Protection", False, f"Only blocked {blocked_attempts}/{len(unauthorized_endpoints)} unauthorized attempts")
    
    def test_scenario_portuguese_error_validation(self):
        """Test: Validação de mensagens de erro em português"""
        print("\n=== Testing Portuguese Error Message Validation ===")
        
        if 'restricted_lawyer' not in self.auth_tokens:
            self.log_test("Portuguese Error Prerequisites", False, "No restricted lawyer token available")
            return
        
        restricted_header = {'Authorization': f'Bearer {self.auth_tokens["restricted_lawyer"]}'}
        
        # Test financial access error message
        try:
            response = self.session.get(f"{API_BASE_URL}/financial", headers=restricted_header)
            if response.status_code == 403:
                error_text = response.text.lower()
                portuguese_keywords = ['permissão', 'acesso', 'negado', 'financeiro', 'dados', 'administrador']
                found_keywords = [keyword for keyword in portuguese_keywords if keyword in error_text]
                
                if len(found_keywords) >= 3:
                    self.log_test("Portuguese Financial Error", True, f"Error message in Portuguese with keywords: {found_keywords}")
                else:
                    self.log_test("Portuguese Financial Error", False, f"Error message may not be in Portuguese: {response.text}")
            else:
                self.log_test("Portuguese Financial Error", False, f"Expected 403 error, got {response.status_code}")
        except Exception as e:
            self.log_test("Portuguese Financial Error", False, f"Exception: {str(e)}")
        
        # Test task creation error message
        task_data = {
            "title": "Test Task",
            "assigned_lawyer_id": "test-id",
            "branch_id": "test-branch"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/tasks", json=task_data, headers=restricted_header)
            if response.status_code == 403:
                error_text = response.text.lower()
                portuguese_keywords = ['apenas', 'administradores', 'podem', 'criar', 'tarefas']
                found_keywords = [keyword for keyword in portuguese_keywords if keyword in error_text]
                
                if len(found_keywords) >= 3:
                    self.log_test("Portuguese Task Error", True, f"Task error message in Portuguese with keywords: {found_keywords}")
                else:
                    self.log_test("Portuguese Task Error", False, f"Task error message may not be in Portuguese: {response.text}")
            else:
                self.log_test("Portuguese Task Error", False, f"Expected 403 error, got {response.status_code}")
        except Exception as e:
            self.log_test("Portuguese Task Error", False, f"Exception: {str(e)}")
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n=== Cleaning Up Additional Test Data ===")
        
        if 'admin' not in self.auth_tokens:
            return
        
        admin_header = {'Authorization': f'Bearer {self.auth_tokens["admin"]}'}
        
        # Deactivate lawyers
        for lawyer_id in self.created_entities['lawyers']:
            try:
                response = self.session.delete(f"{API_BASE_URL}/lawyers/{lawyer_id}", headers=admin_header)
                if response.status_code == 200:
                    print(f"✅ Deactivated lawyer: {lawyer_id}")
                else:
                    print(f"❌ Failed to deactivate lawyer {lawyer_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Exception deactivating lawyer {lawyer_id}: {str(e)}")
    
    def run_additional_tests(self):
        """Run all additional access control tests"""
        print("🔍 ADDITIONAL ACCESS CONTROL TESTS - SPECIFIC SCENARIOS")
        print("=" * 80)
        
        try:
            # Setup
            if not self.setup_test_environment():
                return self.test_results
            
            # Test scenarios from review request
            self.test_scenario_admin_total_access()
            
            restricted_lawyer = self.test_scenario_create_restricted_lawyer()
            if restricted_lawyer:
                self.test_scenario_restricted_lawyer_login_and_test(restricted_lawyer)
                self.test_scenario_unauthorized_access_attempts()
                self.test_scenario_portuguese_error_validation()
            
        finally:
            # Cleanup
            self.cleanup_test_data()
        
        return self.test_results
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🔍 ADDITIONAL ACCESS CONTROL TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['message']}")
        
        return success_rate >= 85

def main():
    """Main test execution"""
    tester = AdditionalAccessTester()
    
    try:
        results = tester.run_additional_tests()
        success = tester.print_summary()
        
        if success:
            print(f"\n🎉 ADDITIONAL ACCESS CONTROL TESTS PASSED!")
            sys.exit(0)
        else:
            print(f"\n🚨 ADDITIONAL ACCESS CONTROL TESTS HAVE ISSUES!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed with exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()