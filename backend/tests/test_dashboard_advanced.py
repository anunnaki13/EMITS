"""
Test Dashboard Advanced API for PLTU Tenayan Fuel Management System
Tests: /api/dashboard/advanced endpoint with all visualizations
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDashboardAdvanced:
    """Dashboard Advanced API tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": "adminpassword"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_login_success(self):
        """Test login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@example.com",
            "password": "adminpassword"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "admin@example.com"
        print("✓ Login successful")
    
    def test_dashboard_advanced_endpoint(self):
        """Test GET /api/dashboard/advanced returns all required data"""
        response = requests.get(f"{BASE_URL}/api/dashboard/advanced", headers=self.headers)
        assert response.status_code == 200, f"API failed: {response.text}"
        data = response.json()
        
        # Check all required fields exist
        required_fields = [
            "total_ds_mt", "total_tonase_po", "contract_percentage",
            "fuel_composition", "gcv_trend", "supplier_economy",
            "slagging_matrix", "six_months_summary", "available_periods", "available_moda"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Dashboard advanced API returns all required fields")
    
    def test_contract_monitoring_gauge(self):
        """Test contract monitoring data (Gauge Chart)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/advanced", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check gauge data
        assert "total_ds_mt" in data
        assert "total_tonase_po" in data
        assert "contract_percentage" in data
        
        # Validate values
        assert isinstance(data["total_ds_mt"], (int, float))
        assert isinstance(data["total_tonase_po"], (int, float))
        assert 0 <= data["contract_percentage"] <= 100
        
        print(f"✓ Contract Monitoring - DS MT: {data['total_ds_mt']:.0f}, PO: {data['total_tonase_po']:.0f}, %: {data['contract_percentage']:.1f}%")
    
    def test_six_months_summary(self):
        """Test 6 months summary data (Bar Chart)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/advanced", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        six_months = data.get("six_months_summary", [])
        assert len(six_months) == 6, f"Expected 6 months, got {len(six_months)}"
        
        # Check each month has required fields
        for month_data in six_months:
            assert "month" in month_data
            assert "vessel" in month_data
            assert "barge" in month_data
            assert "trucking" in month_data
            assert "biomassa" in month_data
            assert "total_tonase" in month_data
        
        # Print summary
        for m in six_months:
            print(f"  {m['month']}: V={m['vessel']}, B={m['barge']}, T={m['trucking']}, Bio={m['biomassa']}")
        print("✓ Six months summary data valid")
    
    def test_fuel_composition_donut(self):
        """Test fuel composition data (Donut Chart)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/advanced", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        fuel_comp = data.get("fuel_composition", [])
        assert len(fuel_comp) > 0, "No fuel composition data"
        
        # Check structure
        for item in fuel_comp[:5]:
            assert "name" in item
            assert "value" in item
            assert "type" in item
            assert item["type"] in ["coal", "biomass"]
        
        print(f"✓ Fuel composition has {len(fuel_comp)} items")
    
    def test_gcv_trend_line_chart(self):
        """Test GCV trend data (Line Chart with target 4000)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/advanced", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        gcv_trend = data.get("gcv_trend", [])
        
        # Check structure if data exists
        if len(gcv_trend) > 0:
            for item in gcv_trend[:5]:
                assert "date" in item
                assert "gcv_avg" in item
                assert "target" in item
                assert item["target"] == 4000, "Target should be 4000 Kcal/Kg"
            
            # Check GCV values are reasonable (2000-6000 range)
            for item in gcv_trend:
                assert 2000 <= item["gcv_avg"] <= 6000, f"GCV value out of range: {item['gcv_avg']}"
        
        print(f"✓ GCV trend has {len(gcv_trend)} data points with target 4000")
    
    def test_supplier_economy_bar_chart(self):
        """Test supplier economy data (Horizontal Bar Chart)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/advanced", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        supplier_economy = data.get("supplier_economy", [])
        
        # Check structure if data exists
        if len(supplier_economy) > 0:
            for item in supplier_economy[:5]:
                assert "supplier" in item
                assert "rp_kcal" in item
                assert "full_name" in item
            
            # Check sorted by rp_kcal (lowest first = most efficient)
            rp_kcal_values = [s["rp_kcal"] for s in supplier_economy]
            assert rp_kcal_values == sorted(rp_kcal_values), "Should be sorted by RP/Kcal ascending"
        
        print(f"✓ Supplier economy has {len(supplier_economy)} suppliers (sorted by RP/Kcal)")
    
    def test_slagging_matrix_heatmap(self):
        """Test slagging risk matrix data (Heatmap/Table)"""
        response = requests.get(f"{BASE_URL}/api/dashboard/advanced", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        slagging_matrix = data.get("slagging_matrix", [])
        
        # Check structure if data exists
        if len(slagging_matrix) > 0:
            valid_risks = ["SEVERE", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
            for item in slagging_matrix[:5]:
                assert "name" in item
                assert "supplier" in item
                assert "slagging_risk" in item
                assert "fouling_risk" in item
                assert "date" in item
                assert item["slagging_risk"] in valid_risks
                assert item["fouling_risk"] in valid_risks
        
        # Count risk levels
        risk_counts = {}
        for item in slagging_matrix:
            risk = item["slagging_risk"]
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        print(f"✓ Slagging matrix has {len(slagging_matrix)} entries")
        print(f"  Risk distribution: {risk_counts}")
    
    def test_filter_moda_options(self):
        """Test available moda filter options"""
        response = requests.get(f"{BASE_URL}/api/dashboard/advanced", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        
        available_moda = data.get("available_moda", [])
        assert len(available_moda) > 0, "No moda options available"
        
        # Check expected moda types
        expected_moda = ["Vessel", "Barge", "Trucking", "Tongkang"]
        for moda in expected_moda:
            assert moda in available_moda, f"Missing moda: {moda}"
        
        print(f"✓ Available moda options: {available_moda}")
    
    def test_dashboard_stats_endpoint(self):
        """Test GET /api/dashboard/stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=self.headers)
        assert response.status_code == 200, f"API failed: {response.text}"
        data = response.json()
        
        # Check required fields
        required_fields = [
            "total_vessel", "total_barge", "total_trucking", "total_biomassa",
            "total_tonase_batubara", "total_tonase_biomassa", "avg_gcv"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Dashboard stats - Vessel: {data['total_vessel']}, Barge: {data['total_barge']}, Trucking: {data['total_trucking']}, Biomassa: {data['total_biomassa']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
