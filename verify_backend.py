"""Verify backend code structure and imports."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all backend imports."""
    print("=" * 80)
    print("Testing Backend Imports")
    print("=" * 80)
    
    tests = [
        ("backend.core.config", "Config module"),
        ("backend.core.tasks", "Task manager"),
        ("backend.api.models", "API models"),
        ("backend.services.file_service", "File service"),
        ("backend.services.gemini_service", "Gemini service"),
        ("backend.services.script_generator", "Script generator"),
        ("backend.services.video_generator", "Video generator"),
        ("backend.utils.video_utils", "Video utils"),
        ("backend.api.routes", "API routes"),
        ("backend.main", "Main app"),
    ]
    
    results = []
    for module_name, description in tests:
        try:
            __import__(module_name)
            print(f"✓ {description:30s} - OK")
            results.append((True, description))
        except Exception as e:
            print(f"❌ {description:30s} - FAILED: {e}")
            results.append((False, description, str(e)))
    
    print("\n" + "=" * 80)
    passed = sum(1 for r in results if r[0])
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 80)
    
    if passed == total:
        print("\n✓ All imports successful! Backend is ready to use.")
        print("\nTo start the server, run:")
        print("  ./start_server.sh")
        print("  or")
        print("  conda activate p2v && uvicorn backend.main:app --reload")
        return True
    else:
        print("\n❌ Some imports failed. Please check the errors above.")
        return False


def test_config():
    """Test configuration."""
    print("\n" + "=" * 80)
    print("Testing Configuration")
    print("=" * 80)
    
    try:
        from backend.core.config import (
            BASE_DIR, UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR,
            API_V1_PREFIX, GEMINI_API_KEY, GEMINI_MODEL
        )
        
        print(f"✓ BASE_DIR: {BASE_DIR}")
        print(f"✓ UPLOAD_DIR: {UPLOAD_DIR} (exists: {UPLOAD_DIR.exists()})")
        print(f"✓ OUTPUT_DIR: {OUTPUT_DIR} (exists: {OUTPUT_DIR.exists()})")
        print(f"✓ TEMP_DIR: {TEMP_DIR} (exists: {TEMP_DIR.exists()})")
        print(f"✓ API_V1_PREFIX: {API_V1_PREFIX}")
        print(f"✓ GEMINI_MODEL: {GEMINI_MODEL}")
        
        if GEMINI_API_KEY:
            print(f"✓ GEMINI_API_KEY: Set (length: {len(GEMINI_API_KEY)})")
        else:
            print("⚠️  GEMINI_API_KEY: Not set (required for script generation)")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_app_creation():
    """Test FastAPI app creation."""
    print("\n" + "=" * 80)
    print("Testing FastAPI App Creation")
    print("=" * 80)
    
    try:
        from backend.main import app
        
        print(f"✓ App created: {app.title}")
        print(f"✓ Version: {app.version}")
        
        # Check routes
        routes = [r.path for r in app.routes]
        print(f"✓ Routes registered: {len(routes)}")
        for route in sorted(routes)[:10]:  # Show first 10
            print(f"  - {route}")
        if len(routes) > 10:
            print(f"  ... and {len(routes) - 10} more")
        
        return True
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("PPT2Preview Backend Verification")
    print("=" * 80 + "\n")
    
    success = True
    success &= test_imports()
    success &= test_config()
    success &= test_app_creation()
    
    print("\n" + "=" * 80)
    if success:
        print("✓ Backend verification complete! All tests passed.")
        sys.exit(0)
    else:
        print("❌ Backend verification failed. Please fix the errors above.")
        sys.exit(1)

