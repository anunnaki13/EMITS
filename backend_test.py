import requests
import sys
import json
from datetime import datetime

class FuelManagementAPITester:
    def __init__(self, base_url="https://fuelman-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, auth_required=True):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f" (Expected: {expected_status})"
                try:
                    error_data = response.json()
                    details += f" - {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f" - {response.text[:100]}"
            
            self.log_test(name, success, details)
            
            if success:
                try:
                    return response.json()
                except:
                    return {}
            return None

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return None

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        self.run_test("Health Check", "GET", "", 200, auth_required=False)
        self.run_test("API Health", "GET", "health", 200, auth_required=False)

    def test_authentication(self):
        """Test authentication endpoints"""
        print("\n🔍 Testing Authentication...")
        
        # Test registration
        test_user_data = {
            "email": "admin@pltu-tenayan.co.id",
            "password": "admin123",
            "name": "Test Admin",
            "role": "admin"
        }
        
        # Try login first (user might already exist)
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        
        response = self.run_test("Login", "POST", "auth/login", 200, login_data, auth_required=False)
        
        if response and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            print(f"    ✅ Logged in as: {response['user']['name']} ({response['user']['role']})")
        else:
            # If login fails, try registration
            print("    Login failed, trying registration...")
            response = self.run_test("Register", "POST", "auth/register", 200, test_user_data, auth_required=False)
            
            if response and 'access_token' in response:
                self.token = response['access_token']
                self.user_id = response['user']['id']
                print(f"    ✅ Registered as: {response['user']['name']} ({response['user']['role']})")
        
        # Test get current user
        if self.token:
            self.run_test("Get Current User", "GET", "auth/me", 200)

    def test_vessel_operations(self):
        """Test vessel CRUD operations"""
        print("\n🔍 Testing Vessel Operations...")
        
        # Test GET vessels (empty list is OK)
        self.run_test("Get Vessels", "GET", "vessels", 200)
        
        # Test CREATE vessel
        vessel_data = {
            "periode_ta": "Jan-25",
            "periode_realisasi": "Jan-25",
            "shipment_code": "TEST-VESSEL-001",
            "voyage_code": "V001",
            "suppliers": "Test Supplier",
            "voyage": "Test Voyage",
            "name_of_vessel": "MV Test Ship",
            "coal_from": "Test Origin",
            "bl_mt": 5000.0,
            "ds_mt": 4950.0,
            "gcv_arb": 4200.0
        }
        
        vessel_response = self.run_test("Create Vessel", "POST", "vessels", 200, vessel_data)
        vessel_id = None
        
        if vessel_response and 'id' in vessel_response:
            vessel_id = vessel_response['id']
            
            # Test GET specific vessel
            self.run_test("Get Vessel by ID", "GET", f"vessels/{vessel_id}", 200)
            
            # Test UPDATE vessel
            updated_data = vessel_data.copy()
            updated_data['suppliers'] = "Updated Supplier"
            self.run_test("Update Vessel", "PUT", f"vessels/{vessel_id}", 200, updated_data)
            
            # Test DELETE vessel (only if admin)
            self.run_test("Delete Vessel", "DELETE", f"vessels/{vessel_id}", 200)

    def test_barge_operations(self):
        """Test barge CRUD operations"""
        print("\n🔍 Testing Barge Operations...")
        
        self.run_test("Get Barges", "GET", "barges", 200)
        
        barge_data = {
            "periode_ta": "Jan-25",
            "periode_realisasi": "Jan-25",
            "shipment_code": "TEST-BARGE-001",
            "voyage_code": "B001",
            "suppliers": "Test Supplier",
            "voyage": "Test Voyage",
            "name_of_barge": "TB Test Barge",
            "coal_from": "Test Origin",
            "bl_mt": 3000.0,
            "ds_mt": 2950.0,
            "gcv_arb": 4100.0
        }
        
        barge_response = self.run_test("Create Barge", "POST", "barges", 200, barge_data)
        
        if barge_response and 'id' in barge_response:
            barge_id = barge_response['id']
            self.run_test("Get Barge by ID", "GET", f"barges/{barge_id}", 200)
            self.run_test("Delete Barge", "DELETE", f"barges/{barge_id}", 200)

    def test_trucking_operations(self):
        """Test trucking CRUD operations"""
        print("\n🔍 Testing Trucking Operations...")
        
        self.run_test("Get Trucking", "GET", "trucking", 200)
        
        trucking_data = {
            "periode": "Jan-25",
            "shipment_code": "TEST-TRUCK-001",
            "suppliers": "Test Carrier",
            "no_truck": "B1234XYZ",
            "origin": "Test Origin",
            "destination": "PLTU Tenayan",
            "weight_mt": 30.0,
            "gcv_arb": 4000.0
        }
        
        trucking_response = self.run_test("Create Trucking", "POST", "trucking", 200, trucking_data)
        
        if trucking_response and 'id' in trucking_response:
            trucking_id = trucking_response['id']
            self.run_test("Get Trucking by ID", "GET", f"trucking/{trucking_id}", 200)
            self.run_test("Delete Trucking", "DELETE", f"trucking/{trucking_id}", 200)

    def test_biomassa_operations(self):
        """Test biomassa CRUD operations"""
        print("\n🔍 Testing Biomassa Operations...")
        
        self.run_test("Get Biomassa", "GET", "biomassa", 200)
        
        biomassa_data = {
            "periode": "Jan-25",
            "shipment_code": "TEST-BIO-001",
            "lot": "LOT001",
            "suppliers": "Test Bio Supplier",
            "shipper": "Test Shipper",
            "biomass_type": "WOODCHIP",
            "jembatan_timbang_mt": 100.0,
            "gcv_arb": 3500.0
        }
        
        biomassa_response = self.run_test("Create Biomassa", "POST", "biomassa", 200, biomassa_data)
        
        if biomassa_response and 'id' in biomassa_response:
            biomassa_id = biomassa_response['id']
            self.run_test("Get Biomassa by ID", "GET", f"biomassa/{biomassa_id}", 200)
            self.run_test("Delete Biomassa", "DELETE", f"biomassa/{biomassa_id}", 200)

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        print("\n🔍 Testing Dashboard Stats...")
        self.run_test("Get Dashboard Stats", "GET", "dashboard/stats", 200)

    def test_user_management(self):
        """Test user management (admin only)"""
        print("\n🔍 Testing User Management...")
        self.run_test("Get Users List", "GET", "users", 200)

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting PLTU Tenayan Fuel Management API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run tests in order
        self.test_health_check()
        self.test_authentication()
        
        if not self.token:
            print("\n❌ Authentication failed - cannot continue with protected endpoints")
            return False
        
        self.test_vessel_operations()
        self.test_barge_operations()
        self.test_trucking_operations()
        self.test_biomassa_operations()
        self.test_dashboard_stats()
        self.test_user_management()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate < 80:
            print("⚠️  Warning: Success rate below 80%")
        
        return success_rate >= 80

def main():
    tester = FuelManagementAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/test_reports/backend_api_results.json', 'w') as f:
        json.dump({
            'summary': {
                'total_tests': tester.tests_run,
                'passed_tests': tester.tests_passed,
                'success_rate': (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
                'timestamp': datetime.now().isoformat()
            },
            'detailed_results': tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())