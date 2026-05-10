"""
Test suite for Merit Order API endpoints
Tests CRUD operations for Merit Order feature in PLTU Tenayan Fuel Management System
"""
import pytest
import requests
import os
from tests.conftest import _require_env

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = _require_env("TEST_ADMIN_PASSWORD")

class TestMeritOrderAPI:
    """Merit Order API endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.created_ids = []
        
        yield
        
        # Cleanup - delete test data
        for item_id in self.created_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/merit-order/{item_id}")
            except:
                pass
    
    def test_01_login_success(self):
        """Test login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": ADMIN_PASSWORD
        }, headers={"Content-Type": "application/json"})
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "admin@example.com"
        assert data["user"]["role"] == "admin"
        print("✓ Login successful with admin credentials")
    
    def test_02_get_merit_orders_list(self):
        """Test GET /api/merit-order - list all merit orders"""
        response = self.session.get(f"{BASE_URL}/api/merit-order")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 58, f"Expected 58 records, got {len(data)}"
        print(f"✓ GET /api/merit-order returns {len(data)} records")
    
    def test_03_merit_order_data_structure(self):
        """Test merit order data has correct structure"""
        response = self.session.get(f"{BASE_URL}/api/merit-order")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        
        # Check first record has required fields
        first_record = data[0]
        required_fields = ["id", "periode", "pemasok", "moda", "tipikal_kcal_kg", 
                          "jenis_kontrak", "harga_batubara", "harga_cif", "rp_kcal"]
        
        for field in required_fields:
            assert field in first_record, f"Missing field: {field}"
        
        print(f"✓ Merit order data structure is correct with all required fields")
    
    def test_04_merit_order_moda_values(self):
        """Test moda field has valid values (Vessel variants, Tongkang, Trucking)"""
        response = self.session.get(f"{BASE_URL}/api/merit-order")
        
        assert response.status_code == 200
        data = response.json()
        
        # Valid moda values include Vessel variants from Excel data
        valid_moda = {"Vessel", "Tongkang", "Trucking", "Vessel Hand Size", "Vessel Supramax"}
        moda_found = set()
        
        for record in data:
            if record.get("moda"):
                moda_found.add(record["moda"])
        
        # Check that all moda values are valid
        for moda in moda_found:
            assert moda in valid_moda, f"Invalid moda value: {moda}"
        
        print(f"✓ Moda values are valid: {moda_found}")
    
    def test_05_merit_order_kontrak_values(self):
        """Test jenis_kontrak field has valid values (CIF, CFR, FOB)"""
        response = self.session.get(f"{BASE_URL}/api/merit-order")
        
        assert response.status_code == 200
        data = response.json()
        
        valid_kontrak = {"CIF", "CFR", "FOB"}
        kontrak_found = set()
        
        for record in data:
            if record.get("jenis_kontrak"):
                kontrak_found.add(record["jenis_kontrak"])
        
        # Check that all kontrak values are valid
        for kontrak in kontrak_found:
            assert kontrak in valid_kontrak, f"Invalid kontrak value: {kontrak}"
        
        print(f"✓ Jenis kontrak values are valid: {kontrak_found}")
    
    def test_06_create_merit_order(self):
        """Test POST /api/merit-order - create new merit order"""
        new_data = {
            "periode": "2026-01-15",
            "periode_year": 2026,
            "periode_month": 1,
            "pemasok": "TEST_PEMASOK_001",
            "moda": "Vessel",
            "tipikal_kcal_kg": 4200,
            "jenis_kontrak": "CIF",
            "harga_batubara": 850000,
            "harga_freight": 150000,
            "harga_cif": 1000000,
            "rp_kg": 1000,
            "rp_kcal": 0.238095
        }
        
        response = self.session.post(f"{BASE_URL}/api/merit-order", json=new_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["pemasok"] == "TEST_PEMASOK_001"
        assert data["moda"] == "Vessel"
        assert data["jenis_kontrak"] == "CIF"
        assert data["tipikal_kcal_kg"] == 4200
        
        self.created_ids.append(data["id"])
        print(f"✓ POST /api/merit-order created record with id: {data['id']}")
        
        # Verify by GET
        get_response = self.session.get(f"{BASE_URL}/api/merit-order/{data['id']}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["pemasok"] == "TEST_PEMASOK_001"
        print("✓ Created record verified via GET")
    
    def test_07_get_merit_order_by_id(self):
        """Test GET /api/merit-order/{id} - get single merit order"""
        # First create a record
        new_data = {
            "periode": "2026-01-20",
            "pemasok": "TEST_PEMASOK_GET",
            "moda": "Tongkang",
            "tipikal_kcal_kg": 3800,
            "jenis_kontrak": "FOB",
            "harga_batubara": 750000,
            "harga_cif": 900000,
            "rp_kcal": 0.236842
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/merit-order", json=new_data)
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]
        self.created_ids.append(created_id)
        
        # Get by ID
        response = self.session.get(f"{BASE_URL}/api/merit-order/{created_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_id
        assert data["pemasok"] == "TEST_PEMASOK_GET"
        assert data["moda"] == "Tongkang"
        print(f"✓ GET /api/merit-order/{created_id} returns correct data")
    
    def test_08_update_merit_order(self):
        """Test PUT /api/merit-order/{id} - update merit order"""
        # First create a record
        new_data = {
            "periode": "2026-01-25",
            "pemasok": "TEST_PEMASOK_UPDATE",
            "moda": "Trucking",
            "tipikal_kcal_kg": 4000,
            "jenis_kontrak": "CFR",
            "harga_batubara": 800000,
            "harga_cif": 950000,
            "rp_kcal": 0.2375
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/merit-order", json=new_data)
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]
        self.created_ids.append(created_id)
        
        # Update the record
        update_data = {
            "periode": "2026-01-25",
            "pemasok": "TEST_PEMASOK_UPDATED",
            "moda": "Vessel",
            "tipikal_kcal_kg": 4500,
            "jenis_kontrak": "CIF",
            "harga_batubara": 900000,
            "harga_cif": 1100000,
            "rp_kcal": 0.244444
        }
        
        response = self.session.put(f"{BASE_URL}/api/merit-order/{created_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["pemasok"] == "TEST_PEMASOK_UPDATED"
        assert data["moda"] == "Vessel"
        assert data["tipikal_kcal_kg"] == 4500
        print(f"✓ PUT /api/merit-order/{created_id} updated successfully")
        
        # Verify update persisted
        get_response = self.session.get(f"{BASE_URL}/api/merit-order/{created_id}")
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched["pemasok"] == "TEST_PEMASOK_UPDATED"
        print("✓ Update verified via GET")
    
    def test_09_delete_merit_order(self):
        """Test DELETE /api/merit-order/{id} - delete merit order"""
        # First create a record
        new_data = {
            "periode": "2026-01-30",
            "pemasok": "TEST_PEMASOK_DELETE",
            "moda": "Tongkang",
            "tipikal_kcal_kg": 3900,
            "jenis_kontrak": "FOB",
            "harga_batubara": 780000,
            "harga_cif": 920000,
            "rp_kcal": 0.235897
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/merit-order", json=new_data)
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]
        
        # Delete the record
        response = self.session.delete(f"{BASE_URL}/api/merit-order/{created_id}")
        
        assert response.status_code == 200
        print(f"✓ DELETE /api/merit-order/{created_id} successful")
        
        # Verify deletion
        get_response = self.session.get(f"{BASE_URL}/api/merit-order/{created_id}")
        assert get_response.status_code == 404
        print("✓ Deletion verified - record not found (404)")
    
    def test_10_get_merit_order_not_found(self):
        """Test GET /api/merit-order/{id} with invalid ID returns 404"""
        response = self.session.get(f"{BASE_URL}/api/merit-order/invalid-id-12345")
        
        assert response.status_code == 404
        print("✓ GET with invalid ID returns 404")
    
    def test_11_merit_order_periods_endpoint(self):
        """Test GET /api/merit-order/periods - get available periods"""
        response = self.session.get(f"{BASE_URL}/api/merit-order/periods")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/merit-order/periods returns {len(data)} year(s) of data")
        
        # Check structure if data exists
        if len(data) > 0:
            first_year = data[0]
            assert "year" in first_year
            assert "months" in first_year
            assert "total_count" in first_year
            print(f"✓ Periods data structure is correct")
    
    def test_12_filter_by_search(self):
        """Test GET /api/merit-order with search parameter"""
        # First create a record with unique name
        new_data = {
            "periode": "2026-02-01",
            "pemasok": "UNIQUE_SEARCH_TEST_XYZ",
            "moda": "Vessel",
            "tipikal_kcal_kg": 4100,
            "jenis_kontrak": "CIF",
            "harga_batubara": 820000,
            "harga_cif": 980000,
            "rp_kcal": 0.239024
        }
        
        create_response = self.session.post(f"{BASE_URL}/api/merit-order", json=new_data)
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]
        self.created_ids.append(created_id)
        
        # Search for the record
        response = self.session.get(f"{BASE_URL}/api/merit-order?search=UNIQUE_SEARCH_TEST_XYZ")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(r["pemasok"] == "UNIQUE_SEARCH_TEST_XYZ" for r in data)
        print("✓ Search filter works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
