#!/usr/bin/env python3
"""
Quick Verification Script
Run this to verify the Administration module is properly set up and ready to use.
"""
import sys
import os
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def check_file_exists(path, description=""):
    """Check if a file exists"""
    if os.path.exists(path):
        desc = f" ({description})" if description else ""
        print_success(f"Found: {path}{desc}")
        return True
    else:
        desc = f" ({description})" if description else ""
        print_error(f"Missing: {path}{desc}")
        return False

def verify_project_structure():
    """Verify all required files exist"""
    print_header("PROJECT STRUCTURE VERIFICATION")
    
    PROJECT_ROOT = Path(__file__).parent
    
    required_files = {
        "app.py": "Main Streamlit app",
        "config.py": "Configuration module",
        "test_integration.py": "Integration tests",
        "requirements.txt": "Dependencies",
        "ARCHITECTURE.md": "Architecture docs",
        "SETUP_GUIDE.md": "Setup guide",
        "FOR_YOUR_COLLEAGUE.md": "Colleague integration guide",
        "Back/app/leads_manager.py": "Lead management",
        "Back/app/document_manager.py": "Document management",
        "Back/app/admin_indexer.py": "Index management",
        "Back/app/agents/contact_agent.py": "Contact agent (updated)",
        "admin_pages/__init__.py": "Admin package init",
        "admin_pages/document_management.py": "Document UI",
        "admin_pages/leads_management.py": "Leads UI",
    }
    
    all_found = True
    for file, description in required_files.items():
        path = PROJECT_ROOT / file
        if not check_file_exists(path, description):
            all_found = False
    
    return all_found

def verify_python_version():
    """Verify Python version"""
    print_header("PYTHON VERSION CHECK")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python 3.7+ required, you have {version.major}.{version.minor}")
        return False

def verify_dependencies():
    """Check if required dependencies can be imported"""
    print_header("DEPENDENCY CHECK")
    
    dependencies = {
        "streamlit": "Streamlit (UI framework)",
        "config": "config (custom module)",
        "numpy": "NumPy",
        "pandas": "Pandas",
        "faiss": "FAISS",
        "sentence_transformers": "Sentence Transformers",
        "google.generativeai": "Google Generative AI",
        "dotenv": "python-dotenv",
        "bs4": "BeautifulSoup4",
    }
    
    missing = []
    for module, description in dependencies.items():
        try:
            __import__(module)
            print_success(f"Installed: {description}")
        except ImportError:
            print_warning(f"Not found: {description} (run: pip install -r requirements.txt)")
            missing.append(description)
    
    return len(missing) == 0

def verify_env_file():
    """Check if .env file exists"""
    print_header("ENVIRONMENT FILE CHECK")
    
    env_file = Path(__file__).parent / ".env"
    
    if env_file.exists():
        print_success(".env file found")
        
        # Check for required keys
        with open(env_file, 'r') as f:
            content = f.read()
        
        required_keys = [
            "GEMINI_API_KEY",
            "GEMINI_MODEL",
        ]
        
        all_found = True
        for key in required_keys:
            if key in content:
                print_success(f"Found: {key}")
            else:
                print_warning(f"Missing: {key} (add to .env file)")
                all_found = False
        
        return all_found
    else:
        print_error(".env file not found")
        print_info("Create .env file with GEMINI_API_KEY and GEMINI_MODEL")
        return False

def verify_directories():
    """Verify necessary directories exist or will be created"""
    print_header("DIRECTORY STRUCTURE")
    
    PROJECT_ROOT = Path(__file__).parent
    directories = [
        "Back/app",
        "Back/app/agents",
        "Back/app/rag",
        "admin_pages",
        "data",
    ]
    
    for directory in directories:
        path = PROJECT_ROOT / directory
        if path.exists():
            print_success(f"Found: {directory}")
        else:
            print_warning(f"Will be created: {directory}")
    
    return True

def verify_module_imports():
    """Verify that core modules can be imported"""
    print_header("MODULE IMPORT TEST")
    
    PROJECT_ROOT = Path(__file__).parent
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT / "Back" / "app"))
    
    modules_to_test = {
        "config": "Configuration module",
    }
    
    all_ok = True
    for module_name, description in modules_to_test.items():
        try:
            __import__(module_name)
            print_success(f"Can import: {description}")
        except Exception as e:
            print_error(f"Cannot import {description}: {str(e)}")
            all_ok = False
    
    return all_ok

def print_next_steps():
    """Print next steps for the user"""
    print_header("NEXT STEPS")
    
    print(f"""
{Colors.BOLD}1. Install Dependencies:{Colors.RESET}
   pip install -r requirements.txt

{Colors.BOLD}2. Create Environment File:{Colors.RESET}
   Create .env with:
   - GEMINI_API_KEY=your-key-here
   - GEMINI_MODEL=gemini-2.5-flash

{Colors.BOLD}3. Run Integration Tests:{Colors.RESET}
   python test_integration.py

{Colors.BOLD}4. Start the Application:{Colors.RESET}
   streamlit run app.py

{Colors.BOLD}5. Try the Features:{Colors.RESET}
   - Go to "Administration" tab
   - Upload a document
   - Rebuild index
   - View leads (if any collected)

{Colors.BOLD}6. Integrate with Your Colleague:{Colors.RESET}
   - Read: FOR_YOUR_COLLEAGUE.md
   - Pass context when calling orchestrator
   - Leads will auto-save
    """)

def main():
    """Run all verifications"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔" + "="*58 + "╗")
    print("║" + " ESILV Smart Assistant - Verification Script ".center(58) + "║")
    print("╚" + "="*58 + "╝")
    print(Colors.RESET)
    
    checks = [
        ("Project Structure", verify_project_structure),
        ("Python Version", verify_python_version),
        ("Directory Structure", verify_directories),
        ("Module Imports", verify_module_imports),
        ("Dependencies", verify_dependencies),
        ("Environment File", verify_env_file),
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print_error(f"Error in {check_name}: {str(e)}")
            results[check_name] = False
    
    # Print summary
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check_name, result in results.items():
        status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if result else f"{Colors.RED}❌ FAIL{Colors.RESET}"
        print(f"{status} - {check_name}")
    
    print(f"\nTotal: {passed}/{total} checks passed\n")
    
    if passed == total:
        print_success("All checks passed! System is ready.")
    else:
        print_warning(f"{total - passed} check(s) failed. See above for details.")
    
    print_next_steps()
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
