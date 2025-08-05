import streamlit as st
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

# Stock data fetching function
@st.cache_data
def get_stock_data(symbol, days):
    """Fetch stock data with caching"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        data = yf.download(symbol, start=start_date, end=end_date, progress=False)
        return data
    except Exception as e:
        st.error(f"Failed to fetch data for {symbol}: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

@st.cache_data
def get_multiple_stocks_data(symbols, days):
    """Fetch data for multiple stocks"""
    stock_data = {}
    for symbol in symbols:
        try:
            data = get_stock_data(symbol, days)
            if isinstance(data, pd.DataFrame) and not data.empty:
                stock_data[symbol] = data
        except Exception as e:
            continue
    return stock_data


def login_page(
    go_to, verify_user, is_account_locked, handle_failed_login, update_last_login
):
    """Render the login page with enhanced security"""
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login", type="primary", use_container_width=True):
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                # Check if account is locked
                locked, unlock_time = is_account_locked(username)
                if locked:
                    st.error(
                        f"Account locked due to failed login attempts. Try again after {unlock_time.strftime('%H:%M:%S')}"
                    )
                elif verify_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    update_last_login(username)
                    st.success("Login successful!")
                    go_to("dashboard")
                else:
                    handle_failed_login(username)
                    st.error("Invalid credentials")

    # Password strength indicator
    if password:
        strength = calculate_password_strength(password)
        st.progress(strength / 100)
        if strength < 50:
            st.caption("🔴 Weak password")
        elif strength < 80:
            st.caption("🟡 Medium password")
        else:
            st.caption("🟢 Strong password")

    st.divider()

    st.write("Don't have an account?")
    if st.button("Register here", use_container_width=True):
        go_to("register")


def register_page(go_to, register_user):
    """Render the registration page with enhanced validation"""
    st.title("📝 Register")

    username = st.text_input("Choose a username", help="Must be at least 3 characters")
    email = st.text_input("Email", help="We'll never share your email")
    password = st.text_input(
        "Choose a password",
        type="password",
        help="Must be at least 8 characters with uppercase, lowercase, number and special character",
    )
    confirm_password = st.text_input("Confirm password", type="password")

    # Real-time password strength indicator
    if password:
        strength = calculate_password_strength(password)
        progress_bar = st.progress(strength / 100)
        if strength < 30:
            st.caption("🔴 Very weak password")
        elif strength < 50:
            st.caption("🟡 Weak password")
        elif strength < 70:
            st.caption("🟠 Medium password")
        elif strength < 90:
            st.caption("🟢 Strong password")
        else:
            st.caption("💪 Very strong password")

    # Password match indicator
    if password and confirm_password:
        if password == confirm_password:
            st.success("✅ Passwords match")
        else:
            st.error("❌ Passwords don't match")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Register", type="primary", use_container_width=True):
            success, message = register_user(username, password, email)
            if success:
                st.success(message)
                st.balloons()  # Celebration animation
                go_to("login")
            else:
                st.error(message)

    with col2:
        if st.button("Back to login", use_container_width=True):
            go_to("login")


def profile_page(go_to, get_user_info, change_password):
    """Render the profile page with user information and settings"""
    st.title("👤 Profile")

    # Get user info
    user_info = get_user_info(st.session_state.username)

    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Dashboard"):
            go_to("dashboard")
    with col2:
        if st.button("🚪 Logout"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Logged out successfully!")
            st.rerun()

    st.divider()

    # Profile tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["👤 Profile Information", "⚙️ Settings", "🔐 Security", "📊 Activity", "🔧 Session"])

    with tab1:
        st.subheader("Profile Information")
        if user_info:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Username:** {user_info['username']}")
                st.write(f"**Email:** {user_info['email']}")
                st.write(f"**Role:** {user_info.get('role', 'user').title()}")
            with col2:
                if user_info.get("created_at"):
                    st.write(
                        f"**Member since:** {user_info['created_at'].strftime('%B %d, %Y')}"
                    )
                st.write(
                    f"**Account Status:** {'Active' if user_info.get('is_active') else 'Inactive'}"
                )

        # Profile update form
        with st.expander("Update Email"):
            new_email = st.text_input(
                "New Email", value=user_info.get("email", "") if user_info else ""
            )
            if st.button("Update Email"):
                st.info("Email update functionality coming soon...")

    with tab2:
        st.subheader("Application Settings")

        # Theme selection
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])

        # Notification preferences
        st.subheader("Notifications")
        email_notifications = st.checkbox("Email notifications", value=True)
        push_notifications = st.checkbox("Push notifications", value=False)

        if st.button("Save Settings"):
            st.success("Settings saved successfully!")

    with tab3:
        st.subheader("Security Settings")

        # Password change
        st.write("**Change Password**")
        with st.form("change_password"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_new_password = st.text_input(
                "Confirm New Password", type="password"
            )

            if st.form_submit_button("Change Password"):
                if new_password != confirm_new_password:
                    st.error("New passwords don't match")
                else:
                    success, message = change_password(
                        st.session_state.username, current_password, new_password
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

        st.divider()

        # Security info
        st.write("**Security Status**")
        st.write("✅ Password protected")
        st.write("✅ Email verified")
        st.write("⚠️ Two-factor authentication: Not enabled (Coming soon)")

    with tab4:
        st.subheader("Recent Activity")

        # Mock activity data - in real app, fetch from database
        activity_data = [
            {"action": "Login", "timestamp": datetime.now(), "ip": "192.168.1.1"},
            {
                "action": "Password Changed",
                "timestamp": datetime.now(),
                "ip": "192.168.1.1",
            },
            {
                "action": "Profile Updated",
                "timestamp": datetime.now(),
                "ip": "192.168.1.1",
            },
        ]

        for activity in activity_data:
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"🔹 {activity['action']}")
                with col2:
                    st.write(activity["timestamp"].strftime("%Y-%m-%d %H:%M"))
                with col3:
                    st.write(activity["ip"])

    with tab5:
        st.subheader("Session Management")
        
        # Session info
        st.write("**Current Session**")
        st.write(f"Username: {st.session_state.username}")
        st.write(f"Page: {st.session_state.get('page', 'dashboard')}")
        
        st.divider()
        
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔄 Refresh Session", type="secondary", use_container_width=True):
                st.success("Session refreshed!")
                st.rerun()

        with col2:
            if st.button("🚪 Logout", type="primary", use_container_width=True):
                # Clear all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.success("Logged out successfully!")
                st.rerun()


def dashboard_page(go_to, get_user_info, change_password):
    """Render the dashboard page with enhanced features"""
    
    # Top navigation bar with profile button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 Dashboard")
    with col2:
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        if st.button("👤 Profile & Settings", type="secondary", use_container_width=True):
            go_to("profile")

    # Get user info
    user_info = get_user_info(st.session_state.username)

    # Welcome message with user info
    st.markdown(f"### Welcome back, **{st.session_state.username}**! 👋")

    if user_info and user_info.get("last_login"):
        last_login = user_info["last_login"]
        if isinstance(last_login, datetime):
            st.caption(f"Last login: {last_login.strftime('%Y-%m-%d %H:%M:%S')} UTC")

    # Dashboard metrics
    if user_info:
        days_since = (
            datetime.utcnow() - user_info.get("created_at", datetime.utcnow())
        ).days
        st.metric("Member for", f"{days_since} days")

    st.divider()

    # Stock Market Summary Section
    st.subheader("📈 Stock Market Dashboard")
    
    # Time range selector
    days = st.slider("Select time range", min_value=7, max_value=90, value=30, help="Number of past days")
    
    # Stock symbols
    stock_symbols = ["AAPL", "GOOGL", "AMZN", "MSFT", "TSLA", "META"]
    
    # Fetch data for all stocks
    with st.spinner("Loading stock data..."):
        all_stock_data = get_multiple_stocks_data(stock_symbols, days)
    
    if all_stock_data:
        # Create stock cards in a grid
        cols = st.columns(3)  # 3 columns for the grid
        
        for idx, (symbol, data) in enumerate(all_stock_data.items()):
            with cols[idx % 3]:  # Distribute across 3 columns
                try:
                    if isinstance(data, pd.DataFrame) and not data.empty:
                        latest = data.iloc[-1]
                        previous = data.iloc[-2] if len(data) > 1 else latest
                        
                        # Calculate change
                        change = float(latest["Close"]) - float(previous["Close"])
                        change_pct = (change / float(previous["Close"])) * 100 if float(previous["Close"]) != 0 else 0
                        
                        # Create stock card
                        with st.container():
                            st.markdown(f"**{symbol}**")
                            
                            # Price and change
                            col_price, col_change = st.columns([1, 1])
                            with col_price:
                                st.metric("Price", f"${float(latest['Close']):.2f}")
                            with col_change:
                                change_color = "🟢" if change >= 0 else "🔴"
                                st.metric("Change", f"{change_pct:+.2f}%", delta=f"{change:+.2f}")
                            
                            # Mini chart
                            if 'Close' in data.columns and len(data) > 1:
                                chart_data = data['Close'].tail(min(30, len(data)))
                                st.line_chart(chart_data, height=150)
                            
                            st.markdown("---")
                            
                except Exception as e:
                    with st.container():
                        st.error(f"Error loading {symbol}: {str(e)}")
                        st.markdown("---")
        
        # Detailed view expander
        with st.expander("📊 Detailed Stock Analysis", expanded=False):
            selected_stock = st.selectbox("Select stock for detailed view", list(all_stock_data.keys()))
            
            if selected_stock in all_stock_data:
                detailed_data = all_stock_data[selected_stock]
                
                # Detailed metrics
                latest = detailed_data.iloc[-1]
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Current Price", f"${float(latest['Close']):.2f}")
                with col2:
                    st.metric("High", f"${float(detailed_data['High'].max()):.2f}")
                with col3:
                    st.metric("Low", f"${float(detailed_data['Low'].min()):.2f}")
                with col4:
                    try:
                        volume = int(float(latest['Volume']))
                        st.metric("Volume", f"{volume:,}")
                    except:
                        st.metric("Volume", "N/A")
                
                # Full chart
                st.subheader(f"{selected_stock} - {days} Day Chart")
                st.line_chart(detailed_data['Close'])
                
                # Recent data
                st.subheader("Recent Data")
                st.dataframe(detailed_data.tail(10), use_container_width=True)
    else:
        st.warning("Unable to load stock data. Please check your internet connection.")




def calculate_password_strength(password):
    """Calculate password strength score (0-100)"""
    if not password:
        return 0

    score = 0

    # Length scoring
    if len(password) >= 8:
        score += 25
    elif len(password) >= 6:
        score += 15
    elif len(password) >= 4:
        score += 10

    # Character variety scoring
    if any(c.isupper() for c in password):
        score += 20
    if any(c.islower() for c in password):
        score += 20
    if any(c.isdigit() for c in password):
        score += 20
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        score += 15

    return min(score, 100)
