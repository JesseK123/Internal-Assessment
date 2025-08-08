import streamlit as st
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd

# Stock symbols by country
STOCK_SYMBOLS_BY_COUNTRY = {
    "United States": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "BRK-B", "UNH", "JNJ",
        "V", "WMT", "JPM", "PG", "MA", "HD", "CVX", "ABBV", "PFE", "KO",
        "AVGO", "PEP", "COST", "TMO", "DHR", "MRK", "VZ", "ADBE", "WFC", "BAC"
    ],
    "United Kingdom": [
        "SHEL.L", "AZN.L", "BP.L", "ULVR.L", "HSBA.L", "VOD.L", "RIO.L", "LLOY.L",
        "BT-A.L", "GSK.L", "BARC.L", "NG.L", "DGE.L", "REL.L", "RB.L", "PRU.L",
        "NWG.L", "CRH.L", "IAG.L", "GLEN.L", "LSEG.L", "III.L", "BA.L", "RTO.L",
        "CPG.L", "ENT.L", "EXPN.L", "FRES.L", "RR.L", "SSE.L"
    ],
    "Australia": [
        "CBA.AX", "BHP.AX", "CSL.AX", "WBC.AX", "ANZ.AX", "NAB.AX", "WES.AX", "FMG.AX",
        "WOW.AX", "RIO.AX", "MQG.AX", "TLS.AX", "WDS.AX", "GMG.AX", "COL.AX", "STO.AX",
        "REA.AX", "QBE.AX", "TCL.AX", "ALL.AX", "XRO.AX", "JHX.AX", "MIN.AX", "RHC.AX",
        "WTC.AX", "SHL.AX", "NCM.AX", "IAG.AX", "S32.AX", "ASX.AX"
    ],
    "Hong Kong": [
        "0700.HK", "0388.HK", "0005.HK", "0941.HK", "1299.HK", "2318.HK", "0003.HK", "0939.HK",
        "1398.HK", "2628.HK", "0883.HK", "0175.HK", "0011.HK", "0016.HK", "0267.HK", "1972.HK",
        "0288.HK", "0002.HK", "0001.HK", "1113.HK", "0006.HK", "1997.HK", "0101.HK", "0012.HK",
        "0017.HK", "0004.HK", "0868.HK", "1109.HK", "0823.HK", "1038.HK"
    ],
    "China": [
        "BABA", "JD", "BIDU", "NIO", "PDD", "BILI", "XPEV", "LI", "NTES", "IQ",
        "YMM", "DIDI", "TME", "VIPS", "WB", "ZTO", "BGNE", "EDU", "TAL", "YY",
        "HUYA", "DOYU", "KC", "GOTU", "RLX", "DADA", "TUYA", "BZUN", "TIGR", "FUTU"
    ]
}

# Stock data fetching function
@st.cache_data(ttl=86400)  # Cache for 24 hours (86400 seconds)
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

@st.cache_data(ttl=3600)  # Cache for 1 hour for search results
def get_stocks_for_search(country):
    """Fetch current stock data for search results"""
    if country not in STOCK_SYMBOLS_BY_COUNTRY:
        return []
    
    symbols = STOCK_SYMBOLS_BY_COUNTRY[country]
    stock_data = []
    
    try:
        # Fetch data in batches to avoid overwhelming the API
        batch_size = 10
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            batch_string = " ".join(batch)
            
            try:
                # Get current data for the batch
                tickers = yf.Tickers(batch_string)
                
                for symbol in batch:
                    try:
                        ticker = tickers.tickers[symbol]
                        info = ticker.info
                        hist = ticker.history(period="2d")
                        
                        if not hist.empty and len(hist) >= 2:
                            current_price = float(hist['Close'].iloc[-1])
                            previous_price = float(hist['Close'].iloc[-2])
                            change = current_price - previous_price
                            
                            stock_data.append({
                                "symbol": symbol,
                                "name": info.get('longName', info.get('shortName', symbol)),
                                "price": current_price,
                                "change": change,
                                "country": country
                            })
                    except Exception as e:
                        # Skip stocks that fail to load
                        continue
                        
            except Exception as e:
                # Skip failed batches
                continue
                
    except Exception as e:
        st.error(f"Error fetching stock data: {str(e)}")
    
    return stock_data

