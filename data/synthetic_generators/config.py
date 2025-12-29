"""
Configuration and Constants for Abu Dhabi Synthetic Data Generation
All data aligned with UAE social support context
"""

from typing import Dict, List
from enum import Enum

# ============================================================================
# PERSONAL DATA CONFIGURATION
# ============================================================================

UAE_FIRST_NAMES_MALE = [
    "Ahmed", "Mohammed", "Ali", "Khalid", "Youssef", "Omar", "Hassan", "Ibrahim",
    "Abdullah", "Rashid", "Salem", "Hamad", "Saeed", "Noura", "Faisal", "Nasser",
    "Tariq", "Waleed", "Majid", "Karim", "Mustafa", "Amr", "Jamal", "Kamal",
    "Hazem", "Jassem", "Salim", "Hilal", "Shams", "Anwar"
]

UAE_FIRST_NAMES_FEMALE = [
    "Fatima", "Aisha", "Layla", "Noor", "Sara", "Hana", "Rania", "Leila",
    "Amira", "Dina", "Maya", "Yasmin", "Zainab", "Huda", "Reem", "Maha",
    "Sama", "Aya", "Luna", "Lina", "Rana", "Mona", "Salma", "Shima",
    "Noura", "Hayat", "Mariam", "Wafa", "Rahma", "Dalia"
]

UAE_LAST_NAMES = [
    "Al Maktoum", "Al Nahyan", "Al Suwaidi", "Al Falahi", "Al Mansoori",
    "Al Mazrouei", "Al Nuaimi", "Al Kaabi", "Al Bloushi", "Al Dhaheri",
    "Al Ketbi", "Al Rumaithi", "Al Qubaisi", "Al Marri", "Al Awani",
    "Al Hosani", "Al Shehhi", "Al Memari", "Al Mazroui", "Al Zaabi",
    "Al Jabri", "Al Ameri", "Al Kalbani", "Al Shamsi", "Al Qassimi"
]

MARITAL_STATUSES = ["Single", "Married", "Widowed", "Divorced", "Separated"]

EDUCATION_LEVELS = [
    "High School",
    "Diploma",
    "Bachelor's Degree",
    "Master's Degree",
    "PhD"
]

# ============================================================================
# EMPLOYMENT CONFIGURATION
# ============================================================================

class EmploymentType(str, Enum):
    GOVERNMENT = "Government"
    PRIVATE = "Private"
    SELF_EMPLOYED = "Self-employed"
    UNEMPLOYED = "Unemployed"
    STUDENT = "Student"
    RETIRED = "Retired"

# Government sector employers
GOVERNMENT_EMPLOYERS = [
    ("ADNOC", "Abu Dhabi National Oil Company", "government"),
    ("EWEC", "Emirates Water and Electricity Company", "government"),
    ("ADEC", "Abu Dhabi Education Council", "government"),
    ("ADSIB", "Abu Dhabi Social Insurance Board", "government"),
    ("DEWA", "Dubai Electricity and Water Authority", "government"),
    ("DAMAN", "DAMAN - National Health Insurance", "government"),
    ("DOE", "Department of Energy", "government"),
    ("MOFA", "Ministry of Foreign Affairs", "government"),
    ("MOHRE", "Ministry of Human Resources & Emiratisation", "government"),
    ("Department of Justice", "Department of Justice", "government"),
]

# Private sector employers
PRIVATE_EMPLOYERS = [
    ("FAB", "First Abu Dhabi Bank", "private"),
    ("ADIB", "Abu Dhabi Islamic Bank", "private"),
    ("Emirates Islamic", "Emirates Islamic Bank", "private"),
    ("ENOC", "Emirates National Oil Company", "private"),
    ("Etihad Airways", "Etihad Airways", "private"),
    ("Emaar Properties", "Emaar Properties", "private"),
    ("Rotana Hotels", "Rotana Hotels", "private"),
    ("Al Futtaim Group", "Al Futtaim Group", "private"),
    ("Mashreq Bank", "Mashreq Bank", "private"),
    ("Lulu Hypermarket", "Lulu Hypermarket", "private"),
    ("Carrefour UAE", "Carrefour UAE", "private"),
    ("Noon.com", "Noon.com", "private"),
    ("Liwa Insurance", "Liwa Insurance", "private"),
    ("Al Ain University", "Al Ain University", "private"),
    ("American University of Sharjah", "American University of Sharjah", "private"),
]

