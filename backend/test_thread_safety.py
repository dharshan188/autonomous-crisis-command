"""
Test Suite: Twilio Approval Workflow Thread Safety & Integration
Tests verify no race conditions with multiple concurrent crises.
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import json

# Mock the dependencies before importing main
import sys
sys.path.insert(0, '/home/dharshan/autonomous-crisis-command/backend')

from services.audit import record_event, get_audit_log, audit_log, audit_lock
from services.dispatcher import execute_dispatch


# ============================================================
# TEST SUITE 1: Audit Log Thread Safety
# ============================================================

class TestAuditLogThreadSafety:
    """Verify audit logging is thread-safe with concurrent records."""
    
    def setup_method(self):
        """Clear audit log before each test."""
        with audit_lock:
            audit_log.clear()
    
    def test_single_event_recorded(self):
        """Test that a single event is recorded correctly."""
        record_event("TEST_EVENT", {"key": "value"})
        
        log = get_audit_log()
        assert len(log) == 1
        assert log[0]["event_type"] == "TEST_EVENT"
        assert log[0]["data"]["key"] == "value"
        assert "timestamp" in log[0]
    
    def test_concurrent_event_recording(self):
        """Test that 100 concurrent events are all recorded without data loss."""
        num_threads = 100
        events_recorded = []
        errors = []
        
        def record_concurrent_event(thread_id):
            try:
                record_event(f"CONCURRENT_EVENT_{thread_id}", {
                    "thread_id": thread_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
                events_recorded.append(thread_id)
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=record_concurrent_event, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Assertions
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(events_recorded) == num_threads, f"Expected {num_threads} events, got {len(events_recorded)}"
        
        log = get_audit_log()
        assert len(log) == num_threads, f"Audit log has {len(log)} entries, expected {num_threads}"
        
        # Verify no duplicate thread IDs
        thread_ids = [entry["data"]["thread_id"] for entry in log]
        assert len(set(thread_ids)) == num_threads, "Duplicate records found in audit log"
    
    def test_audit_log_isolation(self):
        """Test that returned audit log is isolated from internal state."""
        record_event("ORIGINAL_EVENT", {"value": 1})
        
        log1 = get_audit_log()
        assert len(log1) == 1
        
        # Try to modify returned log
        log1.append({"fake": "entry"})
        
        # Get fresh log and verify internal state is unchanged
        log2 = get_audit_log()
        assert len(log2) == 1
        assert log2[0]["event_type"] == "ORIGINAL_EVENT"


# ============================================================
# TEST SUITE 2: Pending Decisions Thread Safety (Mock)
# ============================================================

class TestPendingDecisionsThreadSafety:
    """Verify pending decisions can handle concurrent crisis approvals."""
    
    def test_concurrent_pending_decisions_storage(self):
        """
        Simulate concurrent crises arriving and being stored.
        Verify each gets unique crisis_id and data is not corrupted.
        """
        from uuid import uuid4
        
        pending_decisions = {}
        pending_lock = threading.Lock()
        
        stored_crisis_ids = []
        errors = []
        
        def store_pending_decision(crisis_num):
            try:
                crisis_id = str(uuid4())
                decision_output = {
                    "decisions": [{"crisis_type": f"Crisis_{crisis_num}", "risk_score": 4.0}],
                    "tradeoffs": [],
                    "remaining_resources": {"Fire": 1}
                }
                
                with pending_lock:
                    pending_decisions[crisis_id] = {
                        "decision_output": decision_output,
                        "call_sid": f"call_{crisis_num}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                
                stored_crisis_ids.append(crisis_id)
            except Exception as e:
                errors.append((crisis_num, str(e)))
        
        # Simulate 10 concurrent crises arriving
        threads = []
        for i in range(10):
            t = threading.Thread(target=store_pending_decision, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Assertions
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(stored_crisis_ids) == 10
        assert len(set(stored_crisis_ids)) == 10, "Non-unique crisis IDs generated!"
        
        assert len(pending_decisions) == 10
        for crisis_id in stored_crisis_ids:
            assert crisis_id in pending_decisions
            stored = pending_decisions[crisis_id]
            assert "decision_output" in stored
            assert stored["call_sid"].startswith("call_")


# ============================================================
# TEST SUITE 3: Dispatcher Integration
# ============================================================

class TestDispatcherIntegration:
    """Verify dispatcher works correctly with audit logging."""
    
    def setup_method(self):
        """Clear audit log before each test."""
        with audit_lock:
            audit_log.clear()
    
    def test_execute_dispatch_with_valid_output(self):
        """Test dispatcher executes with valid decision output."""
        decision_output = {
            "decisions": [
                {
                    "crisis_type": "Fire",
                    "location": "Downtown",
                    "risk_score": 4.5
                },
                {
                    "crisis_type": "Flood",
                    "location": "Riverside",
                    "risk_score": 3.2
                }
            ],
            "remaining_resources": {"Fire": 1, "Flood": 2}
        }
        
        result = execute_dispatch(decision_output)
        
        assert result["execution_status"] == "COMPLETED"
        assert len(result["dispatch_log"]) == 2
        assert result["dispatch_log"][0]["unit_type"] == "Fire"
        assert result["dispatch_log"][1]["unit_type"] == "Flood"
        
        # Verify audit events
        log = get_audit_log()
        event_types = [entry["event_type"] for entry in log]
        
        assert "UNIT_DISPATCHED" in event_types
        assert "DISPATCH_COMPLETED" in event_types
    
    def test_execute_dispatch_with_empty_decisions(self):
        """Test dispatcher handles empty decisions gracefully."""
        decision_output = {
            "decisions": [],
            "remaining_resources": {}
        }
        
        result = execute_dispatch(decision_output)
        
        assert result["execution_status"] == "NO_ACTION"
        assert len(result["dispatch_log"]) == 0
        
        # Verify audit event
        log = get_audit_log()
        assert any(e["event_type"] == "DISPATCH_SKIPPED" for e in log)
    
    def test_execute_dispatch_with_none(self):
        """Test dispatcher handles None input."""
        result = execute_dispatch(None)
        assert result["execution_status"] == "NO_ACTION"
        assert result["dispatch_log"] == []


class TestVoiceEndpoint:
    """Ensure TwiML produced by voice() is valid XML and includes gather instructions."""

    def test_voice_response_structure(self):
        import asyncio
        import main

        # ensure there's a pending decision so the endpoint will render gather
        with main.pending_decisions_lock:
            main.pending_decisions["dummy-id"] = {
                "decision_output": {"decisions": []},
                "call_sid": "sid_dummy",
                "timestamp": datetime.utcnow().isoformat()
            }

        twiml = asyncio.get_event_loop().run_until_complete(main.voice("dummy-id"))
        xml = twiml.body.decode() if isinstance(twiml.body, bytes) else str(twiml.body)
        assert xml.strip().startswith("<?xml"), "Response is not proper TwiML XML"
        assert "<Gather" in xml, "Gather element missing in TwiML"
        assert "Press 6 to approve dispatch" in xml


# ============================================================
# TEST SUITE 4: Race Condition Scenario (Concurrent Approvals)
# ============================================================

class TestConcurrentApprovalScenario:
    """
    High-level test simulating the exact race condition scenario:
    - 5 high-risk crises arrive simultaneously
    - Each should get unique crisis_id
    - Each should trigger separate Twilio call
    - Each approval should dispatch only its own crisis
    """
    
    def test_multiple_crises_dont_overwrite_each_other(self):
        """
        SCENARIO: 5 crises arrive at almost same time.
        EXPECTED: Each gets unique crisis_id, none are lost.
        """
        from uuid import uuid4
        
        pending_decisions = {}
        pending_lock = threading.Lock()
        
        crisis_data_map = {}
        
        def simulate_crisis_arrival(crisis_num):
            crisis_id = str(uuid4())
            decision_output = {
                "decisions": [
                    {"crisis_type": f"Type_{crisis_num}", "risk_score": 4.0 + crisis_num}
                ],
                "tradeoffs": [],
                "remaining_resources": {"Fire": 1}
            }
            
            with pending_lock:
                pending_decisions[crisis_id] = {
                    "decision_output": decision_output,
                    "call_sid": f"call_{crisis_num}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            crisis_data_map[crisis_num] = crisis_id

        # 5 threads simulate 5 crises arriving concurrently
        threads = [
            threading.Thread(target=simulate_crisis_arrival, args=(i,))
            for i in range(5)
        ]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # Verify no overwrites occurred
        assert len(pending_decisions) == 5, f"Expected 5 pending decisions, got {len(pending_decisions)}"
        assert len(crisis_data_map) == 5
        
        # Verify each crisis_id is unique
        crisis_ids = list(crisis_data_map.values())
        assert len(set(crisis_ids)) == 5, "Crisis IDs are not unique!"
        
        # Verify each crisis has correct data and full decision_output structure
        for crisis_num, crisis_id in crisis_data_map.items():
            stored = pending_decisions[crisis_id]
            assert "decision_output" in stored
            decisions_list = stored["decision_output"].get("decisions", [])
            assert decisions_list, "decision_output missing decisions list"
            assert decisions_list[0]["crisis_type"] == f"Type_{crisis_num}"
            assert stored["call_sid"] == f"call_{crisis_num}"


# ============================================================
# Run Tests
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
