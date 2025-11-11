from patterns import CircuitBreaker, Retry, Throttle, Debounce, Timeout
from utils.http_client import make_request

# Example usage of all patterns
if __name__ == "__main__":
    base_url = "http://localhost:8000"

    # Circuit Breaker example
    print("\n=== Circuit Breaker ===")
    cb = CircuitBreaker(
        func=make_request,
        exceptions=(Exception,),
        threshold=3,
        delay=5
    )

    try:
        result = cb.make_remote_call(f"{base_url}/random")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")

    # Retry example
    print("\n=== Retry ===")
    retry = Retry(
        func=make_request,
        max_attempts=3,
        delay=1,
        backoff=2
    )

    try:
        result = retry.call(f"{base_url}/unstable")
        print(f"Result: {result}")
    except Exception as e:
        print(f"All retries failed: {e}")