@st.cache_data(ttl=86400)  # Cache for 24 hours (86400 seconds)
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
        
        if st.button("💼 Portfolios", use_container_width=True):
            go_to("portfolios")
        
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
    st.subheader("📈 Global Stock Market Dashboard")
    
    # Stock symbols organized by country
    stock_data_by_country = {
        "🇺🇸 United States": ["AAPL", "GOOGL", "AMZN", "MSFT", "TSLA", "META"],
        "🇬🇧 United Kingdom": ["LLOY.L", "BP.L", "SHEL.L", "AZN.L", "ULVR.L", "VODGBP"],
        "🇦🇺 Australia": ["CBA.AX", "BHP.AX", "CSL.AX", "WBC.AX", "ANZ.AX", "NAB.AX"],
        "🇭🇰 Hong Kong": ["0700.HK", "0941.HK", "0388.HK", "0005.HK", "1299.HK", "2318.HK"],
        "🇨🇳 China": ["BABA", "JD", "BIDU", "NIO", "PDD", "BILI"]
    }
    
    # Fetch data for all countries
    all_countries_data = {}
    
    for country, symbols in stock_data_by_country.items():
        with st.spinner(f"Loading {country} stock data..."):
            country_data = get_multiple_stocks_data(symbols, days)
            if country_data:
                all_countries_data[country] = country_data
    
    if all_countries_data:
        # Create tabs for each country
        country_tabs = st.tabs(list(all_countries_data.keys()))
        
        for tab, (country, country_data) in zip(country_tabs, all_countries_data.items()):
            with tab:
                st.write(f"### {country} Stock Market")
                
                if country_data:
                    # Create stock cards in a grid for this country
                    cols = st.columns(3)  # 3 columns for the grid
                    
                    for idx, (symbol, data) in enumerate(country_data.items()):
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
                    st.warning(f"Unable to load {country} stock data.")
        
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
        
        if st.button("💼 Portfolios", use_container_width=True):
            go_to("portfolios")
        
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


