"""Test script for PPT2Preview API."""

import requests
import time
import json
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_health():
    """Test health check endpoint."""
    print("=" * 80)
    print("Testing Health Check")
    print("=" * 80)
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✓ Health check passed\n")


def test_upload():
    """Test file upload endpoint."""
    print("=" * 80)
    print("Testing File Upload")
    print("=" * 80)
    
    # Check if test files exist
    abstract_file = Path("three_pig_page_abstract.md")
    pdf_file = Path("three_pig_pdf.pdf")
    
    if not abstract_file.exists():
        print(f"❌ Abstract file not found: {abstract_file}")
        return None
    
    if not pdf_file.exists():
        print(f"❌ PDF file not found: {pdf_file}")
        return None
    
    # Upload files
    files = {
        "abstract_file": (abstract_file.name, open(abstract_file, "rb"), "text/markdown"),
    }
    
    if pdf_file.exists():
        files["pdf_file"] = (pdf_file.name, open(pdf_file, "rb"), "application/pdf")
    
    response = requests.post(f"{API_BASE}/upload", files=files)
    
    # Close file handles
    for file_tuple in files.values():
        if hasattr(file_tuple[1], 'close'):
            file_tuple[1].close()
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    task_id = response.json()["task_id"]
    print(f"✓ Upload successful, task_id: {task_id}\n")
    return task_id


def test_get_status(task_id: str):
    """Test status endpoint."""
    print("=" * 80)
    print("Testing Get Status")
    print("=" * 80)
    
    response = requests.get(f"{API_BASE}/status/{task_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    assert response.status_code == 200
    print("✓ Get status successful\n")


def test_generate_script(task_id: str):
    """Test script generation endpoint."""
    print("=" * 80)
    print("Testing Generate Script")
    print("=" * 80)
    
    payload = {
        "task_id": task_id,
        "length_mode": "SHORT"  # Use SHORT for faster testing
    }
    
    response = requests.post(
        f"{API_BASE}/generate-script",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    assert response.status_code == 200
    print("✓ Script generation started\n")
    
    # Wait for script generation (poll status)
    print("Waiting for script generation...")
    max_wait = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status_response = requests.get(f"{API_BASE}/status/{task_id}")
        status_data = status_response.json()
        status = status_data["status"]
        progress = status_data.get("progress", 0)
        message = status_data.get("message", "")
        
        print(f"  Status: {status}, Progress: {progress:.1f}%, Message: {message}")
        
        if status == "script_ready":
            print("✓ Script generation completed\n")
            return True
        elif status == "failed":
            print(f"❌ Script generation failed: {status_data.get('error', 'Unknown error')}\n")
            return False
        
        time.sleep(2)
    
    print("⚠️  Script generation timeout\n")
    return False


def test_get_script(task_id: str):
    """Test get script endpoint."""
    print("=" * 80)
    print("Testing Get Script")
    print("=" * 80)
    
    response = requests.get(f"{API_BASE}/script/{task_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        script_content = data.get("script_content", "")
        print(f"Script length: {len(script_content)} characters")
        print(f"Transcription items: {len(data.get('transcription_data', []))}")
        print(f"✓ Get script successful\n")
        return True
    else:
        print(f"Response: {response.json()}")
        print("❌ Get script failed\n")
        return False


def test_update_script(task_id: str):
    """Test update script endpoint."""
    print("=" * 80)
    print("Testing Update Script")
    print("=" * 80)
    
    # Get current script
    get_response = requests.get(f"{API_BASE}/script/{task_id}")
    if get_response.status_code != 200:
        print("❌ Cannot get script to update\n")
        return False
    
    current_script = get_response.json()["script_content"]
    
    # Add a test comment
    updated_script = current_script + "\n\n<!-- Test update -->"
    
    payload = {
        "script_content": updated_script
    }
    
    response = requests.put(
        f"{API_BASE}/script/{task_id}",
        json=payload
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✓ Script update successful\n")
        return True
    else:
        print(f"Response: {response.json()}")
        print("❌ Script update failed\n")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("PPT2Preview API Test Suite")
    print("=" * 80 + "\n")
    
    # Check if server is running
    try:
        test_health()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server. Please start the server first:")
        print("   cd backend && python main.py")
        print("   or")
        print("   uvicorn backend.main:app --reload")
        return
    
    # Run tests
    task_id = test_upload()
    if not task_id:
        print("❌ Upload test failed, skipping remaining tests")
        return
    
    test_get_status(task_id)
    
    # Test script generation (this may take a while)
    if test_generate_script(task_id):
        test_get_script(task_id)
        test_update_script(task_id)
    
    print("=" * 80)
    print("Test Suite Complete")
    print("=" * 80)
    print(f"\nTask ID: {task_id}")
    print(f"Status endpoint: {API_BASE}/status/{task_id}")
    print(f"Script endpoint: {API_BASE}/script/{task_id}")


if __name__ == "__main__":
    main()

