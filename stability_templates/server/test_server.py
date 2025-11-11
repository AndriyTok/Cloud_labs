import random
import time
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/success')
def success_endpoint():
    return jsonify({"msg": "Success", "timestamp": time.time()}), 200


@app.route('/failure')
def failure_endpoint():
    if random.random() < 0.5:
        time.sleep(2)
    return jsonify({"msg": "Failure"}), 500


@app.route('/random')
def random_endpoint():
    if random.random() < 0.5:
        return jsonify({"msg": "Success"}), 200
    return jsonify({"msg": "Failure"}), 500


@app.route('/slow')
def slow_endpoint():
    delay = float(request.args.get('delay', 3))
    time.sleep(delay)
    return jsonify({"msg": f"Delayed {delay}s"}), 200


@app.route('/unstable')
def unstable_endpoint():
    """70% failure rate for retry testing"""
    if random.random() < 0.7:
        return jsonify({"msg": "Failed"}), 500
    return jsonify({"msg": "Success"}), 200


@app.route('/counter')
def counter_endpoint():
    """Incremental counter for debounce/throttle testing"""
    if not hasattr(counter_endpoint, 'count'):
        counter_endpoint.count = 0
    counter_endpoint.count += 1
    return jsonify({"count": counter_endpoint.count, "timestamp": time.time()}), 200


@app.route('/health')
def health_endpoint():
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    PORT = 8000
    print("=" * 60)
    print("Stability Patterns Test Server")
    print("=" * 60)
    print(f"Server: http://localhost:{PORT}")
    print("\nEndpoints:")
    print(f"  /success  - Always succeeds")
    print(f"  /failure  - Always fails (sometimes with delay)")
    print(f"  /random   - Random success/failure")
    print(f"  /slow     - Delayed response (use ?delay=N)")
    print(f"  /unstable - 70% failure rate")
    print(f"  /counter  - Incremental counter")
    print(f"  /health   - Health check")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=PORT)