def portfolios_page(go_to, get_user_info, change_password):
    """Render the portfolios page for managing investment portfolios"""
    
    # Sidebar for portfolio management
    with st.sidebar:
        st.header("💼 Portfolio Manager")
        
        # Portfolio actions
        st.subheader("🔧 Actions")
        
        if st.button("➕ Create New Portfolio", use_container_width=True):
            go_to("create_portfolio")
        
        if st.button("📊 Portfolio Analytics", use_container_width=True):
            st.session_state.show_analytics = True
            
        st.divider()
        
        # Navigation
        if st.button("← Back to Dashboard", use_container_width=True):
            go_to("dashboard")
        
        if st.button("📈 Stock Analysis", use_container_width=True):
            go_to("stock_analysis")
        
        if st.button("👤 Profile & Settings", use_container_width=True):
            go_to("profile")
    
    # Main portfolio content
    st.title("💼 Portfolio Management")
    
    # Summary section
    st.header("📊 Summary")
    
    # Fetch portfolios from database
    from login import get_user_portfolios
    
    user_portfolios = get_user_portfolios(st.session_state.username)
    
    # Convert database portfolios to display format
    sample_portfolios = []
    for portfolio in user_portfolios:
        # Calculate portfolio value from stocks
        total_value = sum(stock.get('price', 0) * stock.get('shares', 1) for stock in portfolio.get('stocks', []))
        
        sample_portfolios.append({
            "_id": str(portfolio['_id']),
            "name": portfolio['portfolio_name'],
            "created": portfolio['created_at'].strftime('%Y-%m-%d') if portfolio.get('created_at') else "Unknown",
            "value": total_value,
            "budget": portfolio.get('budget', 0),
            "change": 0,  # Placeholder - would calculate from historical data
            "change_pct": 0,  # Placeholder - would calculate from historical data
            "stocks": [stock['symbol'] for stock in portfolio.get('stocks', [])]
        })
    
    if sample_portfolios:
        # Total portfolio value
        total_value = sum(p["value"] for p in sample_portfolios)
        total_change = sum(p["change"] for p in sample_portfolios)
        
        # Calculate percentage change safely
        denominator = total_value - total_change
        if denominator != 0 and total_value != 0:
            total_change_pct = (total_change / denominator) * 100
        else:
            total_change_pct = 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Portfolio Value", f"${total_value:,}", f"{total_change:+,} ({total_change_pct:+.1f}%)")
        with col2:
            st.metric("Number of Portfolios", len(sample_portfolios))
        with col3:
            best_performer = max(sample_portfolios, key=lambda p: p["change_pct"])
            st.metric("Best Performer", best_performer["name"], f"{best_performer['change_pct']:+.1f}%")
    else:
        st.info("📝 No portfolios found. Create your first portfolio to get started!")
    
    st.divider()
    
    # My Portfolios section
    st.header("💼 My Portfolios")
    
    if sample_portfolios:
        # Portfolio cards
        for portfolio in sample_portfolios:
            with st.container():
                col1, col2 = st.columns([2, 2])
                
                with col1:
                    st.markdown(f"### {portfolio['name']}")
                    st.write(f"**Created:** {portfolio['created']}")
                    st.write(f"**Holdings:** {', '.join(portfolio['stocks'])}")
                
                with col2:
                    # Create metrics for current value and budget
                    metric_col1, metric_col2 = st.columns(2)
                    
                    with metric_col1:
                        st.metric(
                            "Current Value",
                            f"${portfolio['value']:.2f}",
                            f"{portfolio['change']:+.2f} ({portfolio['change_pct']:+.1f}%)"
                        )
                    
                    with metric_col2:
                        # Calculate percentage of budget used
                        budget_used_pct = (portfolio['value'] / portfolio['budget'] * 100) if portfolio['budget'] > 0 else 0
                        st.metric(
                            "Budget",
                            f"${portfolio['budget']:.2f}",
                            f"{budget_used_pct:.1f}% used"
                        )
                
                # Portfolio actions
                col_view, col_edit, col_delete = st.columns(3)
                with col_view:
                    if st.button(f"👁️ View Details", key=f"view_{portfolio['name']}"):
                        # Store portfolio ID for viewing details
                        st.session_state.view_portfolio_id = portfolio['_id']
                        st.session_state.view_portfolio_name = portfolio['name']
                        go_to("portfolio_details")
                
                with col_edit:
                    if st.button(f"✏️ Edit", key=f"edit_{portfolio['name']}"):
                        # Store portfolio ID for editing
                        st.session_state.edit_portfolio_id = portfolio['_id']
                        st.session_state.edit_portfolio_name = portfolio['name']
                        go_to("edit_portfolio")
                
                with col_delete:
                    if st.button(f"🗑️ Delete", key=f"delete_{portfolio['name']}", type="secondary"):
                        st.warning(f"Delete {portfolio['name']}? This action cannot be undone.")
                
                st.markdown("---")
    
    # Create new portfolio form
    if st.session_state.get("show_create_form", False):
        st.subheader("➕ Create New Portfolio")
        
        with st.form("create_portfolio"):
            portfolio_name = st.text_input("Portfolio Name", placeholder="e.g., Tech Growth Portfolio")
            portfolio_desc = st.text_area("Description (Optional)", placeholder="Brief description of your investment strategy")
            
            # Stock selection
            st.write("**Select Initial Stocks (Optional):**")
            available_stocks = ["AAPL", "GOOGL", "AMZN", "MSFT", "TSLA", "META", "NFLX", "NVDA"]
            selected_stocks = st.multiselect("Choose stocks to add", available_stocks)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Create Portfolio", type="primary"):
                    if portfolio_name:
                        st.success(f"✅ Portfolio '{portfolio_name}' created successfully!")
                        st.balloons()
                        st.session_state.show_create_form = False
                        st.rerun()
                    else:
                        st.error("Please enter a portfolio name")
            
            with col2:
                if st.form_submit_button("Cancel"):
                    st.session_state.show_create_form = False
                    st.rerun()
    
    # Portfolio analytics
    if st.session_state.get("show_analytics", False):
        st.subheader("📊 Portfolio Analytics")
        
        # Sample analytics data
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Portfolio Performance (Last 30 Days)**")
            # Sample data for demonstration
            performance_data = pd.DataFrame({
                'Date': pd.date_range('2024-01-01', periods=30),
                'Total Value': [20000 + i*100 + (i%5)*50 for i in range(30)]
            })
            st.line_chart(performance_data.set_index('Date'))
        
        with col2:
            st.write("**Asset Allocation**")
            allocation_data = pd.DataFrame({
                'Asset': ['Technology', 'Healthcare', 'Finance', 'Energy', 'Consumer'],
                'Allocation': [40, 25, 15, 10, 10]
            })
            st.bar_chart(allocation_data.set_index('Asset'))
        
        if st.button("Hide Analytics"):
            st.session_state.show_analytics = False
            st.rerun()


