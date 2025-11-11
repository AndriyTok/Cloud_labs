import time
import pytest
from unittest import mock
from stability_templates.patterns.circuit_breaker import (
    CircuitBreaker,
    RemoteCallFailedException,
    StateChoices
)
from stability_templates.utils.http_client import make_request


@pytest.fixture
def faulty_endpoint(server_url):
    """URL для endpoint що завжди падає"""
    return f"{server_url}/failure"


@pytest.fixture
def success_endpoint(server_url):
    """URL для endpoint що завжди успішний"""
    return f"{server_url}/success"


@pytest.fixture
def random_endpoint(server_url):
    """URL для endpoint з випадковою поведінкою"""
    return f"{server_url}/random"


def test_closed_to_open(mock_service, faulty_endpoint):
    """Test CLOSED → OPEN state transition"""
    print("Testing CLOSED to OPEN transition...")

    cb_faulty = CircuitBreaker(
        func=make_request,
        exceptions=(Exception,),
        threshold=3,
        delay=5
    )

    # Make failed calls to trigger OPEN state
    for i in range(4):
        try:
            cb_faulty.make_remote_call(faulty_endpoint)
        except RemoteCallFailedException as e:
            print(f"Attempt {i + 1}: {e}")
            print(f"Current state: {cb_faulty.state}")
            print(f"Failed attempts: {cb_faulty._failed_attempt_count}")

    # Verify state changed to OPEN after threshold failures
    assert cb_faulty.state == StateChoices.OPEN


def test_open_state(mock_service, faulty_endpoint):
    """Test OPEN state behavior"""
    print("\nTesting OPEN state behavior...")

    cb_faulty = CircuitBreaker(
        func=make_request,
        exceptions=(Exception,),
        threshold=3,
        delay=5
    )

    # Force to OPEN state first
    cb_faulty._failed_attempt_count = 3
    cb_faulty.set_state(StateChoices.OPEN)
    cb_faulty.update_last_attempt_timestamp()

    # Try calling while in OPEN state
    for i in range(3):
        try:
            cb_faulty.make_remote_call(faulty_endpoint)
        except RemoteCallFailedException as e:
            print(f"OPEN state call {i + 1}: {e}")

    # Verify still in OPEN state
    assert cb_faulty.state == StateChoices.OPEN


def test_recovery(mock_service, success_endpoint):
    """Test OPEN → HALF_OPEN → CLOSED recovery"""
    print("\nTesting recovery (OPEN → HALF_OPEN → CLOSED)...")

    cb_success = CircuitBreaker(
        func=make_request,
        exceptions=(Exception,),
        threshold=3,
        delay=3
    )

    # Set to OPEN state and wait
    cb_success.set_state(StateChoices.OPEN)
    cb_success.update_last_attempt_timestamp()

    print(f"Waiting {cb_success.delay + 1} seconds for delay period...")
    time.sleep(cb_success.delay + 1)

    # Make successful call to recover
    result = cb_success.make_remote_call(success_endpoint)
    print(f"Recovery successful! State: {cb_success.state}")

    # Verify state changed to CLOSED after successful call
    assert cb_success.state == StateChoices.CLOSED
    assert result is not None


def test_random_behavior(mock_service, random_endpoint):
    """Test with random endpoint"""
    print("\nTesting with random endpoint...")

    cb_random = CircuitBreaker(
        func=make_request,
        exceptions=(Exception,),
        threshold=2,
        delay=3
    )

    success_count = 0
    fail_count = 0

    for i in range(10):
        try:
            result = cb_random.make_remote_call(random_endpoint)
            print(f"Call {i + 1}: SUCCESS - State: {cb_random.state}")
            success_count += 1
        except RemoteCallFailedException:
            print(f"Call {i + 1}: FAILED - State: {cb_random.state}")
            fail_count += 1

        time.sleep(0.5)

    print(f"\nResults: {success_count} successes, {fail_count} failures")


def test_with_mock():
    """Test with controlled mock function"""
    print("\nTesting with mock function...")

    mock_fn = mock.Mock()
    mock_fn.side_effect = [
        Exception("Failed"),
        Exception("Failed"),
        Exception("Failed"),
        "success",
        "success"
    ]

    cb = CircuitBreaker(
        func=mock_fn,
        exceptions=(Exception,),
        threshold=3,
        delay=1
    )

    # First 3 calls - should fail and open circuit
    for i in range(3):
        try:
            cb.make_remote_call()
        except RemoteCallFailedException:
            print(f"Call {i + 1}: Failed as expected")

    assert cb.state == StateChoices.OPEN

    # Wait for timeout
    time.sleep(cb.delay + 0.1)

    # Next call should succeed and close circuit
    result = cb.make_remote_call()
    print(f"Call 4: Succeeded, result: {result}")
    assert cb.state == StateChoices.CLOSED
    assert result == "success"
