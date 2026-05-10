"""
Test suite for PO Batubara API endpoints
Tests: GET /api/po-batubara/years, GET /api/po-batubara, POST/PUT/DELETE operations
"""
import pytest
import requests
import os
from tests.conftest import _require_env

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

ADMIN_EMAIL = os.environ.get("TEST_ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = _require_env("TEST_ADMIN_PASSWORD")

class TestPOBatubaraAPI:
    """PO Batubara API endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_login_with_admin_credentials(self):
        """Test login with admin credentials (TEST_ADMIN_EMAIL / TEST_ADMIN_PASSWORD)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "admin@example.com"
        assert data["user"]["role"] == "admin"
        print("✓ Login with admin credentials - SUCCESS")
    
    def test_get_po_batubara_years(self):
        """Test GET /api/po-batubara/years - returns yearly summary data"""
        response = requests.get(f"{BASE_URL}/api/po-batubara/years", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response is a list
        assert isinstance(data, list)
        
        # Verify structure of year data
        if len(data) > 0:
            year_data = data[0]
            assert "year" in year_data
            assert "months" in year_data
            assert "total_count" in year_data
            assert "total_tonase" in year_data
            assert "total_value" in year_data
            
            # Verify months structure
            if year_data["months"]:
                month_key = list(year_data["months"].keys())[0]
                month_data = year_data["months"][month_key]
                assert "month" in month_data
                assert "count" in month_data
                assert "total_tonase" in month_data
                assert "total_value" in month_data
        
        print(f"✓ GET /api/po-batubara/years - SUCCESS ({len(data)} years found)")
    
    def test_get_po_batubara_by_year_month(self):
        """Test GET /api/po-batubara?year=2025&month=1 - returns PO data (ADR-008 envelope)"""
        response = requests.get(f"{BASE_URL}/api/po-batubara",
                                headers=self.headers,
                                params={"year": 2025, "month": 1})
        assert response.status_code == 200
        data = response.json()

        # Phase-2 introduced pagination envelope: {items, total, page, page_size, total_pages}
        assert isinstance(data, dict) and "items" in data, (
            f"Expected pagination envelope dict with 'items', got: {type(data)}"
        )
        assert isinstance(data["items"], list)

        # Verify structure of PO data (if any items present)
        if len(data["items"]) > 0:
            po = data["items"][0]
            assert "id" in po
            assert "po_number" in po
            assert "supplier_name" in po
            assert "tonase_po" in po
            assert "total" in po
            assert "completed_year" in po
            assert "completed_month" in po

            # Verify year/month filter works
            assert po["completed_year"] == 2025
            assert po["completed_month"] == 1

        print(f"✓ GET /api/po-batubara?year=2025&month=1 - SUCCESS ({data['total']} total records)")
    
    def test_get_po_batubara_all(self):
        """Test GET /api/po-batubara - returns all PO data (ADR-008 envelope)"""
        response = requests.get(f"{BASE_URL}/api/po-batubara", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        # Phase-2 introduced pagination envelope: {items, total, page, page_size, total_pages}
        assert isinstance(data, dict) and "items" in data, (
            f"Expected pagination envelope dict with 'items', got: {type(data)}"
        )
        assert isinstance(data["items"], list)
        print(f"✓ GET /api/po-batubara (all) - SUCCESS ({data['total']} total records)")
    
    def test_create_po_batubara(self):
        """Test POST /api/po-batubara - create new PO"""
        new_po = {
            "district_code": "TEST",
            "district_name": "Test District",
            "periode": "2025-01-01",
            "po_number": "TEST-PO-001",
            "supplier_code": "TEST-SUP",
            "supplier_name": "Test Supplier",
            "spec": "LRC",
            "vessel_tugboat": "Test Vessel",
            "barge": "Test Barge",
            "no_jadwal": "TEST-SCH-001",
            "no_shipment": "TEST-SHIP-001",
            "time_arrival": "2025-01-15 10:00:00",
            "completed": "2025-01-20 14:00:00",
            "completed_year": 2025,
            "completed_month": 1,
            "tonase_po": 5000.0,
            "total": 5000000000.0
        }
        
        response = requests.post(f"{BASE_URL}/api/po-batubara", 
                                headers=self.headers, 
                                json=new_po)
        assert response.status_code == 200
        data = response.json()
        
        # Verify created data
        assert "id" in data
        assert data["po_number"] == "TEST-PO-001"
        assert data["supplier_name"] == "Test Supplier"
        assert data["tonase_po"] == 5000.0
        
        # Store ID for cleanup
        self.created_po_id = data["id"]
        print(f"✓ POST /api/po-batubara - SUCCESS (created ID: {data['id'][:8]}...)")
        
        # Cleanup - delete the test PO
        delete_response = requests.delete(f"{BASE_URL}/api/po-batubara/{data['id']}", 
                                         headers=self.headers)
        assert delete_response.status_code == 200
        print("✓ Cleanup: Test PO deleted")
    
    def test_get_po_batubara_by_id(self):
        """Test GET /api/po-batubara/{id} - get specific PO (ADR-008 envelope)"""
        # First get list to find an ID
        list_response = requests.get(f"{BASE_URL}/api/po-batubara",
                                     headers=self.headers,
                                     params={"page": 1, "page_size": 1})
        assert list_response.status_code == 200
        data = list_response.json()
        # Phase-2 introduced pagination envelope: unwrap items list
        assert isinstance(data, dict) and "items" in data, (
            f"Expected pagination envelope dict with 'items', got: {type(data)}"
        )

        if len(data["items"]) > 0:
            po_id = data["items"][0]["id"]
            response = requests.get(f"{BASE_URL}/api/po-batubara/{po_id}",
                                    headers=self.headers)
            assert response.status_code == 200
            po = response.json()
            assert po["id"] == po_id
            print(f"✓ GET /api/po-batubara/{{id}} - SUCCESS")
        else:
            pytest.skip("No PO data available for testing")
    
    def test_update_po_batubara(self):
        """Test PUT /api/po-batubara/{id} - update PO"""
        # Create a test PO first
        new_po = {
            "district_code": "TEST",
            "po_number": "TEST-UPDATE-001",
            "supplier_name": "Original Supplier",
            "tonase_po": 1000.0,
            "completed_year": 2025,
            "completed_month": 1
        }
        
        create_response = requests.post(f"{BASE_URL}/api/po-batubara", 
                                       headers=self.headers, 
                                       json=new_po)
        assert create_response.status_code == 200
        po_id = create_response.json()["id"]
        
        # Update the PO
        updated_po = {
            "district_code": "TEST",
            "po_number": "TEST-UPDATE-001",
            "supplier_name": "Updated Supplier",
            "tonase_po": 2000.0,
            "completed_year": 2025,
            "completed_month": 1
        }
        
        update_response = requests.put(f"{BASE_URL}/api/po-batubara/{po_id}", 
                                      headers=self.headers, 
                                      json=updated_po)
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["supplier_name"] == "Updated Supplier"
        assert data["tonase_po"] == 2000.0
        print("✓ PUT /api/po-batubara/{id} - SUCCESS")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/po-batubara/{po_id}", headers=self.headers)
    
    def test_delete_po_batubara(self):
        """Test DELETE /api/po-batubara/{id} - delete PO"""
        # Create a test PO first
        new_po = {
            "district_code": "TEST",
            "po_number": "TEST-DELETE-001",
            "supplier_name": "To Be Deleted",
            "completed_year": 2025,
            "completed_month": 1
        }
        
        create_response = requests.post(f"{BASE_URL}/api/po-batubara", 
                                       headers=self.headers, 
                                       json=new_po)
        assert create_response.status_code == 200
        po_id = create_response.json()["id"]
        
        # Delete the PO
        delete_response = requests.delete(f"{BASE_URL}/api/po-batubara/{po_id}", 
                                         headers=self.headers)
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/po-batubara/{po_id}", 
                                   headers=self.headers)
        assert get_response.status_code == 404
        print("✓ DELETE /api/po-batubara/{id} - SUCCESS")
    
    def test_yearly_totals_calculation(self):
        """Test that yearly totals are calculated correctly"""
        response = requests.get(f"{BASE_URL}/api/po-batubara/years", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        for year_data in data:
            # Calculate sum of monthly counts
            monthly_count_sum = sum(m["count"] for m in year_data["months"].values())
            assert year_data["total_count"] == monthly_count_sum, \
                f"Year {year_data['year']}: total_count mismatch"
            
            # Calculate sum of monthly tonase
            monthly_tonase_sum = sum(m["total_tonase"] for m in year_data["months"].values())
            assert abs(year_data["total_tonase"] - monthly_tonase_sum) < 0.01, \
                f"Year {year_data['year']}: total_tonase mismatch"
        
        print("✓ Yearly totals calculation - VERIFIED")
    
    def test_monthly_totals_calculation(self):
        """Test that monthly totals match actual data"""
        # Get years data
        years_response = requests.get(f"{BASE_URL}/api/po-batubara/years", headers=self.headers)
        assert years_response.status_code == 200
        years_data = years_response.json()
        
        if len(years_data) > 0:
            # Test first year, first month
            year = years_data[0]["year"]
            month_key = list(years_data[0]["months"].keys())[0]
            month = int(month_key)
            expected_count = years_data[0]["months"][month_key]["count"]
            expected_tonase = years_data[0]["months"][month_key]["total_tonase"]
            
            # Get actual data for that month
            month_response = requests.get(f"{BASE_URL}/api/po-batubara", 
                                         headers=self.headers,
                                         params={"year": year, "month": month})
            assert month_response.status_code == 200
            month_data = month_response.json()
            
            # Verify count matches
            assert len(month_data) == expected_count, \
                f"Month {month}/{year}: count mismatch (expected {expected_count}, got {len(month_data)})"
            
            # Verify tonase sum matches
            actual_tonase = sum(po.get("tonase_po", 0) or 0 for po in month_data)
            assert abs(actual_tonase - expected_tonase) < 0.01, \
                f"Month {month}/{year}: tonase mismatch"
            
            print(f"✓ Monthly totals for {month}/{year} - VERIFIED")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
