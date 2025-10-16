import time
from circuit_breaker import CircuitBreaker
from snippets import make_request, faulty_endpoint, success_endpoint, random_status_endpoint

def test_closed_to_open():
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
        except Exception as e:
            print(f"Attempt {i + 1}: {e}")
            print(f"Current state: {cb_faulty.state}")
            print(f"Failed attempts: {cb_faulty._failed_attempt_count}")


def test_open_state():
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
    cb_faulty.set_state("open")
    cb_faulty.update_last_attempt_timestamp()

    # Try calling while in OPEN state
    for i in range(3):
        try:
            cb_faulty.make_remote_call(faulty_endpoint)
        except Exception as e:
            print(f"OPEN state call {i + 1}: {e}")


def test_recovery():
    """Test OPEN → HALF_OPEN → CLOSED recovery"""
    print("\nTesting recovery (OPEN → HALF_OPEN → CLOSED)...")

    cb_success = CircuitBreaker(
        func=make_request,
        exceptions=(Exception,),
        threshold=3,
        delay=3
    )

    # Set to OPEN state and wait
    cb_success.set_state("open")
    cb_success.update_last_attempt_timestamp()

    print(f"Waiting {cb_success.delay + 1} seconds for delay period...")
    time.sleep(cb_success.delay + 1)

    # Make successful call to recover
    try:
        result = cb_success.make_remote_call(success_endpoint)
        print(f"Recovery successful! State: {cb_success.state}")
    except Exception as e:
        print(f"Recovery failed: {e}")


def test_random_behavior():
    """Test with random endpoint"""
    print("\nTesting with random endpoint...")

    cb_random = CircuitBreaker(
        func=make_request,
        exceptions=(Exception,),
        threshold=2,
        delay=3
    )

    for i in range(10):
        try:
            result = cb_random.make_remote_call(random_status_endpoint)
            print(f"Call {i + 1}: SUCCESS - State: {cb_random.state}")
        except Exception as e:
            print(f"Call {i + 1}: FAILED - State: {cb_random.state}")

        time.sleep(0.5)


def run_all_tests():
    """Run all circuit breaker tests"""
    print("Starting Circuit Breaker Tests\n")
    print("Make sure Flask app is running: python main.py\n")

    test_closed_to_open()
    test_open_state()
    test_recovery()
    test_random_behavior()


if __name__ == "__main__":
    run_all_tests()
