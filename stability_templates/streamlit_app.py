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
                delay=5
            )

        cb = st.session_state.patterns['circuit_breaker']

        with st.spinner("Testing..."):
            try:
                result = cb.make_remote_call(f"{BASE_URL}{cb_endpoint}")
                st.session_state.stats['circuit_breaker']['success'] += 1
                st.session_state.stats['circuit_breaker']['state'] = cb.state

                st.markdown(f"""
                <div class="success-box">
                    <strong>✅ Success!</strong><br>
                    State: {cb.state}<br>
                    Failed count: {cb._failed_attempt_count}<br>
                    Result: {result}
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.session_state.stats['circuit_breaker']['failed'] += 1
                st.session_state.stats['circuit_breaker']['state'] = cb.state

                st.markdown(f"""
                <div class="error-box">
                    <strong>❌ Failed</strong><br>
                    State: {cb.state}<br>
                    Failed count: {cb._failed_attempt_count}<br>
                    Error: {str(e)}
                </div>
                """, unsafe_allow_html=True)

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
        - Максимум 2 секунди на виклик
        - Запобігає зависанням
        - Швидке повідомлення про помилку
        """)

    timeout_stats = st.session_state.stats['timeout']

    # Metrics
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Success", timeout_stats['success'])
    with col_b:
        st.metric("Timeout", timeout_stats['timeout'])

    # Controls
    delay = st.slider("Server delay (seconds)", 1, 10, 3, key="timeout_delay")
    st.info(f"Timeout limit: 2 seconds")

    if st.button("🧪 Test Timeout", key="timeout_test", use_container_width=True):
        timeout = Timeout(
            func=lambda: make_request(f"{BASE_URL}/slow?delay={delay}", timeout=10.0),
            timeout_seconds=2
        )

        with st.spinner(f"Waiting {delay}s..."):
            try:
                result = timeout.call()
                st.session_state.stats['timeout']['success'] += 1

                st.markdown(f"""
                <div class="success-box">
                    <strong>✅ Completed within timeout</strong><br>
                    Delay: {delay}s<br>
                    Result: {result}
                </div>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.session_state.stats['timeout']['timeout'] += 1

                st.markdown(f"""
                <div class="error-box">
                    <strong>⏰ Timeout exceeded</strong><br>
                    Delay: {delay}s > 2s limit<br>
                    Error: {str(e)}
                </div>
                """, unsafe_allow_html=True)

        st.rerun()

# Debounce
with st.container():
    st.header("⏳ Debounce")

    with st.expander("ℹ️ About Debounce", expanded=False):
        st.markdown("""
        Debounce відкладає виконання до закінчення періоду без нових викликів:
        - Згладжування потоку подій
        - Оптимізація частих викликів
        """)

    # Симуляція з лічильником
    if 'debounce_counter' not in st.session_state:
        st.session_state.debounce_counter = 0

    search_query = st.text_input("Search (simulated debounce)", key="search")

    if st.button("🔍 Search with Debounce"):
        from patterns import Debounce

        def search_function(query):
            st.session_state.debounce_counter += 1
            return f"Search result for: {query}"

        debounce = Debounce(func=search_function, wait_time=1.0)

        # Симуляція кількох швидких викликів
        for i in range(5):
            debounce.call(search_query)

        time.sleep(1.1)  # Чекаємо завершення
        result = debounce.flush()

        st.success(f"Result: {result}")
        st.info(f"Function called only once despite 5 attempts")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6c757d;'>
    <p>Built with Streamlit | Stability Patterns Demo 2025</p>
</div>
""", unsafe_allow_html=True)