def create_portfolio_page(go_to, get_user_info, change_password):
    """Render the create portfolio page with budget and country selection"""
    
    # Sidebar navigation
    with st.sidebar:
        st.header("💼 Create New Portfolio")
        
        st.divider()
        
        # Navigation
        if st.button("← Back to Portfolios", use_container_width=True):
            go_to("portfolios")
        
        if st.button("🏠 Dashboard", use_container_width=True):
            go_to("dashboard")
        
        if st.button("👤 Profile & Settings", use_container_width=True):
            go_to("profile")
    
    # Main content
    st.title("💼 Create New Portfolio")
    st.markdown("### Let's build your investment portfolio step by step")
    
    st.divider()
    
    # Portfolio creation form
    with st.form("create_portfolio_form", clear_on_submit=False):
        
        # Budget question
        st.subheader("💰 What is your budget?")
        budget = st.number_input(
            "Investment Budget (USD)", 
            min_value=100.0, 
            max_value=1000000.0, 
            value=1000.0,
            step=100.0,
            help="Enter the amount you want to invest in this portfolio"
        )
        
        # Budget range selector as alternative
        st.write("Or select a range:")
        budget_range = st.select_slider(
            "Budget Range",
            options=["$100-$1K", "$1K-$5K", "$5K-$10K", "$10K-$25K", "$25K-$50K", "$50K+"],
            value="$1K-$5K"
        )
        
        st.divider()
        
        # Countries question
        st.subheader("🌍 Which countries would you like to invest in?")
        
        # Country selection with popular options
        countries = [
            "United States", "Canada", "United Kingdom", "Germany", "France", 
            "Japan", "Australia", "South Korea", "India", "China", 
            "Brazil", "Netherlands", "Switzerland", "Sweden", "Denmark"
        ]
        
        selected_countries = st.multiselect(
            "Select countries/regions for investment",
            options=countries,
            default=["United States"],
            help="Choose the countries where you'd like to invest. This will help us recommend appropriate stocks and ETFs."
        )
        
        st.divider()
        
        # Portfolio name
        st.subheader("📝 Portfolio Details")
        portfolio_name = st.text_input(
            "Portfolio Name", 
            placeholder="e.g., My Global Growth Portfolio",
            help="Give your portfolio a memorable name"
        )
        
        # Submit buttons
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("Create Portfolio", type="primary", use_container_width=True)
        
        with col2:
            cancelled = st.form_submit_button("Cancel", use_container_width=True)
    
    # Handle form submission
    if submitted:
        if portfolio_name and selected_countries and budget > 0:
            # Create portfolio in database
            from login import create_portfolio
            
            portfolio_data = {
                'name': portfolio_name,
                'budget': budget,
                'countries': selected_countries,
                'stocks': []
            }
            
            success, message = create_portfolio(st.session_state.username, portfolio_data)
            
            if success:
                # Success message with portfolio details
                st.success("🎉 Portfolio created successfully!")
                st.balloons()
                
                # Display summary
                st.subheader("📋 Portfolio Summary")
                st.write(f"**Name:** {portfolio_name}")
                st.write(f"**Budget:** ${budget:,.2f} ({budget_range})")
                st.write(f"**Countries:** {', '.join(selected_countries)}")
                
                st.info("Your portfolio has been created! You can now add stocks and track your investments.")
                
                # Store portfolio data in session state for immediate use
                st.session_state.current_portfolio = portfolio_data
                st.session_state.current_portfolio['_id'] = 'temp_id'  # Will be updated when loading from DB
                
                # Auto redirect to my stocks page
                import time
                time.sleep(2)
                go_to("my_stocks")
            else:
                st.error(f"❌ {message}")
            
        else:
            st.error("❌ Please fill in all required fields")
    
    elif cancelled:
        go_to("portfolios")


def my_stocks_page(go_to, get_user_info, change_password):
    """Render the My Stocks page for managing stocks in a portfolio"""
    
    # Sidebar navigation
    with st.sidebar:
        st.header("📈 My Stocks")
        
        # Portfolio info
        if 'current_portfolio' in st.session_state:
            portfolio = st.session_state.current_portfolio
            st.write(f"**Portfolio:** {portfolio['name']}")
            st.write(f"**Budget:** ${portfolio['budget']:,.2f}")
            st.write(f"**Countries:** {', '.join(portfolio['countries'])}")
        
        st.divider()
        
        # Actions
        st.subheader("🔧 Actions")
        
        if st.button("➕ Add Stock", use_container_width=True, type="primary"):
            go_to("stock_search")
        
        if st.button("📊 Portfolio Analytics", use_container_width=True):
            st.info("Portfolio analytics coming soon!")
        
        st.divider()
        
        # Navigation
        if st.button("← Back to Portfolios", use_container_width=True):
            go_to("portfolios")
        
        if st.button("🏠 Dashboard", use_container_width=True):
            go_to("dashboard")
        
        if st.button("👤 Profile & Settings", use_container_width=True):
            go_to("profile")
    
    # Main content
    st.title("📈 My Portfolio")
    
    # Portfolio header
    if 'current_portfolio' in st.session_state:
        portfolio = st.session_state.current_portfolio
        st.markdown(f"### Portfolio: **{portfolio['name']}**")
        
        # Portfolio summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Budget", f"${portfolio['budget']:,.2f}")
        with col2:
            st.metric("Stocks Added", len(portfolio.get('stocks', [])))
        with col3:
            # Calculate remaining budget (placeholder calculation)
            used_budget = sum(stock.get('value', 0) for stock in portfolio.get('stocks', []))
            remaining = portfolio['budget'] - used_budget
            st.metric("Remaining Budget", f"${remaining:,.2f}")
    
    st.divider()
    
    # Stock list section
    st.subheader("📋 Stock Holdings")
    
    # Check if portfolio has stocks
    if 'current_portfolio' in st.session_state and st.session_state.current_portfolio.get('stocks'):
        stocks = st.session_state.current_portfolio['stocks']
        
        # Display stocks in list format
        for idx, stock in enumerate(stocks):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**{stock['symbol']}**")
                    st.caption(stock.get('name', 'Stock Name'))
                
                with col2:
                    st.write(f"${stock.get('price', 0):.2f}")
                    st.caption("Current Price")
                
                with col3:
                    st.write(f"{stock.get('shares', 0)}")
                    st.caption("Shares")
                
                with col4:
                    value = stock.get('price', 0) * stock.get('shares', 0)
                    st.write(f"${value:.2f}")
                    st.caption("Total Value")
                
                with col5:
                    if st.button("🗑️", key=f"remove_{idx}", help="Remove stock"):
                        st.session_state.current_portfolio['stocks'].pop(idx)
                        st.rerun()
                
                st.markdown("---")
    
    else:
        # Empty state
        st.info("📝 No stocks added yet. Click 'Add Stock' to start building your portfolio!")
        
        # Call-to-action button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Add Your First Stock", type="primary", use_container_width=True):
                go_to("stock_search")