JOB_TITLES = {
    "Government": [
        "Accountant", "Admin Officer", "Clerk", "Manager", "Supervisor",
        "Engineer", "Technician", "Teacher", "Nurse", "Doctor",
        "Specialist", "Consultant", "Director"
    ],
    "Private": [
        "Bank Teller", "Accountant", "Sales Representative", "Manager",
        "Customer Service", "IT Support", "Cashier", "Security Officer",
        "Driver", "Consultant", "Engineer", "Analyst", "Specialist"
    ],
    "Self-employed": [
        "Trader", "Contractor", "Consultant", "Business Owner", "Freelancer",
        "Shop Owner", "Service Provider"
    ],
    "Unemployed": [
        "Job Seeker", "Recent Graduate", "Career Changer"
    ],
    "Student": [
        "University Student", "College Student", "Graduate Student"
    ]
}

# ============================================================================
# INCOME & FINANCIAL CONFIGURATION
# ============================================================================

INCOME_RANGES = {
    "Low": (3000, 8000),           # 30% - Eligible
    "Medium": (8000, 15000),       # 40% - Borderline
    "High": (15000, 50000)         # 30% - Ineligible
}

INCOME_DISTRIBUTION = {
    "Low": 0.30,
    "Medium": 0.40,
    "High": 0.30
}

# For expense simulation
EXPENSE_CATEGORIES = {
    "Rent": (1500, 5000),
    "Utilities": (200, 500),
    "Groceries": (500, 1500),
    "Transportation": (300, 1000),
    "Healthcare": (200, 800),
    "Education": (0, 2000),
    "Entertainment": (100, 500),
    "Other": (200, 800)
}

# ============================================================================
# FAMILY CONFIGURATION
# ============================================================================

FAMILY_SIZE_DISTRIBUTION = {
    "1": 0.20,      # Single, no dependents
    "2": 0.10,      # Single with 1 dependent
    "3": 0.15,      # Married, no children
    "4": 0.25,      # Married with 1-2 children
    "5": 0.20,      # Married with 3 children
    "6+": 0.10      # Large family (3+ children or extended family)
}

# ============================================================================
# HOUSING CONFIGURATION
# ============================================================================

class HousingType(str, Enum):
    OWNS = "Own (with mortgage)"
    OWNS_FREE = "Own (paid off)"
    RENTS = "Rent"
    FAMILY = "Live with family"

HOUSING_DISTRIBUTION = {
    "Own (with mortgage)": 0.15,
    "Own (paid off)": 0.05,
    "Rent": 0.60,
    "Live with family": 0.20
}

# ============================================================================
# ASSETS & LIABILITIES
# ============================================================================

ASSET_PROPERTY_VALUES = {
    "Small Apartment": (300000, 600000),
    "Medium Villa": (800000, 1500000),
    "Large Villa": (1500000, 3000000),
    "Townhouse": (500000, 900000)
}

VEHICLE_VALUES = {
    "Economy Car": (30000, 80000),
    "Mid-range Car": (80000, 150000),
    "Premium Car": (150000, 300000),
    "Luxury Car": (300000, 600000)
}

LOAN_TYPES = {
    "Mortgage": (200000, 2000000),
    "Auto Loan": (30000, 200000),
    "Personal Loan": (10000, 100000),
    "Credit Card": (1000, 50000)
}

# ============================================================================
# CREDIT REPORT CONFIGURATION
# ============================================================================

CREDIT_SCORE_RANGES = {
    "Excellent": (1600, 1800),
    "Very Good": (1400, 1599),
    "Good": (1200, 1399),
    "Fair": (1000, 1199),
    "Poor": (0, 999)
}

# ============================================================================
# DOCUMENT NAMES & FORMATS
# ============================================================================

DOCUMENT_TYPES = {
    "bank_statement": "bank_statement.pdf",
    "emirates_id": "emirates_id.png",
    "employment_letter": "employment_letter.pdf",
    "resume": "resume.pdf",
    "assets_liabilities": "assets_liabilities.xlsx",
    "credit_report": "credit_report.json"
}

# ============================================================================
# TEST CASE SCENARIOS
# ============================================================================

