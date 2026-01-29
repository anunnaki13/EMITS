# Excel parsing services for Smart Stock
import pandas as pd
import io
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

def parse_smart_stock_excel(contents: bytes) -> List[Dict[str, Any]]:
    """
    Parse Excel file for Smart Stock (Sumber Penerimaan) with complex merged headers.
    
    Expected structure:
    Row 0: Main headers (TANGGAL, STOCK AWAL, SUMBER PENERIMAAN, TOTAL PENERIMAAN, [Supplier names...])
    Row 1: Sub-headers (A, B, C for each supplier)
    Row 2+: Data rows
    """
    df = pd.read_excel(io.BytesIO(contents), header=None)
    
    # Get header rows
    header_row_0 = df.iloc[0].tolist()
    header_row_1 = df.iloc[1].tolist() if len(df) > 1 else []
    
    logger.info(f"Header row 0: {header_row_0[:10]}...")
    logger.info(f"Header row 1: {header_row_1[:10]}...")
    
    # Find supplier columns (skip TANGGAL, STOCK AWAL, SUMBER PENERIMAAN/TOTAL PENERIMAAN)
    # Suppliers start after the fixed columns
    supplier_columns = {}
    current_supplier = None
    col_start = None
    
    # Keywords to skip - these are not supplier names
    skip_keywords = [
        'TANGGAL', 'STOCK', 'AWAL', 'SUMBER', 'PENERIMAAN', 'TOTAL', 
        'TOTALPENERIMAAN', 'TOTAL_PENERIMAAN', 'TOTAL PENERIMAAN',
        'A', 'B', 'C', 'MT', 'AKHIR', 'STOCK AKHIR'
    ]
    
    for col_idx, cell_value in enumerate(header_row_0):
        if pd.notna(cell_value):
            cell_str = str(cell_value).strip().upper()
            
            # Skip non-supplier columns
            if any(keyword in cell_str for keyword in skip_keywords):
                # If we were tracking a supplier, save it
                if current_supplier and col_start is not None:
                    supplier_columns[current_supplier] = (col_start, col_idx)
                    current_supplier = None
                    col_start = None
                continue
            
            # This looks like a supplier name
            if current_supplier and col_start is not None:
                supplier_columns[current_supplier] = (col_start, col_idx)
            
            current_supplier = str(cell_value).strip()
            col_start = col_idx
    
    # Add the last supplier
    if current_supplier and col_start is not None:
        supplier_columns[current_supplier] = (col_start, len(df.columns))
    
    logger.info(f"Found suppliers: {list(supplier_columns.keys())}")
    
    # Parse data rows
    parsed_data = []
    for idx in range(2, len(df)):
        row = df.iloc[idx]
        
        # Skip if date is empty
        if pd.isna(row.iloc[0]):
            continue
        
        # Parse date
        try:
            date_value = row.iloc[0]
            if isinstance(date_value, (int, float)):
                date_value = pd.to_datetime(date_value, origin='1899-12-30', unit='D')
            else:
                date_value = pd.to_datetime(date_value)
            date_str = date_value.strftime("%Y-%m-%d")
        except Exception as e:
            logger.warning(f"Date parsing error at row {idx}: {e}")
            continue
        
        # Get stock awal (column 1)
        stock_awal = _safe_float(row.iloc[1]) if len(row) > 1 else 0.0
        
        # Get total penerimaan - find the column with "TOTAL" in header
        total_penerimaan = 0.0
        for col_idx, header in enumerate(header_row_0):
            if pd.notna(header) and 'TOTAL' in str(header).upper() and 'PENERIMAAN' in str(header).upper():
                total_penerimaan = _safe_float(row.iloc[col_idx])
                break
        
        # If not found, try column 3
        if total_penerimaan == 0.0 and len(row) > 3:
            total_penerimaan = _safe_float(row.iloc[3])
        
        # Parse supplier data
        suppliers_data = {}
        for supplier_name, (start_col, end_col) in supplier_columns.items():
            supplier_key = _normalize_supplier_name(supplier_name)
            
            zones = {"A": 0.0, "B": 0.0, "C": 0.0}
            zone_keys = ["A", "B", "C"]
            
            for i, col in enumerate(range(start_col, min(start_col + 3, end_col))):
                if col < len(row) and i < 3:
                    zones[zone_keys[i]] = _safe_float(row.iloc[col])
            
            suppliers_data[supplier_key] = zones
        
        # Calculate stock akhir
        stock_akhir = stock_awal + total_penerimaan
        
        parsed_data.append({
            "date": date_str,
            "stock_awal": stock_awal,
            "suppliers": suppliers_data,
            "total_penerimaan": total_penerimaan,
            "stock_akhir": stock_akhir
        })
    
    return parsed_data