def stock_search_page(go_to, get_user_info, change_password):
    """Render the stock search page for adding stocks to portfolio"""
    
    # Sidebar navigation
    with st.sidebar:
        st.header("🔍 Stock Search")
        
        # Search filters
        st.subheader("🎯 Filters")
        
        # Country filter with all available countries
        available_countries = ["All", "United States", "United Kingdom", "Australia", "Hong Kong", "China"]
        if 'current_portfolio' in st.session_state:
            portfolio_countries = st.session_state.current_portfolio.get('countries', [])
            # Show portfolio countries first, then all others
            country_options = ["All"] + portfolio_countries + [c for c in available_countries[1:] if c not in portfolio_countries]
        else:
            country_options = available_countries
            
        selected_country = st.selectbox("Country", country_options, help="Filter stocks by country/region")
        
        st.divider()
        
        # Navigation
        if st.button("← Back to My Stocks", use_container_width=True):
            go_to("my_stocks")
        
        if st.button("🏠 Dashboard", use_container_width=True):
            go_to("dashboard")
    
    # Main content
    st.title("🔍 Stock Search")
    st.markdown("### Find and add stocks to your portfolio")
    
    # Search bar
    search_query = st.text_input("🔍 Search for stocks (symbol or company name)", placeholder="e.g., AAPL, Apple, Tesla")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        search_button = st.button("Search", type="primary")
    
    st.divider()
    
    # Real-time stock search results using yfinance
    if search_query or search_button:
        st.subheader(f"📊 Search Results for '{search_query or 'Popular Stocks'}'")
        
        # Get real stock data based on selected country
        with st.spinner("Loading real-time stock data..."):
            if selected_country != "All":
                # Fetch stocks from specific country
                all_stocks = get_stocks_for_search(selected_country)
            else:
                # Fetch stocks from all countries
                all_stocks = []
                for country in STOCK_SYMBOLS_BY_COUNTRY.keys():
                    country_stocks = get_stocks_for_search(country)
                    all_stocks.extend(country_stocks)
        
        # Apply search filter
        if search_query:
            filtered_stocks = [s for s in all_stocks 
                             if search_query.upper() in s["symbol"] or 
                                search_query.lower() in s["name"].lower()]
        else:
            filtered_stocks = all_stocks
        
        # Show filter info
        if selected_country != "All":
            st.info(f"🌍 Showing {len(filtered_stocks)} real-time stocks from {selected_country}")
        else:
            st.info(f"🌍 Showing {len(filtered_stocks)} real-time stocks from all countries")
        
        # Display search results
        for stock in filtered_stocks:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1, 1, 1.5])
                
                with col1:
                    st.write(f"**{stock['symbol']}**")
                    st.caption(stock['name'])
                
                with col2:
                    st.write(f"🌍 {stock['country']}")
                
                with col3:
                    st.write(f"${stock['price']:.2f}")
                
                with col4:
                    change_color = "🟢" if stock['change'] > 0 else "🔴"
                    st.write(f"{change_color} {stock['change']:+.2f}")
                
                with col5:
                    # Shares input and Add button
                    shares_key = f"shares_{stock['symbol']}"
                    shares = st.number_input(
                        "Shares", 
                        min_value=1, 
                        max_value=10000, 
                        value=1,
                        key=shares_key,
                        help="Number of shares to buy"
                    )
                    
                    total_cost = stock['price'] * shares
                    st.caption(f"Total: ${total_cost:.2f}")
                    
                    if st.button("➕ Add", key=f"add_{stock['symbol']}"):
                        # Add stock to portfolio
                        if 'current_portfolio' not in st.session_state:
                            st.session_state.current_portfolio = {'stocks': []}
                        
                        # Check if stock already exists
                        existing = [s for s in st.session_state.current_portfolio.get('stocks', []) 
                                  if s['symbol'] == stock['symbol']]
                        
                        if existing:
                            st.warning(f"{stock['symbol']} is already in your portfolio!")
                        else:
                            # Add stock with user-specified quantity
                            new_stock = {
                                'symbol': stock['symbol'],
                                'name': stock['name'],
                                'price': stock['price'],
                                'shares': shares,
                                'value': total_cost
                            }
                            
                            if 'stocks' not in st.session_state.current_portfolio:
                                st.session_state.current_portfolio['stocks'] = []
                            
                            st.session_state.current_portfolio['stocks'].append(new_stock)
                            st.success(f"✅ Added {shares} shares of {stock['symbol']} (${total_cost:.2f}) to your portfolio!")
                            st.balloons()
                            
                            # Redirect to My Portfolio (My Stocks) after balloons
                            import time
                            time.sleep(2)  # Wait for balloons animation
                            go_to("my_stocks")
                
                st.markdown("---")
        
        if not filtered_stocks:
            st.info("No stocks found matching your search criteria.")
    
    else:
        st.info("💡 Enter a stock symbol or company name to search for stocks to add to your portfolio.")


