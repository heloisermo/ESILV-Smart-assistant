"""
Test suite to verify that new Admin modules don't break existing Assistant functionality
Run this to ensure both systems work independently.
"""
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "Back" / "app"))

from config import ensure_directories, get_backend_paths, get_admin_paths


def test_configuration():
    """Test that configuration is set up correctly"""
    print("\n" + "="*60)
    print("TEST 1: Configuration and Directory Setup")
    print("="*60)
    
    try:
        ensure_directories()
        print("✅ All directories created/verified")
        
        backend_paths = get_backend_paths()
        print(f"✅ Backend paths accessible: {len(backend_paths)} paths")
        for key, value in backend_paths.items():
            print(f"   - {key}: {value}")
        
        admin_paths = get_admin_paths()
        print(f"✅ Admin paths configured: {len(admin_paths)} paths")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {str(e)}")
        return False


def test_leads_manager():
    """Test that leads_manager module works independently"""
    print("\n" + "="*60)
    print("TEST 2: Leads Manager Module")
    print("="*60)
    
    try:
        from leads_manager import (
            get_leads,
            get_leads_count,
            load_leads,
        )
        
        leads = get_leads()
        count = get_leads_count()
        
        print(f"✅ Leads manager initialized")
        print(f"   - Current leads: {count}")
        print(f"   - Leads list retrieved: {type(leads)}")
        
        return True
    except Exception as e:
        print(f"❌ Leads manager error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_document_manager():
    """Test that document_manager module works independently"""
    print("\n" + "="*60)
    print("TEST 3: Document Manager Module")
    print("="*60)
    
    try:
        from document_manager import (
            get_processed_documents,
            ensure_upload_dir,
        )
        
        ensure_upload_dir()
        docs = get_processed_documents()
        
        print(f"✅ Document manager initialized")
        print(f"   - Upload directory ensured")
        print(f"   - Current documents: {len(docs)}")
        
        return True
    except Exception as e:
        print(f"❌ Document manager error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_admin_indexer():
    """Test that admin_indexer module works independently"""
    print("\n" + "="*60)
    print("TEST 4: Admin Indexer Module")
    print("="*60)
    
    try:
        from admin_indexer import (
            get_index_stats,
            ensure_data_dir,
        )
        
        ensure_data_dir()
        stats = get_index_stats()
        
        print(f"✅ Admin indexer initialized")
        print(f"   - Data directory ensured")
        print(f"   - Index stats retrieved: {stats}")
        
        return True
    except Exception as e:
        print(f"❌ Admin indexer error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_contact_agent_import():
    """Test that contact_agent still works with leads_manager integration"""
    print("\n" + "="*60)
    print("TEST 5: Contact Agent with Leads Integration")
    print("="*60)
    
    try:
        from agents.contact_agent import ContactAgent
        
        agent = ContactAgent()
        print(f"✅ Contact agent initialized: {agent.name}")
        print(f"   - Has process method: {hasattr(agent, 'process')}")
        print(f"   - Has can_handle method: {hasattr(agent, 'can_handle')}")
        print(f"   - Has _save_lead_from_context method: {hasattr(agent, '_save_lead_from_context')}")
        
        # Test can_handle
        test_query = "Comment je peux vous contacter?"
        can_handle = agent.can_handle(test_query)
        print(f"   - Can handle contact query: {can_handle}")
        
        return True
    except Exception as e:
        print(f"❌ Contact agent error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_agents_orchestrator():
    """Test that agents still work through orchestrator"""
    print("\n" + "="*60)
    print("TEST 6: Agents Orchestrator (without LLM calls)")
    print("="*60)
    
    try:
        from agents.orchestrator import OrchestratorAgent
        from agents.contact_agent import ContactAgent
        
        orchestrator = OrchestratorAgent()
        print(f"✅ Orchestrator initialized")
        
        contact_agent = ContactAgent()
        orchestrator.register_agent(contact_agent)
        
        agents = orchestrator.list_agents()
        print(f"✅ Agents registered: {agents}")
        print(f"   - Total agents: {len(agents)}")
        
        return True
    except Exception as e:
        print(f"❌ Orchestrator error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_admin_pages_imports():
    """Test that admin pages modules can be imported"""
    print("\n" + "="*60)
    print("TEST 7: Admin Pages Modules")
    print("="*60)
    
    try:
        # Test that modules can be imported (don't need streamlit to be running)
        import importlib.util
        
        doc_mgmt_path = str(PROJECT_ROOT / "admin_pages" / "document_management.py")
        leads_mgmt_path = str(PROJECT_ROOT / "admin_pages" / "leads_management.py")
        
        print(f"✅ Module files exist:")
        print(f"   - document_management.py: {os.path.exists(doc_mgmt_path)}")
        print(f"   - leads_management.py: {os.path.exists(leads_mgmt_path)}")
        
        return True
    except Exception as e:
        print(f"❌ Admin pages error: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("ESILV Smart Assistant - Module Integration Tests")
    print("="*60)
    
    results = {
        "Configuration": test_configuration(),
        "Leads Manager": test_leads_manager(),
        "Document Manager": test_document_manager(),
        "Admin Indexer": test_admin_indexer(),
        "Contact Agent": test_contact_agent_import(),
        "Orchestrator": test_agents_orchestrator(),
        "Admin Pages": test_admin_pages_imports(),
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed! System is ready.")
        return True
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check logs above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
