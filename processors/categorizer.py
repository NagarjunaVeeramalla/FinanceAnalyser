import json
import os

class Categorizer:
    def __init__(self):
        self.rules_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'categories.json')
        self.rules = self.load_rules()

    def load_rules(self):
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading categories: {e}")
        
        # Default rules
        defaults = {
            "Food": ["swiggy", "zomato", "restaurant", "cafe", "food", "burger", "pizza", "starbucks", "mcdonalds", "kfc", "tobox ve ntures", "cane hou se"],
            "Grocery": ["samudral a satyanaray", "samudral a satyanaraya"],
            "Shopping": ["amazon", "flipkart", "myntra", "zara", "h&m", "retail", "store", "mart", "mall"],
            "Travel": ["uber", "ola", "rapido", "irctc", "airline", "indigo", "air india", "hotel", "makemytrip", "fuel", "petrol", "shell"],
            "Utilities": ["electricity", "water", "bill", "bescom", "bwssb", "gas", "jio", "airtel", "vodafone"],
            "Rent": ["rent", "landlord", "broker"],
            "Investment": ["zerodha", "groww", "upstox", "mutual fund", "sip", "stocks"],
            "EMI": ["emi", "loan", "bajaj", "finance", "repayment", "installment"],
            "Grooming": ["salon", "barber", "spa", "grooming"],
            "Grooming": ["salon", "barber", "spa", "grooming"],
            "UPI Payment": ["upi", "transfer to", "paid to"],
            "Salary": ["salary", "payroll", "bonus"]
        }
        self.save_rules(defaults)
        return defaults

    def save_rules(self, rules=None):
        if rules is None:
            rules = self.rules
        try:
            with open(self.rules_file, 'w') as f:
                json.dump(rules, f, indent=4)
        except Exception as e:
            print(f"Error saving categories: {e}")

    def categorize(self, description):
        """
        Returns the category based on description keywords.
        Prioritizes specific categories over generic ones like 'UPI Transfer'.
        """
        if not description:
            return "Others"
            
        desc_lower = description.lower()
        
        # 1. Check all categories EXCEPT 'UPI Payment'
        for category, keywords in self.rules.items():
            if category == "UPI Payment":
                continue
            for keyword in keywords:
                if keyword in desc_lower:
                    return category
        
        # 2. Check 'UPI Payment' last (as it's a catch-all for UPI transactions)
        if "UPI Payment" in self.rules:
            for keyword in self.rules["UPI Payment"]:
                if keyword in desc_lower:
                    return "UPI Payment"
                    
        return "Others"

    def add_keyword(self, category, keyword):
        """
        Adds a new keyword to a category. 
        Returns (True, None) if successful.
        Returns (False, existing_category) if keyword already exists.
        """
        keyword = keyword.lower().strip()
        
        # Check if exists anywhere
        for cat, keywords in self.rules.items():
            if keyword in keywords:
                return False, cat
        
        if category not in self.rules:
            self.rules[category] = []
            
        self.rules[category].append(keyword)
        self.save_rules()
        return True, None

    def get_categories(self):
        return list(self.rules.keys())