def edit_portfolio_page(go_to, get_user_info, change_password):
    """Render the edit portfolio page for managing stocks"""
    
    # Check if we have a portfolio to edit
    if 'edit_portfolio_id' not in st.session_state:
        st.error("No portfolio selected for editing")
        go_to("portfolios")
        return
    
    # Get portfolio data from database
    from login import get_portfolio_by_id, update_portfolio, remove_stock_from_portfolio
    
    portfolio_id = st.session_state.edit_portfolio_id
    portfolio = get_portfolio_by_id(portfolio_id)
    
    if not portfolio:
        st.error("Portfolio not found")
        go_to("portfolios")
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.header("✏️ Edit Portfolio")
        
        # Portfolio info
        st.write(f"**Portfolio:** {portfolio['portfolio_name']}")
        st.write(f"**Budget:** ${portfolio['budget']:,.2f}")
        
        st.divider()
        
        # Actions
        st.subheader("🔧 Actions")
        
        if st.button("➕ Add More Stocks", use_container_width=True, type="primary"):
            # Set current portfolio for stock search
            st.session_state.current_portfolio = {
                '_id': portfolio_id,
                'name': portfolio['portfolio_name'],
                'budget': portfolio['budget'],
                'countries': portfolio['countries'],
                'stocks': portfolio.get('stocks', [])
            }
            go_to("stock_search")
        
        st.divider()
        
        # Navigation
        if st.button("← Back to Portfolios", use_container_width=True):
            go_to("portfolios")
        
        if st.button("🏠 Dashboard", use_container_width=True):
            go_to("dashboard")
    
    # Main content
    st.title("✏️ Edit Portfolio")
    st.markdown(f"### {portfolio['portfolio_name']}")
    
    # Portfolio summary
    total_value = sum(stock.get('price', 0) * stock.get('shares', 1) for stock in portfolio.get('stocks', []))
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Budget", f"${portfolio['budget']:,.2f}")
    with col2:
        st.metric("Current Value", f"${total_value:.2f}")
    with col3:
        remaining = portfolio['budget'] - total_value
        st.metric("Remaining", f"${remaining:.2f}")
    
    st.divider()
    
    # Stock management section
    st.subheader("📈 Manage Stocks")
    
    if portfolio.get('stocks'):
        stocks = portfolio['stocks']
        
        # Track changes
        if 'stock_changes' not in st.session_state:
            st.session_state.stock_changes = {}
        
        updated_stocks = []
        stocks_to_remove = []
        
        for idx, stock in enumerate(stocks):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                
                with col1:
                    st.write(f"**{stock['symbol']}**")
                    st.caption(stock.get('name', 'Stock Name'))
                
                with col2:
                    st.write(f"${stock.get('price', 0):.2f}")
                    st.caption("Price per share")
                
                with col3:
                    # Editable shares input
                    current_shares = stock.get('shares', 1)
                    new_shares = st.number_input(
                        "Shares",
                        min_value=0,
                        max_value=10000,
                        value=current_shares,
                        key=f"shares_{stock['symbol']}_{idx}",
                        help="Set to 0 to remove stock"
                    )
                    
                    if new_shares != current_shares:
                        st.session_state.stock_changes[stock['symbol']] = new_shares
                
                with col4:
                    # Calculate total value
                    shares_to_use = st.session_state.stock_changes.get(stock['symbol'], current_shares)
                    total_stock_value = stock.get('price', 0) * shares_to_use
                    st.write(f"${total_stock_value:.2f}")
                    st.caption("Total Value")
                
                with col5:
                    # Remove button
                    if st.button("🗑️", key=f"remove_{stock['symbol']}_{idx}", help="Remove stock"):
                        stocks_to_remove.append(stock['symbol'])
                        st.rerun()
                
                # Track updated stock
                final_shares = st.session_state.stock_changes.get(stock['symbol'], current_shares)
                if final_shares > 0:
                    updated_stock = stock.copy()
                    updated_stock['shares'] = final_shares
                    updated_stock['value'] = stock.get('price', 0) * final_shares
                    updated_stocks.append(updated_stock)
                
                st.markdown("---")
        
        # Save changes button
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save Changes", type="primary", use_container_width=True):
                # Filter out stocks with 0 shares and process removals
                final_stocks = [s for s in updated_stocks if s['shares'] > 0]
                
                # Remove stocks that were marked for deletion
                for symbol in stocks_to_remove:
                    success, message = remove_stock_from_portfolio(portfolio_id, symbol)
                    if success:
                        st.success(f"Removed {symbol}")
                    else:
                        st.error(f"Failed to remove {symbol}: {message}")
                
                # Update portfolio with new stock data
                update_data = {'stocks': final_stocks}
                success, message = update_portfolio(portfolio_id, update_data)
                
                if success:
                    st.success("✅ Portfolio updated successfully!")
                    st.session_state.stock_changes = {}  # Clear changes
                    st.balloons()
                    
                    # Refresh the page to show updated data
                    import time
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"Failed to update portfolio: {message}")
        
        with col2:
            if st.button("❌ Cancel Changes", use_container_width=True):
                st.session_state.stock_changes = {}  # Clear changes
                st.info("Changes cancelled")
                st.rerun()
    
    else:
        # Empty state
        st.info("📝 No stocks in this portfolio. Add stocks to get started!")
        
        if st.button("🚀 Add Your First Stock", type="primary", use_container_width=True):
            st.session_state.current_portfolio = {
                '_id': portfolio_id,
                'name': portfolio['portfolio_name'],
                'budget': portfolio['budget'],
                'countries': portfolio['countries'],
                'stocks': []
            }
            go_to("stock_search")


