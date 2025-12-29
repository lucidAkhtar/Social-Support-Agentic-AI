"""
PersonGenerator: Realistic UAE Person Data Generation
Generates valid Emirates IDs with check digits, names, contact info
Production-grade for Abu Dhabi context
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from .config import (
    UAE_FIRST_NAMES_MALE, UAE_FIRST_NAMES_FEMALE, UAE_LAST_NAMES,
    MARITAL_STATUSES, EDUCATION_LEVELS
)


class PersonGenerator:
    """Generate realistic UAE person data with valid Emirates IDs."""
    
    def __init__(self, seed: int = None):
        """
        Initialize PersonGenerator.
        
        Args:
            seed: Random seed for reproducibility
        """
        if seed is not None:
            random.seed(seed)
        self.generated_ids = set()  # Track to avoid duplicates
    
    def generate_emirates_id(self) -> str:
        """
        Generate valid Emirates ID in format: XXX-YYYY-ZZZZZZZZ-C
        Where C is Luhn check digit
        
        Returns:
            str: Valid Emirates ID
        """
        while True:
            # XXX: Birth year (784 = UAE, we use it as-is)
            birth_year = random.randint(1950, 2010)
            
            # YYYY: Birth month (01-12) + Birth day (01-31)
            # Format: MMDD
            month = random.randint(1, 12)
            day = random.randint(1, 28)  # Safe day range
            middle_part = f"{month:02d}{day:02d}"
            
            # ZZZZZZZZ: Sequential registration number (8 digits)
            # Using realistic range
            sequence = random.randint(10000000, 99999999)
            
            # Construct ID without check digit
            id_without_check = f"{birth_year}{middle_part}{sequence}"
            
            # Calculate Luhn check digit
            check_digit = self._calculate_luhn_check_digit(id_without_check)
            
            # Format as XXX-YYYY-ZZZZZZZZ-C
            emirates_id = f"{birth_year}-{middle_part}-{sequence:08d}-{check_digit}"
            
            if emirates_id not in self.generated_ids:
                self.generated_ids.add(emirates_id)
                return emirates_id
    
    @staticmethod
    def _calculate_luhn_check_digit(id_number: str) -> int:
        """
        Calculate Luhn check digit for Emirates ID.
        
        Args:
            id_number: ID number without check digit
            
        Returns:
            int: Check digit (0-9)
        """
        total = 0
        for i, digit in enumerate(reversed(id_number)):
            n = int(digit)
            # Double every second digit from right
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        
        check_digit = (10 - (total % 10)) % 10
        return check_digit
    
    def generate_phone(self) -> str:
        """
        Generate valid UAE phone number.
        Format: +971-XX-XXX-XXXX
        
        Returns:
            str: Phone number
        """
        # UAE mobile prefixes: 50, 51, 52, 54, 55, 56
        mobile_prefix = random.choice([50, 51, 52, 54, 55, 56])
        
        # Next 3 digits
        middle = random.randint(100, 999)
        
        # Last 4 digits
        last = random.randint(1000, 9999)
        
        return f"+971-{mobile_prefix}-{middle}-{last}"
    
    def generate_email(self, first_name: str, last_name: str) -> str:
        """
        Generate realistic email address.
        
        Args:
            first_name: Person's first name
            last_name: Person's last name
            
        Returns:
            str: Email address
        """
        first_lower = first_name.lower().replace(" ", "")
        last_lower = last_name.lower().replace(" ", "")
        
        domains = ["gmail.com", "yahoo.com", "outlook.com", "emirates.net.ae"]
        domain = random.choice(domains)
        
        # Sometimes include full name, sometimes first.last
        if random.random() > 0.5:
            return f"{first_lower}.{last_lower}@{domain}"
        else:
            return f"{first_lower}{last_lower}{random.randint(100, 999)}@{domain}"
    
    def generate_name(self) -> Tuple[str, str, str]:
        """
        Generate realistic UAE person name.
        
        Returns:
            Tuple: (first_name, last_name, full_name)
        """
        gender = random.choice(["M", "F"])
        
        if gender == "M":
            first_name = random.choice(UAE_FIRST_NAMES_MALE)
        else:
            first_name = random.choice(UAE_FIRST_NAMES_FEMALE)
        
        last_name = random.choice(UAE_LAST_NAMES)
        full_name = f"{first_name} {last_name}"
        
        return first_name, last_name, full_name
    
    def generate_date_of_birth(self, min_age: int = 20, max_age: int = 65) -> Tuple[str, int]:
        """
        Generate realistic date of birth.
        
        Args:
            min_age: Minimum age in years
            max_age: Maximum age in years
            
        Returns:
            Tuple: (dob_string, age)
        """
        today = datetime.now()
        min_date = today - timedelta(days=max_age * 365)
        max_date = today - timedelta(days=min_age * 365)
        
        dob = datetime.fromtimestamp(
            random.uniform(min_date.timestamp(), max_date.timestamp())
        )
        
        age = today.year - dob.year
        if (today.month, today.day) < (dob.month, dob.day):
            age -= 1
        
        dob_string = dob.strftime("%Y-%m-%d")
        return dob_string, age
    
    def generate_marital_status(self, age: int) -> str:
        """
        Generate realistic marital status based on age.
        
        Args:
            age: Person's age
            
        Returns:
            str: Marital status
        """
        if age < 22:
            # Younger people unlikely to be married
            return random.choices(
                MARITAL_STATUSES,
                weights=[0.95, 0.03, 0, 0.02, 0],
                k=1
            )[0]
        elif age < 30:
            return random.choices(
                MARITAL_STATUSES,
                weights=[0.50, 0.40, 0.02, 0.05, 0.03],
                k=1
            )[0]
        else:
            return random.choices(
                MARITAL_STATUSES,
                weights=[0.30, 0.55, 0.05, 0.08, 0.02],
                k=1
            )[0]
    
    def generate_education_level(self) -> str:
        """
        Generate realistic education level.
        
        Returns:
            str: Education level
        """
        return random.choices(
            EDUCATION_LEVELS,
            weights=[0.20, 0.30, 0.35, 0.12, 0.03],  # Bachelor's most common
            k=1
        )[0]
    
    def generate_dependents(self, marital_status: str, age: int) -> int:
        """
        Generate realistic number of dependents based on marital status and age.
        
        Args:
            marital_status: Person's marital status
            age: Person's age
            
        Returns:
            int: Number of dependents
        """
        if marital_status == "Single":
            if age > 35:
                # Older single people might have dependents
                return random.choices([0, 1, 2], weights=[0.70, 0.20, 0.10], k=1)[0]
            else:
                return random.choices([0, 1], weights=[0.85, 0.15], k=1)[0]
        
        elif marital_status == "Married":
            # Weighted towards having children
            return random.choices([0, 1, 2, 3, 4, 5], 
                                weights=[0.15, 0.20, 0.30, 0.20, 0.10, 0.05], 
                                k=1)[0]
        
        elif marital_status == "Widowed":
            # Often have grown children
            return random.choices([1, 2, 3, 4], weights=[0.30, 0.40, 0.20, 0.10], k=1)[0]
        
        elif marital_status == "Divorced":
            # May have children from previous marriage
            return random.choices([0, 1, 2, 3], weights=[0.40, 0.35, 0.20, 0.05], k=1)[0]
        
        else:  # Separated
            return random.choices([0, 1, 2], weights=[0.50, 0.35, 0.15], k=1)[0]
    
    def generate_person(self) -> Dict[str, Any]:
        """
        Generate complete person record.
        
        Returns:
            Dict: Complete person data
        """
        first_name, last_name, full_name = self.generate_name()
        dob, age = self.generate_date_of_birth()
        marital_status = self.generate_marital_status(age)
        dependents = self.generate_dependents(marital_status, age)
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "emirates_id": self.generate_emirates_id(),
            "date_of_birth": dob,
            "age": age,
            "nationality": "UAE National",  # Can adjust if needed
            "phone": self.generate_phone(),
            "email": self.generate_email(first_name, last_name),
            "marital_status": marital_status,
            "education_level": self.generate_education_level(),
            "num_dependents": dependents,
            "family_size": 1 + dependents
        }


# Quick test
if __name__ == "__main__":
    gen = PersonGenerator(seed=42)
    
    print("=" * 60)
    print("PERSON DATA GENERATION TEST")
    print("=" * 60)
    
    for i in range(5):
        person = gen.generate_person()
        print(f"\nPerson {i+1}:")
        print(f"  Name: {person['full_name']}")
        print(f"  Emirates ID: {person['emirates_id']}")
        print(f"  Age: {person['age']}")
        print(f"  Phone: {person['phone']}")
        print(f"  Email: {person['email']}")
        print(f"  Marital Status: {person['marital_status']}")
        print(f"  Family Size: {person['family_size']}")
        print(f"  Education: {person['education_level']}")
