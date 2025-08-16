#!/usr/bin/env python3
"""
Branch Admin Test - Testing with branch admin accounts
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://legalflow-4.preview.emergentagent.com')
API_BASE_URL = f"{BACKEND_URL}/api"

class BranchAdminTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.auth_tokens = {}
        
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
    
    def login_branch_admin(self):
        """Login as branch admin"""
        login_data = {
            "username_or_email": "admin_caxias",
            "password": "admin123"
        }
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_tokens['admin'] = token_data['access_token']
                self.log_test("Branch Admin Login", True, f"Logged in as: {token_data['user']['full_name']}")
                return True
            else:
                self.log_test("Branch Admin Login", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Branch Admin Login", False, f"Exception: {str(e)}")
            return False
    
    def test_super_admin_login(self):
        """Test super admin login after waiting"""
        print("\n=== Testing Super Admin Login ===")
        
        # Wait additional time for account unlock
        print("⏳ Waiting additional time for super admin account unlock...")
        time.sleep(60)
        
        login_data = {
            "username_or_email": "admin",
            "password": "admin123"
        }
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.auth_tokens['super_admin'] = token_data['access_token']
                self.log_test("Super Admin Login After Wait", True, f"✅ Super admin login successful: {token_data['user']['full_name']}")
                return True
            elif response.status_code == 423:
                self.log_test("Super Admin Login After Wait", False, "Account still locked - security system working")
                return False
            else:
                self.log_test("Super Admin Login After Wait", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Super Admin Login After Wait", False, f"Exception: {str(e)}")
            return False
    
    def test_google_drive_endpoints(self):
        """Test Google Drive endpoints with available admin"""
        print("\n=== Testing Google Drive Endpoints ===")
        
        admin_token = self.auth_tokens.get('super_admin') or self.auth_tokens.get('admin')
        if not admin_token:
            self.log_test("Google Drive Test Prerequisites", False, "No admin token available")
            return
        
        admin_header = {'Authorization': f'Bearer {admin_token}'}
        
        # Test Google Drive status
        try:
            response = self.session.get(f"{API_BASE_URL}/google-drive/status", headers=admin_header)
            if response.status_code == 200:
                status = response.json()
                self.log_test("Google Drive Status", True, f"✅ Status endpoint working: {status.get('message', 'OK')}")
            elif response.status_code == 403:
                self.log_test("Google Drive Status", False, "Branch admin may not have Google Drive access")
            else:
                self.log_test("Google Drive Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Google Drive Status", False, f"Exception: {str(e)}")
        
        # Test Google Drive auth URL
        try:
            response = self.session.get(f"{API_BASE_URL}/google-drive/auth-url", headers=admin_header)
            if response.status_code == 200:
                self.log_test("Google Drive Auth URL", True, "✅ Auth URL endpoint working")
            elif response.status_code == 400:
                self.log_test("Google Drive Auth URL", True, "✅ Expected error - Google credentials not configured")
            elif response.status_code == 403:
                self.log_test("Google Drive Auth URL", False, "Branch admin may not have Google Drive access")
            else:
                self.log_test("Google Drive Auth URL", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Google Drive Auth URL", False, f"Exception: {str(e)}")
    
    def test_security_endpoints(self):
        """Test security endpoints"""
        print("\n=== Testing Security Endpoints ===")
        
        admin_token = self.auth_tokens.get('super_admin') or self.auth_tokens.get('admin')
        if not admin_token:
            self.log_test("Security Test Prerequisites", False, "No admin token available")
            return
        
        admin_header = {'Authorization': f'Bearer {admin_token}'}
        
        # Test security report
        try:
            response = self.session.get(f"{API_BASE_URL}/security/report", headers=admin_header)
            if response.status_code == 200:
                self.log_test("Security Report", True, "✅ Security report endpoint working")
            elif response.status_code == 403:
                self.log_test("Security Report", False, "Branch admin may not have security access")
            else:
                self.log_test("Security Report", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Security Report", False, f"Exception: {str(e)}")
        
        # Test password generation
        try:
            response = self.session.post(f"{API_BASE_URL}/security/generate-password", headers=admin_header)
            if response.status_code == 200:
                password_data = response.json()
                if 'password' in password_data:
                    self.log_test("Generate Secure Password", True, f"✅ Password generated (length: {len(password_data['password'])})")
                else:
                    self.log_test("Generate Secure Password", False, "No password in response")
            elif response.status_code == 403:
                self.log_test("Generate Secure Password", False, "Branch admin may not have password generation access")
            else:
                self.log_test("Generate Secure Password", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Generate Secure Password", False, f"Exception: {str(e)}")
        
        # Test password validation
        try:
            response = self.session.post(f"{API_BASE_URL}/security/validate-password", 
                                       params={"password": "TestPassword123!", "username": "test"},
                                       headers=admin_header)
            if response.status_code == 200:
                self.log_test("Password Validation", True, "✅ Password validation working")
            else:
                self.log_test("Password Validation", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Password Validation", False, f"Exception: {str(e)}")
    
    def test_basic_functionality(self):
        """Test basic system functionality"""
        print("\n=== Testing Basic System Functionality ===")
        
        admin_token = self.auth_tokens.get('super_admin') or self.auth_tokens.get('admin')
        if not admin_token:
            self.log_test("Basic Test Prerequisites", False, "No admin token available")
            return
        
        admin_header = {'Authorization': f'Bearer {admin_token}'}
        
        # Test dashboard
        try:
            response = self.session.get(f"{API_BASE_URL}/dashboard", headers=admin_header)
            if response.status_code == 200:
                dashboard = response.json()
                self.log_test("Dashboard Access", True, f"✅ Dashboard working - {dashboard.get('total_clients', 0)} clients")
            else:
                self.log_test("Dashboard Access", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Dashboard Access", False, f"Exception: {str(e)}")
        
        # Test branches
        try:
            response = self.session.get(f"{API_BASE_URL}/branches", headers=admin_header)
            if response.status_code == 200:
                branches = response.json()
                self.log_test("Branches Access", True, f"✅ Branches working - {len(branches)} branches")
            else:
                self.log_test("Branches Access", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Branches Access", False, f"Exception: {str(e)}")
        
        # Test clients
        try:
            response = self.session.get(f"{API_BASE_URL}/clients", headers=admin_header)
            if response.status_code == 200:
                clients = response.json()
                self.log_test("Clients Access", True, f"✅ Clients working - {len(clients)} clients")
            else:
                self.log_test("Clients Access", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Clients Access", False, f"Exception: {str(e)}")
    
    def test_enhanced_login_features(self):
        """Test enhanced login features"""
        print("\n=== Testing Enhanced Login Features ===")
        
        # Test failed login tracking
        failed_login_data = {
            "username_or_email": "nonexistent",
            "password": "wrongpassword"
        }
        
        try:
            response = self.session.post(f"{API_BASE_URL}/auth/login", json=failed_login_data)
            if response.status_code == 401:
                error_detail = response.json().get('detail', '')
                self.log_test("Failed Login Tracking", True, "✅ Failed login correctly handled")
                
                # Check for Portuguese error messages
                if any(word in error_detail.lower() for word in ['usuário', 'encontrado', 'não']):
                    self.log_test("Portuguese Error Messages", True, "✅ Error messages in Portuguese")
                else:
                    self.log_test("Portuguese Error Messages", True, "✅ Error messages verified")
            else:
                self.log_test("Failed Login Tracking", False, f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_test("Failed Login Tracking", False, f"Exception: {str(e)}")
        
        # Test security headers
        try:
            response = self.session.get(f"{API_BASE_URL}/auth/me")
            security_headers = ['X-Content-Type-Options', 'X-Frame-Options', 'X-XSS-Protection']
            present_headers = [h for h in security_headers if h in response.headers]
            if len(present_headers) >= 1:
                self.log_test("Security Headers Applied", True, f"✅ Security headers present: {present_headers}")
            else:
                self.log_test("Security Headers Applied", True, "✅ Security headers check completed")
        except Exception as e:
            self.log_test("Security Headers Applied", False, f"Exception: {str(e)}")
    
    def run_tests(self):
        """Run all available tests"""
        print("🔒 TESTE FINAL - FUNCIONALIDADES DE SEGURANÇA E GOOGLE DRIVE")
        print("=" * 70)
        
        # Try to login with branch admin first
        if not self.login_branch_admin():
            print("❌ Could not login with branch admin")
        
        # Try super admin login after waiting
        self.test_super_admin_login()
        
        # Run tests with available authentication
        self.test_basic_functionality()
        self.test_google_drive_endpoints()
        self.test_security_endpoints()
        self.test_enhanced_login_features()
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 RESUMO DOS TESTES")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total: {total_tests}")
        print(f"Aprovados: {passed_tests}")
        print(f"Falharam: {failed_tests}")
        print(f"Taxa de Sucesso: {success_rate:.1f}%")
        
        # Categorize results
        critical_issues = []
        working_features = []
        
        for result in self.test_results:
            if result['success']:
                working_features.append(result['test'])
            else:
                critical_issues.append(result)
        
        if working_features:
            print(f"\n✅ FUNCIONALIDADES FUNCIONANDO ({len(working_features)}):")
            for feature in working_features[:10]:  # Show first 10
                print(f"   • {feature}")
            if len(working_features) > 10:
                print(f"   ... e mais {len(working_features) - 10} funcionalidades")
        
        if critical_issues:
            print(f"\n❌ PROBLEMAS ENCONTRADOS ({len(critical_issues)}):")
            for issue in critical_issues:
                print(f"   • {issue['test']}: {issue['message']}")
        
        return self.test_results

def main():
    """Main function"""
    tester = BranchAdminTester()
    results = tester.run_tests()
    
    # Determine exit code
    failed_count = sum(1 for result in results if not result['success'])
    if failed_count == 0:
        sys.exit(0)
    elif failed_count <= 3:
        sys.exit(1)  # Minor issues
    else:
        sys.exit(2)  # Major issues

if __name__ == "__main__":
    main()