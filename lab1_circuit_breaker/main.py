import random
import time
from flask import Flask

app = Flask(__name__)


@app.route('/success')
def success_endpoint():
    return {
        "msg": "Call to this endpoint was a success."
    }, 200


@app.route('/failure')
def faulty_endpoint():
    r = random.randint(0, 1)
    if r == 0:
        time.sleep(2)

    return {
        "msg": "I will fail."
    }, 500


@app.route('/random')
def fail_randomly_endpoint():
    r = random.randint(0, 1)
    if r == 0:
        return {
            "msg": "Success msg"
        }, 200

    return {
        "msg": "I will fail (sometimes)."
    }, 500


if __name__ == '__main__':
    PORT = 8000  # Change this to your desired port

    print("=" * 50)
    print("Flask Circuit Breaker Test Server")
    print("=" * 50)
    print(f"Server running at: http://localhost:{PORT}")
    print("\nAvailable endpoints:")
    print(f"  • Success: http://localhost:{PORT}/success")
    print(f"  • Failure: http://localhost:{PORT}/failure")
    print(f"  • Random:  http://localhost:{PORT}/random")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=PORT)
