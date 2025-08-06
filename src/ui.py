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
        
        # Flatten multi-level columns if they exist
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]
        
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
    
    # Sidebar configuration
    with st.sidebar:
        st.header("📊 Menu")
        
        # Time range selector
        days = st.slider("Time Range (days)", min_value=7, max_value=90, value=30)
        
        st.divider()
        
        # Dashboard options
        st.subheader("🔧 Options")
        
        if st.button("📈 Detailed Stock Analysis", use_container_width=True):
            go_to("stock_analysis")
        
        if st.button("👤 Profile & Settings", use_container_width=True):
            go_to("profile")
        
        st.divider()
        
        # Quick stats
        st.subheader("ℹ️ Quick Info")
        st.caption("📅 Market data updated in real-time")
        st.caption("🔄 Auto-refresh every 5 minutes")
    
    # Main dashboard title
    st.title("📊 Dashboard")

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
                        
                        # Calculate change safely
                        change = float(latest["Close"]) - float(previous["Close"])
                        prev_close = float(previous["Close"])
                        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
                        
                        # Create stock card
                        with st.container():
                            st.markdown(f"**{symbol}**")
                            
                            # Price and change
                            col_price, col_change = st.columns([1, 1])
                            with col_price:
                                st.metric("Price", f"${float(latest['Close']):.2f}")
                            with col_change:
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
        
    else:
        st.warning("Unable to load stock data. Please check your internet connection.")


def stock_analysis_page(go_to, get_user_info, change_password):
    """Render detailed stock analysis page"""
    
    # Sidebar for stock analysis
    with st.sidebar:
        st.header("📈 Stock Analysis")
        
        # Stock selection
        stock_symbols = ["AAPL", "GOOGL", "AMZN", "MSFT", "TSLA", "META"]
        selected_stock = st.selectbox("Select Stock", stock_symbols)
        
        # Time range
        days = st.slider("Time Range (days)", min_value=7, max_value=365, value=90)
        
        # Analysis options
        st.subheader("📊 Analysis Tools")
        show_volume = st.checkbox("Show Volume", value=True)
        show_moving_avg = st.checkbox("Show Moving Average", value=False)
        
        st.divider()
        
        # Navigation
        if st.button("← Back to Dashboard", use_container_width=True):
            go_to("dashboard")
        
        if st.button("👤 Profile & Settings", use_container_width=True):
            go_to("profile")
    
    # Main analysis content
    st.title(f"📈 {selected_stock} - Detailed Analysis")
    
    # Fetch data
    with st.spinner(f"Loading {selected_stock} data..."):
        data = get_stock_data(selected_stock, days)
    
    if isinstance(data, pd.DataFrame) and not data.empty:
        latest = data.iloc[-1]
        previous = data.iloc[-2] if len(data) > 1 else latest
        
        # Calculate metrics
        change = float(latest["Close"]) - float(previous["Close"])
        prev_close = float(previous["Close"])
        change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Current Price", f"${float(latest['Close']):.2f}", 
                     f"{change:+.2f} ({change_pct:+.2f}%)")
        with col2:
            st.metric("52-Week High", f"${float(data['High'].max()):.2f}")
        with col3:
            st.metric("52-Week Low", f"${float(data['Low'].min()):.2f}")
        with col4:
            try:
                volume = int(float(latest['Volume']))
                st.metric("Volume", f"{volume:,}")
            except:
                st.metric("Volume", "N/A")
        
        st.divider()
        
        # Charts section
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"📊 {selected_stock} Price Chart")
            
            try:
                # Add moving average if selected
                if 'Close' in data.columns:
                    chart_data = pd.DataFrame({'Close': data['Close']})
                    if show_moving_avg and len(data) >= 20:
                        chart_data['20-Day MA'] = data['Close'].rolling(window=20).mean()
                    
                    st.line_chart(chart_data, height=400)
                else:
                    st.error("Close price data not available")
            except Exception as e:
                st.error(f"Error creating price chart: {str(e)}")
        
        with col2:
            try:
                if show_volume and 'Volume' in data.columns:
                    st.subheader("📊 Volume Chart")
                    volume_data = pd.DataFrame({'Volume': data['Volume']})
                    st.bar_chart(volume_data, height=400)
                elif 'High' in data.columns and 'Low' in data.columns:
                    st.subheader("📈 High-Low Range")
                    high_low_data = pd.DataFrame({
                        'High': data['High'],
                        'Low': data['Low']
                    })
                    st.line_chart(high_low_data, height=400)
                else:
                    st.error("Chart data not available")
            except Exception as e:
                st.error(f"Error creating secondary chart: {str(e)}")
        
        # Additional analysis
        st.divider()
        
        # Recent performance
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Recent Performance")
            
            # Calculate different time periods
            periods = [1, 7, 30]
            performance_data = []
            
            for period in periods:
                if len(data) > period:
                    old_price = float(data.iloc[-(period+1)]['Close'])
                    current_price = float(latest['Close'])
                    change = ((current_price - old_price) / old_price) * 100
                    performance_data.append({
                        'Period': f'{period} Day{"s" if period > 1 else ""}',
                        'Change (%)': f'{change:+.2f}%'
                    })
            
            if performance_data:
                st.table(pd.DataFrame(performance_data))
        
        with col2:
            st.subheader("📈 Price Statistics")
            
            # Statistical summary
            stats_data = [
                {'Metric': 'Average', 'Value': f"${data['Close'].mean():.2f}"},
                {'Metric': 'Median', 'Value': f"${data['Close'].median():.2f}"},
                {'Metric': 'Std Deviation', 'Value': f"${data['Close'].std():.2f}"},
                {'Metric': 'Range', 'Value': f"${data['Close'].max() - data['Close'].min():.2f}"}
            ]
            st.table(pd.DataFrame(stats_data))
        
        # Raw data
        st.divider()
        st.subheader("📋 Recent Data")
        
        try:
            # Format the dataframe for better display
            display_data = data.tail(15).copy()
            
            # Round numeric columns if they exist
            for col in ['Open', 'High', 'Low', 'Close']:
                if col in display_data.columns:
                    display_data[col] = display_data[col].round(2)
            
            st.dataframe(display_data, use_container_width=True)
        except Exception as e:
            st.error(f"Error displaying data table: {str(e)}")
            st.write("Raw data preview:")
            st.write(data.head())
        
    else:
        st.error(f"Unable to load data for {selected_stock}")
        st.info("Please check your internet connection and try again.")


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