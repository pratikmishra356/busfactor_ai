#!/usr/bin/env python3
"""
Backend API Testing for Context Intelligence Platform
Tests all backend endpoints including context, incident, and role-based APIs
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

class ContextIntelligenceAPITester:
    def __init__(self, base_url="https://slack-thread-intel.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.results = {}

    def log_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name} - PASSED")
        else:
            print(f"❌ {test_name} - FAILED")
            self.failed_tests.append({"test": test_name, "details": details})
        
        self.results[test_name] = {
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }

    def test_api_endpoint(self, name: str, endpoint: str, expected_status: int = 200, 
                         params: Dict = None, timeout: int = 30) -> tuple:
        """Test a single API endpoint"""
        url = f"{self.base_url}/api/{endpoint}"
        
        try:
            print(f"\n🔍 Testing {name}...")
            print(f"   URL: {url}")
            if params:
                print(f"   Params: {params}")
            
            response = requests.get(url, params=params, timeout=timeout)
            
            success = response.status_code == expected_status
            
            details = {
                "status_code": response.status_code,
                "url": url,
                "params": params,
                "response_size": len(response.text) if response.text else 0
            }
            
            if success:
                try:
                    json_data = response.json()
                    details["has_json"] = True
                    details["response_keys"] = list(json_data.keys()) if isinstance(json_data, dict) else []
                    
                    # Check for specific response structure based on endpoint
                    if "context" in endpoint:
                        details["has_context"] = "context" in json_data
                        details["has_sources"] = "sources_used" in json_data
                        details["entity_count"] = json_data.get("entity_count", 0)
                    elif "incident" in endpoint:
                        details["has_report"] = "report" in json_data
                        details["has_timeline"] = "timeline" in json_data
                        details["related_tickets"] = len(json_data.get("related_tickets", []))
                        details["related_prs"] = len(json_data.get("related_prs", []))
                    elif "role" in endpoint:
                        details["has_response"] = "response" in json_data
                        details["role"] = json_data.get("role", "")
                        details["priority_items"] = len(json_data.get("priority_items", []))
                    
                except json.JSONDecodeError:
                    details["has_json"] = False
                    details["response_preview"] = response.text[:200]
            else:
                details["error_message"] = response.text[:500]
            
            self.log_result(name, success, details)
            return success, response.json() if success else {}
            
        except requests.exceptions.Timeout:
            details = {"error": "Request timeout", "timeout": timeout}
            self.log_result(name, False, details)
            return False, {}
        except requests.exceptions.RequestException as e:
            details = {"error": f"Request failed: {str(e)}"}
            self.log_result(name, False, details)
            return False, {}
        except Exception as e:
            details = {"error": f"Unexpected error: {str(e)}"}
            self.log_result(name, False, details)
            return False, {}

    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        return self.test_api_endpoint("Basic API Connectivity", "", expected_status=200)

    def test_context_api(self):
        """Test Knowledge Base context API"""
        test_queries = [
            "payment",
            "database performance", 
            "security issues"
        ]
        
        results = []
        for query in test_queries:
            success, response = self.test_api_endpoint(
                f"Context API - {query}",
                "context",
                params={"query": query, "top_k": 3},
                timeout=45  # LLM calls can be slow
            )
            results.append(success)
        
        return all(results)

    def test_incident_api(self):
        """Test Incident Analysis API"""
        test_queries = [
            "payment outage",
            "email notification failure",
            "database connection issues"
        ]
        
        results = []
        for query in test_queries:
            success, response = self.test_api_endpoint(
                f"Incident API - {query}",
                "incident", 
                params={"query": query},
                timeout=45  # LLM calls can be slow
            )
            results.append(success)
        
        return all(results)

    def test_role_apis(self):
        """Test AI Companion role-based APIs"""
        roles = ["engineer", "product_manager", "engineering_manager"]
        test_queries = [
            "database performance",
            "team incidents",
            "security updates"
        ]
        
        results = []
        for role in roles:
            for query in test_queries:
                success, response = self.test_api_endpoint(
                    f"Role API - {role} - {query}",
                    f"role/{role}/task",
                    params={"query": query},
                    timeout=45  # LLM calls can be slow
                )
                results.append(success)
        
        return all(results)

    def test_mcp_apis(self):
        """Test underlying MCP APIs"""
        # Test MCP search
        success1, _ = self.test_api_endpoint(
            "MCP Search API",
            "mcp/search",
            params={"q": "payment", "top_k": 3}
        )
        
        # Test MCP connections
        success2, _ = self.test_api_endpoint(
            "MCP Connections API", 
            "mcp/connections",
            params={"q": "payment", "top_k": 2, "depth": 1}
        )
        
        return success1 and success2

    def run_all_tests(self):
        """Run comprehensive backend API tests"""
        print("=" * 80)
        print("🚀 Context Intelligence Platform - Backend API Testing")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test basic connectivity first
        print("\n📡 Testing Basic Connectivity...")
        basic_success = self.test_basic_connectivity()
        
        if not basic_success:
            print("\n❌ Basic connectivity failed. Stopping tests.")
            return self.generate_summary()
        
        # Test MCP layer APIs
        print("\n🔧 Testing MCP Layer APIs...")
        self.test_mcp_apis()
        
        # Test application layer APIs
        print("\n📚 Testing Knowledge Base (Context) API...")
        self.test_context_api()
        
        print("\n🚨 Testing Incident Analysis API...")
        self.test_incident_api()
        
        print("\n🤖 Testing AI Companion (Role) APIs...")
        self.test_role_apis()
        
        return self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ Failed Tests ({len(self.failed_tests)}):")
            for i, failure in enumerate(self.failed_tests, 1):
                print(f"  {i}. {failure['test']}")
                if 'error' in failure['details']:
                    print(f"     Error: {failure['details']['error']}")
                elif 'status_code' in failure['details']:
                    print(f"     Status: {failure['details']['status_code']}")
        
        # Determine overall status
        critical_failures = len([f for f in self.failed_tests if any(
            api in f['test'].lower() for api in ['context', 'incident', 'role']
        )])
        
        if critical_failures > 0:
            print(f"\n🚨 CRITICAL: {critical_failures} core API failures detected")
            return False
        elif success_rate < 80:
            print(f"\n⚠️  WARNING: Low success rate ({success_rate:.1f}%)")
            return False
        else:
            print(f"\n✅ SUCCESS: All critical APIs working ({success_rate:.1f}% success rate)")
            return True

def main():
    """Main test execution"""
    tester = ContextIntelligenceAPITester()
    
    try:
        success = tester.run_all_tests()
        
        # Save detailed results
        with open('/app/backend_test_results.json', 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": tester.tests_run,
                    "passed": tester.tests_passed,
                    "failed": len(tester.failed_tests),
                    "success_rate": (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
                    "timestamp": datetime.now().isoformat()
                },
                "failed_tests": tester.failed_tests,
                "all_results": tester.results
            }, indent=2)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())