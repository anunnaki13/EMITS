"""
COA Reconciliation API Tests
Tests for COA Reconciliation & Dispute Monitor feature
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://coal-quality-check.preview.emergentagent.com')


class TestCOAReconciliationAuth:
    """Authentication tests for COA Reconciliation endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": "adminpassword"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": "adminpassword"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "admin@example.com"
        assert data["user"]["role"] == "admin"


class TestCOAReconciliationList:
    """Tests for GET /api/coa-reconciliation endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": "adminpassword"
        })
        return response.json()["access_token"]
    
    def test_get_coa_reconciliation_paginated(self, auth_token):
        """Test GET /api/coa-reconciliation returns paginated data"""
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"page": 1, "page_size": 10}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify pagination structure
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        
        # Verify data exists (283 records as per context)
        assert data["total"] > 0
        assert len(data["items"]) <= 10
        
    def test_get_coa_reconciliation_item_structure(self, auth_token):
        """Test that each item has required fields"""
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"page": 1, "page_size": 1}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data["items"]:
            item = data["items"][0]
            # Required fields for Triple Check Table
            assert "id" in item
            assert "shipment" in item
            assert "suppliers" in item
            assert "loading_gcv_arb" in item
            assert "unloading_gcv_arb" in item
            assert "internal_gcv_arb" in item
            assert "delta_loading_internal" in item
            assert "status" in item
            assert "umpire_status" in item
    
    def test_get_coa_reconciliation_status_filter_critical(self, auth_token):
        """Test status filter for critical records"""
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"page": 1, "page_size": 50, "status": "critical"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All items should have critical status
        for item in data["items"]:
            assert item["status"] == "critical"
    
    def test_get_coa_reconciliation_status_filter_warning(self, auth_token):
        """Test status filter for warning records"""
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"page": 1, "page_size": 50, "status": "warning"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All items should have warning status
        for item in data["items"]:
            assert item["status"] == "warning"
    
    def test_get_coa_reconciliation_status_filter_normal(self, auth_token):
        """Test status filter for normal records"""
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"page": 1, "page_size": 50, "status": "normal"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All items should have normal status
        for item in data["items"]:
            assert item["status"] == "normal"
    
    def test_get_coa_reconciliation_search_filter(self, auth_token):
        """Test search filter for supplier name"""
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"page": 1, "page_size": 50, "search": "PT BA"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All items should contain search term in suppliers
        for item in data["items"]:
            assert "PT BA" in item["suppliers"] or str(item["shipment"]).find("PT BA") >= 0


class TestCOAReconciliationKPIs:
    """Tests for GET /api/coa-reconciliation/kpis endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": "adminpassword"
        })
        return response.json()["access_token"]
    
    def test_get_kpis_returns_all_metrics(self, auth_token):
        """Test GET /api/coa-reconciliation/kpis returns all KPI metrics"""
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation/kpis",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify all KPI fields
        assert "total_records" in data
        assert "high_deviation_count" in data
        assert "potential_loss_rp" in data
        assert "total_tonnage_problem" in data
        assert "umpire_status" in data
        assert "supplier_deviations" in data
        assert "worst_supplier" in data
        assert "avg_accuracy" in data
        assert "critical_count" in data
        assert "warning_count" in data
        assert "normal_count" in data
    
    def test_get_kpis_umpire_status_structure(self, auth_token):
        """Test umpire status has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation/kpis",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        umpire_status = data["umpire_status"]
        assert "proposed" in umpire_status
        assert "in_progress" in umpire_status
        assert "completed" in umpire_status
        assert "total" in umpire_status
    
    def test_get_kpis_worst_supplier_structure(self, auth_token):
        """Test worst supplier has correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation/kpis",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        if data["worst_supplier"]:
            worst = data["worst_supplier"]
            assert "supplier" in worst
            assert "count" in worst
            assert "avg_deviation" in worst
            assert "total_deviation" in worst


