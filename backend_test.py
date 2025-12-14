#!/usr/bin/env python3
"""
Backend API Testing for Context Intelligence Platform
Tests agent endpoints: CodeHealth and Employee agents
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

class AgentAPITester:
    def __init__(self, base_url="https://dynamic-agent-maker.preview.emergentagent.com"):
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
    
    def test_status_endpoint(self):
        """Test GET /api/status endpoint"""
        return self.test_api_endpoint("Status Endpoint", "status", expected_status=200)

    def test_post_endpoint(self, name: str, endpoint: str, data: Dict, expected_status: int = 200, timeout: int = 30) -> tuple:
        """Test a POST endpoint"""
        url = f"{self.base_url}/api/{endpoint}"
        
        try:
            print(f"\n🔍 Testing {name}...")
            print(f"   URL: {url}")
            print(f"   Data: {json.dumps(data, indent=2)}")
            
            response = requests.post(url, json=data, timeout=timeout, headers={'Content-Type': 'application/json'})
            
            success = response.status_code == expected_status
            
            details = {
                "status_code": response.status_code,
                "url": url,
                "request_data": data,
                "response_size": len(response.text) if response.text else 0
            }
            
            if success:
                try:
                    json_data = response.json()
                    details["has_json"] = True
                    details["response_keys"] = list(json_data.keys()) if isinstance(json_data, dict) else []
                    
                    # Check for specific response structure based on endpoint
                    if "codehealth" in endpoint:
                        details["has_checklist"] = "checklist" in json_data
                        details["has_related_prs"] = "related_prs" in json_data
                        details["checklist_count"] = len(json_data.get("checklist", []))
                        details["related_prs_count"] = len(json_data.get("related_prs", []))
                        details["risk_level"] = json_data.get("risk_level", "")
                    elif "employee" in endpoint:
                        details["role"] = json_data.get("role", "")
                        details["task_type"] = json_data.get("task_type", "")
                        details["has_pr_draft"] = "pr_draft" in json_data and json_data["pr_draft"] is not None
                        details["has_slack_message"] = "slack_message" in json_data and json_data["slack_message"] is not None
                        details["has_general_response"] = "general_response" in json_data and json_data["general_response"] is not None
                    
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

    def test_codehealth_agent(self):
        """Test CodeHealth Agent API"""
        test_pr = {
            "pr_number": 123,
            "title": "feat: add payment retry mechanism",
            "description": "Implements automatic retry for failed payment transactions",
            "author": "test-developer",
            "author_github": "testdev",
            "files_changed": [
                "src/services/payment.py",
                "src/queues/retry.py"
            ],
            "labels": ["feature", "payment"],
            "lines_added": 150,
            "lines_removed": 20,
            "jira_ref": "ENG-500",
            "comments": []
        }
        
        success, response = self.test_post_endpoint(
            "CodeHealth Agent",
            "agent/codehealth",
            test_pr,
            timeout=60  # LLM calls can be slow
        )
        
        return success

    def test_employee_agent_engineer(self):
        """Test Employee Agent - Engineer role"""
        test_data = {
            "role": "engineer",
            "task": "implement payment retry for ENG-500"
        }
        
        success, response = self.test_post_endpoint(
            "Employee Agent - Engineer",
            "agent/employee",
            test_data,
            timeout=60  # LLM calls can be slow
        )
        
        return success

    def test_employee_agent_manager(self):
        """Test Employee Agent - Manager role"""
        test_data = {
            "role": "manager",
            "task": "send slack message about the payment bug fix"
        }
        
        success, response = self.test_post_endpoint(
            "Employee Agent - Manager",
            "agent/employee",
            test_data,
            timeout=60  # LLM calls can be slow
        )
        
        return success

    def run_smoke_tests(self):
        """Run quick smoke tests for agents-related endpoints (no auth)"""
        print("=" * 80)
        print("🚀 Backend Smoke Test - Agents Endpoints (No Auth)")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test 1: GET /api/status should return 200
        print("\n📡 Testing GET /api/status...")
        start_time = datetime.now()
        status_success = self.test_status_endpoint()
        status_latency = (datetime.now() - start_time).total_seconds()
        print(f"   Latency: {status_latency:.3f}s")
        
        # Test 2: POST /api/agent/codehealth with minimal valid PR payload should return 200
        print("\n🔧 Testing POST /api/agent/codehealth...")
        start_time = datetime.now()
        codehealth_success = self.test_codehealth_agent()
        codehealth_latency = (datetime.now() - start_time).total_seconds()
        print(f"   Latency: {codehealth_latency:.3f}s")
        
        # Test 3: POST /api/agent/employee with role=engineer and short task should return 200
        print("\n👨‍💻 Testing POST /api/agent/employee (engineer)...")
        start_time = datetime.now()
        employee_success = self.test_employee_agent_engineer()
        employee_latency = (datetime.now() - start_time).total_seconds()
        print(f"   Latency: {employee_latency:.3f}s")
        
        return self.generate_summary()

    def run_all_tests(self):
        """Run comprehensive backend API tests"""
        print("=" * 80)
        print("🚀 Context Intelligence Platform - Agent API Testing")
        print("=" * 80)
        print(f"Base URL: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test basic connectivity first
        print("\n📡 Testing Basic Connectivity...")
        basic_success = self.test_basic_connectivity()
        
        if not basic_success:
            print("\n❌ Basic connectivity failed. Stopping tests.")
            return self.generate_summary()
        
        # Test Status endpoint
        print("\n📊 Testing Status Endpoint...")
        self.test_status_endpoint()
        
        # Test Agent APIs
        print("\n🔧 Testing CodeHealth Agent API...")
        self.test_codehealth_agent()
        
        print("\n👨‍💻 Testing Employee Agent - Engineer...")
        self.test_employee_agent_engineer()
        
        print("\n👨‍💼 Testing Employee Agent - Manager...")
        self.test_employee_agent_manager()
        
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
            api in f['test'].lower() for api in ['codehealth', 'employee']
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
    import sys
    
    # Check if smoke test is requested
    smoke_test = len(sys.argv) > 1 and sys.argv[1] == "smoke"
    
    tester = AgentAPITester()
    
    try:
        if smoke_test:
            success = tester.run_smoke_tests()
        else:
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
            }, f, indent=2)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())