TEST_CASE_PROFILES = {
    "test_001": {
        "name": "Ahmed Al Mazrouei",
        "scenario": "APPROVED - Classic Eligible",
        "monthly_income": 8500,
        "family_size": 4,
        "employment_status": "Government",
        "employment_years": 5,
        "marital_status": "Married",
        "housing": "Rent",
        "education": "Bachelor's Degree",
        "expected_decision": "APPROVED"
    },
    "test_002": {
        "name": "Fatima Al Maktoum",
        "scenario": "DECLINED - High Income",
        "monthly_income": 35000,
        "family_size": 3,
        "employment_status": "Private",
        "employment_years": 8,
        "marital_status": "Married",
        "housing": "Own (with mortgage)",
        "education": "Master's Degree",
        "expected_decision": "DECLINED"
    },
    "test_003": {
        "name": "Mohammed Al Nuaimi",
        "scenario": "APPROVED - Large Family Priority",
        "monthly_income": 12000,
        "family_size": 6,
        "employment_status": "Self-employed",
        "employment_years": 3,
        "marital_status": "Married",
        "housing": "Live with family",
        "education": "Diploma",
        "expected_decision": "APPROVED"
    },
    "test_004": {
        "name": "Layla Al Falahi",
        "scenario": "CONFLICT - Income Mismatch",
        "monthly_income": 8500,
        "income_variance": True,  # Will create inconsistencies
        "family_size": 2,
        "employment_status": "Private",
        "employment_years": 4,
        "marital_status": "Single",
        "housing": "Rent",
        "education": "Diploma",
        "expected_decision": "NEEDS_REVIEW"
    },
    "test_005": {
        "name": "Omar Al Kaabi",
        "scenario": "INCOMPLETE - Missing Documents",
        "monthly_income": 7000,
        "incomplete_documents": True,
        "family_size": 3,
        "employment_status": "Government",
        "employment_years": 2,
        "marital_status": "Married",
        "housing": "Rent",
        "education": "High School",
        "expected_decision": "PENDING"
    },
    "test_006": {
        "name": "Sara Al Mansoori",
        "scenario": "APPROVED + ENABLEMENT - Single Parent",
        "monthly_income": 6500,
        "family_size": 3,
        "employment_status": "Unemployed",
        "employment_years": 0,
        "previous_job": "Accountant",
        "marital_status": "Single",
        "housing": "Rent",
        "education": "Bachelor's Degree",
        "expected_decision": "APPROVED_WITH_ENABLEMENT"
    },
    "test_007": {
        "name": "Noor Al Suwaidi",
        "scenario": "APPROVED + ENABLEMENT - Recent Graduate",
        "monthly_income": 0,
        "savings": 25000,
        "family_size": 1,
        "employment_status": "Student",
        "employment_years": 0,
        "marital_status": "Single",
        "housing": "Live with family",
        "education": "Bachelor's Degree",
        "expected_decision": "APPROVED_WITH_ENABLEMENT"
    },
    "test_008": {
        "name": "Khalid Al Heemi",
        "scenario": "CONDITIONAL - Self-Employed Variable",
        "monthly_income": 12000,
        "income_variable": True,
        "family_size": 4,
        "employment_status": "Self-employed",
        "employment_years": 6,
        "marital_status": "Married",
        "housing": "Own (with mortgage)",
        "education": "Diploma",
        "expected_decision": "CONDITIONAL"
    },
    "test_009": {
        "name": "Amira Al Dhaheri",
        "scenario": "DECLINED - Asset Rich, Income Poor",
        "monthly_income": 5000,
        "total_assets": 250000,
        "total_liabilities": 180000,
        "family_size": 2,
        "employment_status": "Self-employed",
        "employment_years": 8,
        "marital_status": "Single",
        "housing": "Own (paid off)",
        "education": "Bachelor's Degree",
        "expected_decision": "DECLINED"
    },
    "test_010": {
        "name": "Youssef Al Bloushi",
        "scenario": "APPROVED - Complex Multiple Income",
        "monthly_income": 13000,
        "secondary_income": 3000,
        "family_size": 5,
        "employment_status": "Private",
        "employment_years": 7,
        "side_business": True,
        "marital_status": "Married",
        "housing": "Rent",
        "education": "Bachelor's Degree",
        "expected_decision": "APPROVED"
    }
}

# ============================================================================
# VALIDATION RULES
# ============================================================================

ELIGIBILITY_THRESHOLD = 15000  # Monthly income threshold in AED

ELIGIBILITY_CRITERIA = {
    "income_threshold": 15000,
    "family_size_weight": 0.15,
    "employment_stability_weight": 0.10,
    "asset_liability_ratio_threshold": 0.75,
    "min_family_size_for_consideration": 3
}

# ============================================================================
# DEFAULTS
# ============================================================================

DEFAULT_RANDOM_SEED = 42
DEFAULT_DATASET_SIZE_TRAINING = 100
DEFAULT_DATASET_SIZE_BULK = 500
DEFAULT_TEST_SIZE = 10