class TestCOAReconciliationTrend:
    """Tests for GET /api/coa-reconciliation/trend endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": "adminpassword"
        })
        return response.json()["access_token"]
    
    def test_get_trend_data(self, auth_token):
        """Test GET /api/coa-reconciliation/trend returns trend data"""
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation/trend",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"months": 6}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return list of trend data
        assert isinstance(data, list)
        
        if data:
            item = data[0]
            assert "periode" in item
            assert "loading" in item
            assert "unloading" in item
            assert "internal" in item


class TestCOAReconciliationSupplierConsistency:
    """Tests for GET /api/coa-reconciliation/supplier-consistency endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": "adminpassword"
        })
        return response.json()["access_token"]
    
    def test_get_supplier_consistency(self, auth_token):
        """Test GET /api/coa-reconciliation/supplier-consistency returns supplier data"""
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation/supplier-consistency",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should return list of supplier deviations
        assert isinstance(data, list)
        
        if data:
            item = data[0]
            assert "supplier" in item
            assert "count" in item
            assert "avg_deviation" in item
            assert "total_deviation" in item


class TestCOAReconciliationDetail:
    """Tests for GET /api/coa-reconciliation/{record_id} endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": "adminpassword"
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def sample_record_id(self, auth_token):
        """Get a sample record ID for testing"""
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"page": 1, "page_size": 1}
        )
        if response.status_code == 200 and response.json()["items"]:
            return response.json()["items"][0]["id"]
        return None
    
    def test_get_detail_with_radar_chart(self, auth_token, sample_record_id):
        """Test GET /api/coa-reconciliation/{record_id} returns record with radar chart"""
        if not sample_record_id:
            pytest.skip("No sample record available")
        
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation/{sample_record_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "record" in data
        assert "radar_chart" in data
        
        # Verify radar chart structure
        radar = data["radar_chart"]
        assert isinstance(radar, list)
        assert len(radar) == 4  # GCV, TM, Ash, Sulphur
        
        for item in radar:
            assert "parameter" in item
            assert "loading" in item
            assert "unloading" in item
            assert "internal" in item
            assert "fullMark" in item
    
    def test_get_detail_not_found(self, auth_token):
        """Test GET /api/coa-reconciliation/{record_id} returns 404 for invalid ID"""
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation/invalid-id-12345",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404


class TestCOAReconciliationUmpire:
    """Tests for umpire proposal endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": "adminpassword"
        })
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def critical_record_id(self, auth_token):
        """Get a critical record ID for testing umpire proposal"""
        response = requests.get(
            f"{BASE_URL}/api/coa-reconciliation",
            headers={"Authorization": f"Bearer {auth_token}"},
            params={"page": 1, "page_size": 10, "status": "critical"}
        )
        if response.status_code == 200 and response.json()["items"]:
            # Find a record without umpire proposal
            for item in response.json()["items"]:
                if item.get("umpire_status") == "none":
                    return item["id"]
            # If all have proposals, return first one
            return response.json()["items"][0]["id"]
        return None
    
    def test_propose_umpire_success(self, auth_token, critical_record_id):
        """Test POST /api/coa-reconciliation/propose-umpire saves umpire proposal"""
        if not critical_record_id:
            pytest.skip("No critical record available")
        
        response = requests.post(
            f"{BASE_URL}/api/coa-reconciliation/propose-umpire",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "reconciliation_id": critical_record_id,
                "sample_number": "TEST-UMPIRE-001",
                "notes": "Test umpire proposal from pytest"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "sample_number" in data
        assert data["sample_number"] == "TEST-UMPIRE-001"
    
    def test_propose_umpire_invalid_id(self, auth_token):
        """Test POST /api/coa-reconciliation/propose-umpire returns 404 for invalid ID"""
        response = requests.post(
            f"{BASE_URL}/api/coa-reconciliation/propose-umpire",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "reconciliation_id": "invalid-id-12345",
                "sample_number": "TEST-UMPIRE-002",
                "notes": "Should fail"
            }
        )
        assert response.status_code == 404


class TestCOAReconciliationUnauthorized:
    """Tests for unauthorized access"""
    
    def test_get_coa_reconciliation_unauthorized(self):
        """Test GET /api/coa-reconciliation without auth returns 403"""
        response = requests.get(f"{BASE_URL}/api/coa-reconciliation")
        assert response.status_code == 403
    
    def test_get_kpis_unauthorized(self):
        """Test GET /api/coa-reconciliation/kpis without auth returns 403"""
        response = requests.get(f"{BASE_URL}/api/coa-reconciliation/kpis")
        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
