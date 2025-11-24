import streamlit as st
import requests
import time
from patterns import CircuitBreaker, Retry, Throttle, Timeout
from utils.http_client import make_request

# Page config
st.set_page_config(
    page_title="Stability Patterns Demo",
    page_icon="🛡️",
    layout="wide"
)

# Initialize session state
if 'patterns' not in st.session_state:
    st.session_state.patterns = {
        'circuit_breaker': None,
        'retry': None,
        'throttle': None,
        'timeout': None
    }

if 'stats' not in st.session_state:
    st.session_state.stats = {
        'circuit_breaker': {'success': 0, 'failed': 0, 'state': 'CLOSED'},
        'retry': {'attempts': 0, 'success': 0, 'failed': 0},
        'throttle': {'allowed': 0, 'rejected': 0},
        'timeout': {'success': 0, 'timeout': 0}
    }

BASE_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    .stAlert {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🛡️ Stability Patterns Demo")
st.markdown("---")

# Sidebar with controls
with st.sidebar:
    st.header("⚙️ Controls")

    if st.button("🔄 Reset All Stats", use_container_width=True):
        for pattern in st.session_state.stats:
            for key in st.session_state.stats[pattern]:
                if isinstance(st.session_state.stats[pattern][key], int):
                    st.session_state.stats[pattern][key] = 0
        st.session_state.patterns = {k: None for k in st.session_state.patterns}
        st.success("All stats reset!")
        st.rerun()

    st.markdown("---")

    st.header("🌐 Server Status")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=1)
        if response.status_code == 200:
            st.success("✅ Server is running")
        else:
            st.error("❌ Server error")
    except:
        st.error("❌ Server not running")
        st.code(f"python -m stability_templates.server.test_server")

# Main content - 2x2 grid
col1, col2 = st.columns(2)

# Circuit Breaker
with col1:
    st.header("⚡ Circuit Breaker")

    with st.expander("ℹ️ About Circuit Breaker", expanded=False):
        st.markdown("""
        Circuit Breaker захищає систему від каскадних збоїв:
        - **CLOSED**: Нормальна робота
        - **OPEN**: Блокує виклики після порогу помилок
        - **HALF_OPEN**: Перевіряє відновлення
        """)

    cb_stats = st.session_state.stats['circuit_breaker']

    # Metrics
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("State", cb_stats['state'])
    with col_b:
        st.metric("Success", cb_stats['success'])
    with col_c:
        st.metric("Failed", cb_stats['failed'])

    # Controls
    cb_endpoint = st.selectbox(
        "Endpoint",
        ["/random", "/failure", "/success"],
        key="cb_endpoint"
    )

    if st.button("🧪 Test Circuit Breaker", key="cb_test", use_container_width=True):
        if st.session_state.patterns['circuit_breaker'] is None:
            st.session_state.patterns['circuit_breaker'] = CircuitBreaker(
                func=make_request,
                exceptions=(Exception,),
                threshold=3,
                delay=5 # seconds
            )

        cb = st.session_state.patterns['circuit_breaker']

        with st.spinner("Testing..."):
            time.sleep(0.5) #to see current state

            try:
                result = cb.make_remote_call(f"{BASE_URL}{cb_endpoint}")
                st.session_state.stats['circuit_breaker']['success'] += 1

            except Exception as e:
                st.session_state.stats['circuit_breaker']['failed'] += 1

            st.session_state.stats['circuit_breaker']['state'] = cb.state
            time.sleep(0.5)

        st.rerun()