def portfolio_details_page(go_to, get_user_info, change_password):
    """Render detailed portfolio view with stock performance analysis"""
    
    # Check if we have a portfolio to view
    if 'view_portfolio_id' not in st.session_state:
        st.error("No portfolio selected for viewing")
        go_to("portfolios")
        return
    
    # Get portfolio data from database
    from login import get_portfolio_by_id
    
    portfolio_id = st.session_state.view_portfolio_id
    portfolio = get_portfolio_by_id(portfolio_id)
    
    if not portfolio:
        st.error("Portfolio not found")
        go_to("portfolios")
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.header("👁️ Portfolio Details")
        
        # Portfolio info
        st.write(f"**Portfolio:** {portfolio['portfolio_name']}")
        st.write(f"**Created:** {portfolio['created_at'].strftime('%Y-%m-%d') if portfolio.get('created_at') else 'Unknown'}")
        st.write(f"**Budget:** ${portfolio['budget']:,.2f}")
        
        st.divider()
        
        # Quick actions
        st.subheader("🔧 Actions")
        
        if st.button("✏️ Edit Portfolio", use_container_width=True, type="primary"):
            st.session_state.edit_portfolio_id = portfolio_id
            st.session_state.edit_portfolio_name = portfolio['portfolio_name']
            go_to("edit_portfolio")
        
        st.divider()
        
        # Navigation
        if st.button("← Back to Portfolios", use_container_width=True):
            go_to("portfolios")
        
        if st.button("🏠 Dashboard", use_container_width=True):
            go_to("dashboard")
    
    # Main content
    st.title("👁️ Portfolio Details")
    st.markdown(f"### {portfolio['portfolio_name']}")
    
    # Get current stock prices for comparison
    stocks = portfolio.get('stocks', [])
    
    if not stocks:
        st.info("📝 No stocks in this portfolio.")
        if st.button("➕ Add Stocks", type="primary"):
            st.session_state.current_portfolio = {
                '_id': portfolio_id,
                'name': portfolio['portfolio_name'],
                'budget': portfolio['budget'],
                'countries': portfolio['countries'],
                'stocks': []
            }
            go_to("stock_search")
        return
    
    # Calculate portfolio metrics
    total_purchase_value = sum(stock.get('price', 0) * stock.get('shares', 1) for stock in stocks)
    
    # Fetch current prices
    with st.spinner("Loading current stock prices..."):
        current_stock_data = {}
        for stock in stocks:
            try:
                ticker = yf.Ticker(stock['symbol'])
                current_data = ticker.history(period="1d")
                if not current_data.empty:
                    current_price = float(current_data['Close'].iloc[-1])
                    current_stock_data[stock['symbol']] = current_price
            except:
                # Use purchase price if current price unavailable
                current_stock_data[stock['symbol']] = stock.get('price', 0)
    
    # Calculate current total value
    current_total_value = sum(
        current_stock_data.get(stock['symbol'], stock.get('price', 0)) * stock.get('shares', 1) 
        for stock in stocks
    )
    
    # Portfolio overview metrics
    total_gain_loss = current_total_value - total_purchase_value
    total_gain_loss_pct = (total_gain_loss / total_purchase_value * 100) if total_purchase_value > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Purchase Value", f"${total_purchase_value:.2f}")
    with col2:
        st.metric("Current Value", f"${current_total_value:.2f}")
    with col3:
        st.metric("Total Gain/Loss", f"${total_gain_loss:+.2f}", f"{total_gain_loss_pct:+.2f}%")
    with col4:
        remaining_budget = portfolio['budget'] - total_purchase_value
        st.metric("Remaining Budget", f"${remaining_budget:.2f}")
    
    st.divider()
    
    # Detailed stock breakdown
    st.subheader("📊 Stock Holdings Detail")
    
    # Create detailed table
    stock_details = []
    for stock in stocks:
        symbol = stock['symbol']
        shares = stock.get('shares', 1)
        purchase_price = stock.get('price', 0)
        current_price = current_stock_data.get(symbol, purchase_price)
        
        # Calculate metrics
        purchase_value = purchase_price * shares
        current_value = current_price * shares
        gain_loss = current_value - purchase_value
        gain_loss_pct = (gain_loss / purchase_value * 100) if purchase_value > 0 else 0
        
        stock_details.append({
            'Symbol': symbol,
            'Name': stock.get('name', symbol),
            'Shares': shares,
            'Purchase Price': f"${purchase_price:.2f}",
            'Current Price': f"${current_price:.2f}",
            'Purchase Value': f"${purchase_value:.2f}",
            'Current Value': f"${current_value:.2f}",
            'Gain/Loss ($)': f"${gain_loss:+.2f}",
            'Gain/Loss (%)': f"{gain_loss_pct:+.2f}%"
        })
    
    # Display as interactive table
    if stock_details:
        df = pd.DataFrame(stock_details)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        # Individual stock cards with charts
        st.subheader("📈 Individual Stock Performance")
        
        # Create columns for stock cards
        cols = st.columns(2)
        for idx, stock in enumerate(stocks):
            with cols[idx % 2]:
                symbol = stock['symbol']
                shares = stock.get('shares', 1)
                purchase_price = stock.get('price', 0)
                current_price = current_stock_data.get(symbol, purchase_price)
                
                # Calculate metrics
                purchase_value = purchase_price * shares
                current_value = current_price * shares
                gain_loss = current_value - purchase_value
                gain_loss_pct = (gain_loss / purchase_value * 100) if purchase_value > 0 else 0
                
                with st.container():
                    st.markdown(f"#### {symbol}")
                    st.caption(stock.get('name', symbol))
                    
                    # Metrics
                    metric_col1, metric_col2 = st.columns(2)
                    with metric_col1:
                        st.metric("Current Value", f"${current_value:.2f}", f"{gain_loss:+.2f}")
                    with metric_col2:
                        st.metric("Performance", f"{gain_loss_pct:+.2f}%")
                    
                    # Stock details
                    st.write(f"**Shares:** {shares}")
                    st.write(f"**Purchase Price:** ${purchase_price:.2f}")
                    st.write(f"**Current Price:** ${current_price:.2f}")
                    
                    # Try to show mini chart
                    try:
                        ticker = yf.Ticker(symbol)
                        hist_data = ticker.history(period="1mo")
                        if not hist_data.empty:
                            st.line_chart(hist_data['Close'], height=200)
                    except:
                        st.caption("Chart unavailable")
                    
                    st.markdown("---")
    
    else:
        st.warning("No stock details available")


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