"""
Excel Parser - Extract assets and liabilities data from Excel files
"""
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import re

try:
    import openpyxl
    import pandas as pd
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False


class ExcelParser:
    """
    Parse Excel files containing assets and liabilities data
    Features:
    - Multiple sheet support
    - Flexible column detection
    - Data validation
    - Error handling
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ExcelParser")
        
        if not EXCEL_SUPPORT:
            self.logger.warning("openpyxl/pandas not available. Install with: pip install openpyxl pandas")
    
    async def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Excel file for assets and liabilities
        
        Args:
            file_path: Path to Excel file
            
        Returns:
            Structured financial data
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return self._get_empty_result()
        
        # If it's a text file (for testing), parse as text
        if file_path.suffix.lower() == '.txt':
            return await self._parse_text_format(file_path)
        
        if not EXCEL_SUPPORT:
            self.logger.error("Excel parsing not available")
            return self._get_empty_result()
        
        try:
            # Try to read Excel file
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                return await self._parse_excel(file_path)
            elif file_path.suffix.lower() == '.csv':
                return await self._parse_csv(file_path)
            else:
                self.logger.warning(f"Unsupported file format: {file_path.suffix}")
                return self._get_empty_result()
                
        except Exception as e:
            self.logger.error(f"Excel parsing failed: {e}")
            return self._get_empty_result()
    
    async def _parse_excel(self, file_path: Path) -> Dict[str, Any]:
        """Parse Excel file using openpyxl"""
        try:
            # Read with pandas for easier processing
            df = pd.read_excel(file_path, sheet_name=0)
            
            return self._extract_financial_data(df)
            
        except Exception as e:
            self.logger.error(f"Excel parsing error: {e}")
            return self._get_empty_result()
    
    async def _parse_csv(self, file_path: Path) -> Dict[str, Any]:
        """Parse CSV file"""
        try:
            df = pd.read_csv(file_path)
            return self._extract_financial_data(df)
        except Exception as e:
            self.logger.error(f"CSV parsing error: {e}")
            return self._get_empty_result()
    
    async def _parse_text_format(self, file_path: Path) -> Dict[str, Any]:
        """Parse text format (for testing)"""
        try:
            with open(file_path, 'r') as f:
                text = f.read()
            
            # Extract using regex patterns
            assets = {}
            liabilities = {}
            
            # Find ASSETS section
            assets_match = re.search(r'ASSETS:(.*?)(?:LIABILITIES:|TOTAL LIABILITIES:|$)', 
                                    text, re.DOTALL | re.IGNORECASE)
            if assets_match:
                assets_text = assets_match.group(1)
                assets = self._parse_financial_section(assets_text)
            
            # Find LIABILITIES section
            liabilities_match = re.search(r'LIABILITIES:(.*?)(?:NET WORTH:|TOTAL ASSETS:|$)', 
                                         text, re.DOTALL | re.IGNORECASE)
            if liabilities_match:
                liabilities_text = liabilities_match.group(1)
                liabilities = self._parse_financial_section(liabilities_text)
            
            # Calculate totals
            total_assets = sum(assets.values())
            total_liabilities = sum(liabilities.values())
            net_worth = total_assets - total_liabilities
            
            return {
                "total_assets": total_assets,
                "total_liabilities": total_liabilities,
                "net_worth": net_worth,
                "assets": assets,
                "liabilities": liabilities
            }
            
        except Exception as e:
            self.logger.error(f"Text parsing error: {e}")
            return self._get_empty_result()
    
    def _parse_financial_section(self, text: str) -> Dict[str, float]:
        """Parse a financial section (assets or liabilities)"""
        items = {}
        lines = text.split('\n')
        
        for line in lines:
            # Look for pattern: "Item Name: 12345.67 AED"
            match = re.search(r'([^:]+):\s*([\d,]+\.?\d*)\s*(?:AED)?', line)
            if match:
                item_name = match.group(1).strip().lower().replace(' ', '_')
                try:
                    value = float(match.group(2).replace(',', ''))
                    # Skip total lines
                    if 'total' not in item_name:
                        items[item_name] = value
                except ValueError:
                    continue
        
        return items
    
    def _extract_financial_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract financial data from DataFrame"""
        result = {
            "total_assets": 0,
            "total_liabilities": 0,
            "net_worth": 0,
            "assets": {},
            "liabilities": {}
        }
        
        # Try to find relevant columns
        column_map = self._map_columns(df)
        
        if not column_map:
            self.logger.warning("Could not map columns in Excel file")
            return result
        
        # Extract assets
        if "assets_col" in column_map:
            assets_data = df[column_map["assets_col"]].dropna()
            for idx, value in assets_data.items():
                if isinstance(value, (int, float)) and value > 0:
                    item_name = f"asset_{idx}"
                    # Try to get name from another column
                    if "name_col" in column_map:
                        item_name = df.loc[idx, column_map["name_col"]]
                    result["assets"][item_name] = float(value)
        
        # Extract liabilities
        if "liabilities_col" in column_map:
            liabilities_data = df[column_map["liabilities_col"]].dropna()
            for idx, value in liabilities_data.items():
                if isinstance(value, (int, float)) and value > 0:
                    item_name = f"liability_{idx}"
                    if "name_col" in column_map:
                        item_name = df.loc[idx, column_map["name_col"]]
                    result["liabilities"][item_name] = float(value)
        
        # Calculate totals
        result["total_assets"] = sum(result["assets"].values())
        result["total_liabilities"] = sum(result["liabilities"].values())
        result["net_worth"] = result["total_assets"] - result["total_liabilities"]
        
        return result
    
    def _map_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Map DataFrame columns to expected fields"""
        column_map = {}
        
        # Normalize column names
        columns = {col.lower().strip(): col for col in df.columns}
        
        # Find asset column
        asset_keywords = ["asset", "assets", "amount"]
        for keyword in asset_keywords:
            for norm_col, orig_col in columns.items():
                if keyword in norm_col:
                    column_map["assets_col"] = orig_col
                    break
            if "assets_col" in column_map:
                break
        
        # Find liability column
        liability_keywords = ["liability", "liabilities", "debt", "loan"]
        for keyword in liability_keywords:
            for norm_col, orig_col in columns.items():
                if keyword in norm_col:
                    column_map["liabilities_col"] = orig_col
                    break
            if "liabilities_col" in column_map:
                break
        
        # Find name/description column
        name_keywords = ["name", "description", "item", "type"]
        for keyword in name_keywords:
            for norm_col, orig_col in columns.items():
                if keyword in norm_col:
                    column_map["name_col"] = orig_col
                    break
            if "name_col" in column_map:
                break
        
        return column_map
    
    def _get_empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "total_assets": 0,
            "total_liabilities": 0,
            "net_worth": 0,
            "assets": {},
            "liabilities": {}
        }


# Singleton instance
_excel_parser_instance = None

def get_excel_parser() -> ExcelParser:
    """Get or create excel parser singleton"""
    global _excel_parser_instance
    if _excel_parser_instance is None:
        _excel_parser_instance = ExcelParser()
    return _excel_parser_instance
