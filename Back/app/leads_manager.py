"""
Module de gestion des leads/contacts collectés par le chatbot
Stocke les leads au format JSON pour un accès et export facile
"""
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project root to path for config import
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from config import LEADS_DATA_DIR, LEADS_FILE_PATH
    LEADS_DIR = str(LEADS_DATA_DIR)
    LEADS_FILE = str(LEADS_FILE_PATH)
except ImportError:
    # Fallback to defaults if config not available
    LEADS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "leads")
    LEADS_FILE = os.path.join(LEADS_DIR, "leads.json")


def ensure_leads_dir():
    """Create the leads directory if it doesn't exist"""
    os.makedirs(LEADS_DIR, exist_ok=True)


def load_leads() -> List[Dict[str, Any]]:
    """
    Load all leads from the JSON file
    
    Returns:
        List of lead dictionaries
    """
    ensure_leads_dir()
    
    if not os.path.exists(LEADS_FILE):
        return []
    
    try:
        with open(LEADS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_leads(leads: List[Dict[str, Any]]):
    """
    Save leads to the JSON file
    
    Args:
        leads: List of lead dictionaries
    """
    ensure_leads_dir()
    
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)


def add_lead(
    name: str,
    email: str,
    education: Optional[str] = None,
    program_of_interest: Optional[str] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a new lead to the collection
    
    Args:
        name: Lead's name
        email: Lead's email
        education: Current education/background (optional)
        program_of_interest: Program or major of interest (optional)
        message: Additional message or notes (optional)
        
    Returns:
        The created lead dictionary
    """
    leads = load_leads()
    
    new_lead = {
        "id": len(leads) + 1,
        "name": name.strip(),
        "email": email.strip(),
        "education": education.strip() if education else None,
        "program_of_interest": program_of_interest.strip() if program_of_interest else None,
        "message": message.strip() if message else None,
        "created_at": datetime.now().isoformat()
    }
    
    leads.append(new_lead)
    save_leads(leads)
    
    return new_lead


def get_leads() -> List[Dict[str, Any]]:
    """
    Get all leads
    
    Returns:
        List of all leads
    """
    return load_leads()


def get_lead_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get a lead by email address
    
    Args:
        email: Email to search for
        
    Returns:
        Lead dictionary or None if not found
    """
    leads = load_leads()
    for lead in leads:
        if lead["email"].lower() == email.lower():
            return lead
    return None


def delete_lead(lead_id: int) -> bool:
    """
    Delete a lead by ID
    
    Args:
        lead_id: ID of the lead to delete
        
    Returns:
        True if deleted, False if not found
    """
    leads = load_leads()
    initial_count = len(leads)
    leads = [lead for lead in leads if lead.get("id") != lead_id]
    
    if len(leads) < initial_count:
        save_leads(leads)
        return True
    return False


def update_lead(lead_id: int, **kwargs) -> Optional[Dict[str, Any]]:
    """
    Update a lead's information
    
    Args:
        lead_id: ID of the lead to update
        **kwargs: Fields to update (name, email, education, program_of_interest, message)
        
    Returns:
        Updated lead dictionary or None if not found
    """
    leads = load_leads()
    
    for i, lead in enumerate(leads):
        if lead.get("id") == lead_id:
            # Update allowed fields
            for key in ["name", "email", "education", "program_of_interest", "message"]:
                if key in kwargs and kwargs[key] is not None:
                    lead[key] = str(kwargs[key]).strip()
            
            lead["updated_at"] = datetime.now().isoformat()
            leads[i] = lead
            save_leads(leads)
            return lead
    
    return None


def get_leads_count() -> int:
    """Retourne le nombre total de leads"""
    return len(load_leads())


def export_leads_to_csv() -> str:
    """
    Export all leads to CSV format
    
    Returns:
        CSV content as string
    """
    leads = load_leads()
    
    if not leads:
        return ""
    
    import csv
    from io import StringIO
    
    output = StringIO()
    fieldnames = ["ID", "Name", "Email", "Education", "Program of Interest", "Message", "Collected Date"]
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for lead in leads:
        # Parse ISO datetime to readable format
        created_at = lead.get("created_at", "")
        if created_at:
            try:
                dt = datetime.fromisoformat(created_at)
                created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        writer.writerow({
            "ID": lead.get("id", ""),
            "Name": lead.get("name", ""),
            "Email": lead.get("email", ""),
            "Education": lead.get("education", ""),
            "Program of Interest": lead.get("program_of_interest", ""),
            "Message": lead.get("message", ""),
            "Collected Date": created_at
        })
    
    return output.getvalue()


def search_leads(query: str) -> List[Dict[str, Any]]:
    """
    Search leads by name or email
    
    Args:
        query: Search query
        
    Returns:
        List of matching leads
    """
    leads = load_leads()
    query_lower = query.lower()
    
    results = []
    for lead in leads:
        if (query_lower in lead.get("name", "").lower() or
            query_lower in lead.get("email", "").lower()):
            results.append(lead)
    
    return results