def parse_sumber_pemakaian_excel(contents: bytes) -> List[Dict[str, Any]]:
    """
    Parse Excel file for Sumber Pemakaian with complex merged headers.
    
    Expected structure:
    Row 0: Main headers (TANGGAL, UNIT 1, UNIT 2, etc.)
    Row 1: Sub-headers for each unit
    Row 2+: Data rows
    """
    df = pd.read_excel(io.BytesIO(contents), header=None)
    
    header_row_0 = df.iloc[0].tolist()
    header_row_1 = df.iloc[1].tolist() if len(df) > 1 else []
    
    logger.info(f"Pemakaian Header row 0: {header_row_0[:10]}...")
    
    # Find UNIT 1 and UNIT 2 column ranges
    unit1_cols = None
    unit2_cols = None
    
    for col_idx, cell in enumerate(header_row_0):
        if pd.notna(cell):
            cell_str = str(cell).upper()
            if 'UNIT' in cell_str and '1' in cell_str:
                unit1_start = col_idx
            elif 'UNIT' in cell_str and '2' in cell_str:
                unit2_start = col_idx
                if unit1_cols is None:
                    unit1_cols = (unit1_start, col_idx)
    
    # Get sub-headers for detailed fields
    unit1_subheaders = []
    unit2_subheaders = []
    
    if unit1_cols:
        for col in range(unit1_cols[0], unit1_cols[1] if unit1_cols[1] else len(header_row_1)):
            if col < len(header_row_1) and pd.notna(header_row_1[col]):
                unit1_subheaders.append((col, str(header_row_1[col]).strip()))
    
    # Parse data rows
    parsed_data = []
    for idx in range(2, len(df)):
        row = df.iloc[idx]
        
        if pd.isna(row.iloc[0]):
            continue
        
        # Parse date
        try:
            date_value = row.iloc[0]
            if isinstance(date_value, (int, float)):
                date_value = pd.to_datetime(date_value, origin='1899-12-30', unit='D')
            else:
                date_value = pd.to_datetime(date_value)
            date_str = date_value.strftime("%Y-%m-%d")
        except Exception as e:
            logger.warning(f"Date parsing error at row {idx}: {e}")
            continue
        
        # Get burn values - typically first numeric columns after date
        unit1_burn = _safe_float(row.iloc[1]) if len(row) > 1 else 0.0
        unit2_burn = _safe_float(row.iloc[2]) if len(row) > 2 else 0.0
        
        # Parse detailed unit data
        unit1_details = {}
        unit2_details = {}
        
        for col_idx, subheader in unit1_subheaders:
            if col_idx < len(row):
                key = _normalize_supplier_name(subheader)
                unit1_details[key] = _safe_float(row.iloc[col_idx])
        
        parsed_data.append({
            "date": date_str,
            "unit1_burn": unit1_burn,
            "unit2_burn": unit2_burn,
            "unit1_details": unit1_details,
            "unit2_details": unit2_details
        })
    
    return parsed_data


def _safe_float(value) -> float:
    """Safely convert value to float"""
    if pd.isna(value) or value == '' or value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _normalize_supplier_name(name: str) -> str:
    """Normalize supplier name for use as dictionary key"""
    if not name:
        return "UNKNOWN"
    return (str(name)
            .strip()
            .replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("&", "")
            .replace("-", "_")
            .upper())