# Retry
with col2:
    st.header("🔄 Retry")

    with st.expander("ℹ️ About Retry", expanded=False):
        st.markdown("""
        Retry автоматично повторює виклики:
        - Експоненційний backoff
        - Налаштовувана кількість спроб
        - Обробка специфічних помилок
        """)

    retry_stats = st.session_state.stats['retry']

    # Metrics
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Attempts", retry_stats['attempts'])
    with col_b:
        st.metric("Success", retry_stats['success'])
    with col_c:
        st.metric("Failed", retry_stats['failed'])

    # Controls
    retry_endpoint = st.selectbox(
        "Endpoint",
        ["/unstable", "/random", "/failure"],
        key="retry_endpoint"
    )

    if st.button("🧪 Test Retry", key="retry_test", use_container_width=True):
        if st.session_state.patterns['retry'] is None:
            st.session_state.patterns['retry'] = Retry(
                func=make_request,
                max_attempts=3,
                delay=0.5,
                backoff=2
            )

        retry = st.session_state.patterns['retry']

        with st.spinner("Retrying..."):
            try:
                result = retry.call(f"{BASE_URL}{retry_endpoint}")
                st.session_state.stats['retry']['success'] += 1
                st.session_state.stats['retry']['attempts'] = retry.attempt_count

                st.markdown(f"""
                <div class="success-box">
                    <strong>✅ Success after {retry.attempt_count} attempts</strong><br>
                    Result: {result}
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.session_state.stats['retry']['failed'] += 1
                st.session_state.stats['retry']['attempts'] = retry.attempt_count

                st.markdown(f"""
                <div class="error-box">
                    <strong>❌ Failed after {retry.attempt_count} attempts</strong><br>
                    Error: {str(e)}
                </div>
                """, unsafe_allow_html=True)

        st.rerun()

# Second row
col3, col4 = st.columns(2)

# Throttle
with col3:
    st.header("⏱️ Throttle")

    with st.expander("ℹ️ About Throttle", expanded=False):
        st.markdown("""
        Throttle обмежує частоту викликів:
        - Максимум 3 виклики за 10 секунд
        - Захист від rate limiting
        - Автоматичне відновлення
        """)

    throttle_stats = st.session_state.stats['throttle']

    # Metrics
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Allowed", throttle_stats['allowed'])
    with col_b:
        st.metric("Rejected", throttle_stats['rejected'])

    if st.button("🧪 Test Throttle (3/10s)", key="throttle_test", use_container_width=True):
        if st.session_state.patterns['throttle'] is None:
            st.session_state.patterns['throttle'] = Throttle(
                func=lambda: make_request(f"{BASE_URL}/counter"),
                calls_per_period=3,
                period=10.0
            )

        throttle = st.session_state.patterns['throttle']

        try:
            result = throttle.call()
            st.session_state.stats['throttle']['allowed'] += 1
            remaining = throttle.get_remaining_calls()

            st.markdown(f"""
            <div class="success-box">
                <strong>✅ Call allowed</strong><br>
                Remaining calls: {remaining}/3<br>
                Result: {result}
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.session_state.stats['throttle']['rejected'] += 1
            remaining = throttle.get_remaining_calls()

            st.markdown(f"""
            <div class="error-box">
                <strong>⏳ Throttled</strong><br>
                Remaining calls: {remaining}/3<br>
                Error: {str(e)}
            </div>
            """, unsafe_allow_html=True)

        st.rerun()

# Timeout
with col4:
    st.header("⏰ Timeout")

    with st.expander("ℹ️ About Timeout", expanded=False):
        st.markdown("""
        Timeout обмежує час виконання:
        - Переривається за 2 секунди
        - Працює через threading + join(timeout)
        - ⚠️ Не переривається HTTP request, але обмежує загальний час
        """)

    timeout_stats = st.session_state.stats['timeout']

    # Metrics
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Success", timeout_stats['success'])
    with col_b:
        st.metric("Timeout", timeout_stats['timeout'])

    # Controls
    delay = st.slider("Server delay (seconds)", 1, 5, 3, key="timeout_delay")
    st.info(f"⏱️ Pattern timeout: 2s | Server delay: {delay}s")

    if st.button("🧪 Test Timeout", key="timeout_test", use_container_width=True):
        # HTTP timeout більший, щоб Pattern Timeout спрацював першим
        timeout = Timeout(
            func=lambda: make_request(f"{BASE_URL}/slow?delay={delay}", timeout=10.0),
            timeout_seconds=2
        )

        with st.spinner(f"Testing with {delay}s delay (2s limit)..."):
            start = time.time()
            try:
                result = timeout.call()
                elapsed = time.time() - start
                st.session_state.stats['timeout']['success'] += 1

                st.markdown(f"""
                <div class="success-box">
                    <strong>✅ Completed within timeout</strong><br>
                    Actual time: {elapsed:.2f}s < 2s<br>
                    Server delay: {delay}s<br>
                    Result: {result}
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                elapsed = time.time() - start
                st.session_state.stats['timeout']['timeout'] += 1

                st.markdown(f"""
                <div class="error-box">
                    <strong>⏰ Timeout!</strong><br>
                    Stopped at: {elapsed:.2f}s ≈ 2s<br>
                    Server delay: {delay}s > 2s<br>
                    Error: {type(e).__name__}
                </div>
                """, unsafe_allow_html=True)

        st.rerun()

# Debounce
st.markdown("---")
st.header("⏳ Debounce")

with st.expander("ℹ️ About Debounce", expanded=False):
    st.markdown("""
    Debounce відкладає виконання:
    - Чекає 1 секунду після останнього виклику
    - Скасовує попередні виклики
    - Ідеально для пошуку/автозбереження

    **⚠️ Обмеження**: Streamlit не підтримує real-time events.
    Ця демонстрація показує концепцію через симуляцію.
    """)

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Manual Test")

    # Ініціалізація в основному потоці
    if 'debounce_calls' not in st.session_state:
        st.session_state.debounce_calls = 0
        st.session_state.debounce_result = None

    search_query = st.text_input("Search query", key="search")

    if st.button("🔍 Trigger Debounce (simulated)", key="debounce_btn"):
        from patterns import Debounce

        # Лічильник викликів для демонстрації
        call_counter = {'count': 0}

        def search_function(query):
            # Використовуємо локальний лічильник замість session_state
            call_counter['count'] += 1
            return f"Search result for: '{query}'"

        debounce = Debounce(func=search_function, wait_time=1.0)

        # Симуляція 5 швидких викликів
        with st.spinner("Simulating 5 rapid calls..."):
            for i in range(5):
                debounce.call(search_query)
                st.session_state.debounce_calls += 1

            time.sleep(1.1)  # Чекаємо debounce
            result = debounce.flush()

        # Показуємо результат
        if result:
            st.success(f"✅ {result}")
            st.info(f"📊 5 calls → 1 execution (saved 4 calls)")
        else:
            st.warning("⚠️ No result (function executed in thread)")

    # Metrics
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Total calls", st.session_state.debounce_calls)
    with col_m2:
        st.metric("Saved calls", max(0, st.session_state.debounce_calls - st.session_state.debounce_calls // 5))

with col_b:
    st.subheader("Conceptual Demo")

    st.code("""
# Without Debounce (every keystroke)
def on_input(query):
    api_call(query)  # Called 5 times!

# User types: "h", "he", "hel", "hell", "hello"
# Result: 5 API calls

# With Debounce (1s delay)
@debounce(wait_time=1.0)
def on_input(query):
    api_call(query)  # Called once!

# User types: "hello" (waits 1s)
# Result: 1 API call (saved 4 calls)
    """, language="python")

    st.warning("💡 For real-time debounce, use JavaScript frontend or CLI app")

    # Додатковий приклад
    st.markdown("### Real-world Example")
    st.code("""
from patterns import Debounce

# Search with debounce
search = Debounce(api_search, wait_time=0.5)

# User types fast: "python"
search.call("p")     # Cancelled
search.call("py")    # Cancelled
search.call("pyt")   # Cancelled
search.call("pyth")  # Cancelled
search.call("python") # Executed after 0.5s

# Result: 1 API call instead of 5
    """, language="python")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6c757d;'>
    <p>Built with Streamlit | Stability Patterns Demo 2025</p>
</div>
""", unsafe_allow_html=True)
