import streamlit as st
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import time
import requests
from urllib.parse import quote
import re

def format_percentage_with_color(percentage):
    """Format percentage with color coding - green for positive, red for negative"""
    if percentage > 0:
        return f'<span class="positive-percentage">{percentage:+.2f}%</span>'
    elif percentage < 0:
        return f'<span class="negative-percentage">{percentage:+.2f}%</span>'
    else:
        return f'<span class="neutral-percentage">{percentage:.2f}%</span>'

@st.dialog("🗑️ Delete Portfolio")
def show_delete_confirmation_popup():
    """Show portfolio deletion confirmation popup"""
    portfolio_id = st.session_state.get('confirm_delete_portfolio')
    portfolio_name = st.session_state.get('confirm_delete_name', 'Unknown Portfolio')
    
    st.warning(f"⚠️ **Confirm Deletion**")
    st.write(f"Are you sure you want to delete the portfolio **{portfolio_name}**?")
    st.write("**This action cannot be undone.**")
    st.write("")
    
    col_confirm, col_cancel = st.columns(2)
    
    with col_confirm:
        if st.button("🗑️ Yes, Delete", type="primary", use_container_width=True):
            try:
                from login import delete_portfolio
                success, message = delete_portfolio(portfolio_id, st.session_state.username)
                
                if success:
                    st.success(f"✅ Portfolio '{portfolio_name}' deleted successfully!")
                    # Clear session state
                    del st.session_state.confirm_delete_portfolio
                    del st.session_state.confirm_delete_name
                    time.sleep(2)  # Show success message briefly
                    st.rerun()
                else:
                    st.error(f"❌ Failed to delete portfolio: {message}")
                    
            except Exception as e:
                st.error(f"❌ Error deleting portfolio: {str(e)}")
    
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True):
            # Clear confirmation state and close popup
            del st.session_state.confirm_delete_portfolio
            del st.session_state.confirm_delete_name
            st.rerun()

def get_company_news_link(symbol):
    """Get Google News search link for a company"""
    try:
        # Get company name from ticker if possible
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            company_name = info.get('longName', symbol)
        except:
            company_name = symbol
        
        # Create Google News search URL with company name and stock symbol
        search_query = f"{company_name} {symbol} stock"
        encoded_query = quote(search_query)
        google_news_url = f"https://news.google.com/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        return {
            'company_name': company_name,
            'symbol': symbol,
            'search_query': search_query,
            'news_url': google_news_url
        }
        
    except Exception as e:
        st.error(f"Error generating news link: {str(e)}")
        return None

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

# Historical data fetching function from 2000s
@st.cache_data(ttl=86400)  # Cache for 24 hours (86400 seconds)
def get_historical_stock_data(symbol, start_year=2000):
    """Fetch long-term historical stock data from specified start year"""
    try:
        start_date = datetime(start_year, 1, 1)
        end_date = datetime.now()
        
        data = yf.download(symbol, start=start_date, end=end_date, progress=False)
        
        # Flatten multi-level columns if they exist
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[0] for col in data.columns]
        
        return data
    except Exception as e:
        st.error(f"Failed to fetch historical data for {symbol}: {str(e)}")
        return pd.DataFrame()  # Return empty DataFrame on error

def get_stock_info_with_history(symbol):
    """Get stock info including historical data from 2000s"""
    try:
        ticker = yf.Ticker(symbol)
        
        # Get basic info
        info = ticker.info
        
        # Get historical data from 2000
        historical_data = get_historical_stock_data(symbol, 2000)
        
        # Get recent data for current price
        recent_data = ticker.history(period="2d")
        
        stock_info = {
            "symbol": symbol,
            "name": info.get('longName', info.get('shortName', symbol)),
            "sector": info.get('sector', 'N/A'),
            "industry": info.get('industry', 'N/A'),
            "historical_data": historical_data,
            "info": info
        }
        
        if not recent_data.empty and len(recent_data) >= 2:
            current_price = float(recent_data['Close'].iloc[-1])
            previous_price = float(recent_data['Close'].iloc[-2])
            change = current_price - previous_price
            
            stock_info.update({
                "price": current_price,
                "change": change,
                "previous_price": previous_price
            })
        
        return stock_info
        
    except Exception as e:
        st.error(f"Failed to fetch complete info for {symbol}: {str(e)}")
        return None

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


def login_page(go_to, verify_user, update_last_login):
    """Render the login page"""
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login", type="primary", use_container_width=True):
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                if verify_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    update_last_login(username)
                    st.success("Login successful!")
                    go_to("dashboard")
                else:
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
            # Profile photo section
            col_photo, col_info = st.columns([1, 2])
            
            with col_photo:
                st.write("**Profile Photo**")
                
                # Check if user has profile photo
                if user_info.get('profile_photo'):
                    st.image(user_info['profile_photo'], width=150, caption="Current Photo")
                else:
                    # Default avatar placeholder
                    st.write("📷")
                    st.caption("No photo uploaded")
                
                # Photo upload
                uploaded_file = st.file_uploader(
                    "Upload Profile Photo", 
                    type=['png', 'jpg', 'jpeg', 'gif'],
                    help="Max file size: 5MB"
                )
                
                if uploaded_file is not None:
                    if uploaded_file.size > 5 * 1024 * 1024:  # 5MB limit
                        st.error("File size too large. Please upload a file smaller than 5MB.")
                    else:
                        # Display preview
                        st.image(uploaded_file, width=150, caption="Preview")
                        
                        if st.button("Save Photo"):
                            # In a real app, you'd upload to cloud storage (AWS S3, etc.)
                            # For demo, we'll just show success
                            st.success("✅ Profile photo updated!")
                            st.info("Note: Photo upload functionality would connect to cloud storage in production")
            
            with col_info:
                st.write(f"**Username:** {user_info['username']}")
                st.write(f"**Email:** {user_info['email']}")
                st.write(f"**Role:** {user_info.get('role', 'user').title()}")
                
                if user_info.get("created_at"):
                    st.write(
                        f"**Member since:** {user_info['created_at'].strftime('%B %d, %Y')}"
                    )
                st.write(
                    f"**Account Status:** {'Active' if user_info.get('is_active') else 'Inactive'}"
                )
                

        # Profile update forms
        col_left, col_right = st.columns(2)
        
        with col_left:
            with st.expander("📧 Update Email"):
                new_email = st.text_input(
                    "New Email", value=user_info.get("email", "") if user_info else ""
                )
                if st.button("Update Email", key="update_email"):
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
    st.divider()

    # Quick Actions Section at the top
    st.subheader("🚀 Quick Actions")
    
    # Get user portfolios to determine what actions to show
    from login import get_user_portfolios
    user_portfolios = get_user_portfolios(st.session_state.username)
    
    if user_portfolios:
        # User has portfolios - show full quick actions
        action_col1, action_col2, action_col3 = st.columns(3)
        with action_col1:
            if st.button("➕ Create New Portfolio", type="primary", use_container_width=True):
                go_to("create_portfolio")
        with action_col2:
            if st.button("📊 View All Portfolios", use_container_width=True):
                go_to("portfolios")
        with action_col3:
            if st.button("🔎 Search Stocks", use_container_width=True):
                go_to("stock_analysis")
    else:
        # No portfolios yet - show getting started actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Create Your First Portfolio", type="primary", use_container_width=True):
                go_to("create_portfolio")
        with col2:
            if st.button("📚 Learn About Portfolios", use_container_width=True):
                st.info("""
                **What is a Portfolio?**
                
                A portfolio is a collection of stocks from different markets that you want to track and manage. 
                You can:
                - Add stocks from multiple countries
                - Track performance over time
                - Compare different investment strategies
                """)

    st.divider()

    # Portfolio Summary Section
    st.subheader("💼 Your Portfolios Summary")
    
    if user_portfolios:
        # Calculate overall portfolio metrics
        total_portfolios = len(user_portfolios)
        total_stocks = sum(len(p.get('stocks', [])) for p in user_portfolios)
        
        # Calculate total invested across all portfolios using purchase prices
        total_invested = 0
        for portfolio in user_portfolios:
            for stock in portfolio.get('stocks', []):
                # Use purchase_price if available, fallback to 'price' for backward compatibility
                purchase_price = stock.get('purchase_price', stock.get('price', 0))
                total_invested += purchase_price * stock.get('shares', 1)
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Portfolios", total_portfolios)
        with col2:
            st.metric("Total Stocks", total_stocks)
        with col3:
            st.metric("Total Invested", f"${total_invested:,.2f}")
        with col4:
            avg_portfolio_value = total_invested / total_portfolios if total_portfolios > 0 else 0
            st.metric("Avg Portfolio", f"${avg_portfolio_value:,.2f}")
        
        st.divider()
        
        # Portfolio list view
        st.subheader("📊 Portfolio Overview")
        
        # Create table data for portfolios
        portfolio_data = []
        for portfolio in user_portfolios:
            # Portfolio metrics
            stocks = portfolio.get('stocks', [])
            stock_count = len(stocks)
            countries = portfolio.get('countries', [])
            
            # Calculate invested amount using purchase prices
            invested = 0
            for stock in stocks:
                purchase_price = stock.get('purchase_price', stock.get('price', 0))
                invested += purchase_price * stock.get('shares', 1)
            
            # Top holdings (first 3 stocks)
            top_holdings = []
            for stock in stocks[:3]:
                purchase_price = stock.get('purchase_price', stock.get('price', 0))
                stock_value = purchase_price * stock.get('shares', 1)
                top_holdings.append(f"{stock.get('symbol', 'N/A')} ({stock.get('shares', 1)} shares)")
            
            top_holdings_str = ", ".join(top_holdings) if top_holdings else "No stocks"
            if len(stocks) > 3:
                top_holdings_str += f" + {len(stocks) - 3} more"
            
            portfolio_data.append({
                "Portfolio Name": portfolio.get('portfolio_name', 'Unnamed Portfolio'),
                "Total Value": f"${invested:,.2f}",
                "Stocks": stock_count,
                "Markets": ", ".join(countries) if countries else "N/A",
                "Top Holdings": top_holdings_str
            })
        
        # Display as a clean table
        if portfolio_data:
            import pandas as pd
            df = pd.DataFrame(portfolio_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
                
    else:
        # No portfolios yet
        st.info("📝 You haven't created any portfolios yet!")
    
    st.divider()

    # Stock Market Summary Section
    st.subheader("📈 Global Stock Market Dashboard")
    
    # Stock symbols organized by country
    stock_data_by_country = {
        "🇺🇸 United States": [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "UNH", "JNJ",
            "V", "WMT", "JPM", "PG", "MA", "HD", "CVX", "ABBV", "PFE", "KO",
            "AVGO", "PEP", "COST", "TMO", "DHR", "MRK", "VZ", "ADBE", "WFC", "BAC",
            "NFLX", "CRM", "XOM", "LLY", "ABT", "ORCL", "ACN", "NVS", "CMCSA", "DIS",
            "CSCO", "TXN", "MDT", "PM", "QCOM", "HON", "RTX", "UPS", "LOW", "NKE",
            "INTC", "AMGN", "SPGI", "INTU", "CAT", "GS", "IBM", "SBUX", "AMD", "T"
        ],
        "🇬🇧 United Kingdom": [
            "LLOY.L", "BP.L", "SHEL.L", "AZN.L", "ULVR.L", "VODGBP", "LSEG.L", "RIO.L", "HSBA.L", "GSK.L",
            "BARC.L", "NG.L", "DGE.L", "BT-A.L", "REL.L", "GLEN.L", "AAL.L", "NWG.L", "STAN.L", "PRU.L",
            "SSE.L", "CNA.L", "FLTR.L", "IAG.L", "RB.L", "CRDA.L", "INF.L", "LAND.L", "IMB.L", "III.L",
            "ADM.L", "ANTO.L", "AUTO.L", "AV.L", "BA.L", "BNZL.L", "BRBY.L", "CCL.L", "CPG.L", "CRDS.L",
            "EXPN.L", "FRAS.L", "HLMA.L", "IHG.L", "JET.L", "KGF.L", "LGEN.L", "MNG.L", "OCDO.L", "PSH.L",
            "RTO.L", "SGRO.L", "SMDS.L", "SPX.L", "TW.L", "UU.L", "VOD.L", "WTB.L", "3IN.L", "ABDN.L"
        ],
        "🇦🇺 Australia": [
            "CBA.AX", "BHP.AX", "CSL.AX", "WBC.AX", "ANZ.AX", "NAB.AX", "WOW.AX", "FMG.AX", "MQG.AX", "WES.AX",
            "TLS.AX", "RIO.AX", "TCL.AX", "GMG.AX", "STO.AX", "QBE.AX", "ASX.AX", "COL.AX", "JHX.AX", "REA.AX",
            "AMP.AX", "ALL.AX", "APT.AX", "ASP.AX", "AWC.AX", "BEN.AX", "BKL.AX", "BLD.AX", "BOQ.AX", "BPT.AX",
            "BRG.AX", "BSL.AX", "BWP.AX", "CAR.AX", "CCP.AX", "CHC.AX", "CPU.AX", "CTX.AX", "CWN.AX", "DMP.AX",
            "DXS.AX", "ELD.AX", "EVN.AX", "FLT.AX", "GOR.AX", "GPT.AX", "HVN.AX", "IAG.AX", "IEL.AX", "IGO.AX",
            "ILU.AX", "IPL.AX", "JBH.AX", "LLC.AX", "MGR.AX", "MIN.AX", "NEC.AX", "NHF.AX", "NST.AX", "ORA.AX"
        ],
        "🇭🇰 Hong Kong": [
            "0700.HK", "0941.HK", "0388.HK", "0005.HK", "1299.HK", "2318.HK", "0939.HK", "3690.HK", "0883.HK", "1398.HK",
            "2388.HK", "0267.HK", "0175.HK", "0002.HK", "0011.HK", "0016.HK", "0027.HK", "1109.HK", "0006.HK", "0001.HK",
            "0012.HK", "0017.HK", "0019.HK", "0023.HK", "0066.HK", "0083.HK", "0101.HK", "0144.HK", "0151.HK", "0200.HK",
            "0291.HK", "0293.HK", "0322.HK", "0386.HK", "0390.HK", "0392.HK", "0688.HK", "0762.HK", "0823.HK", "0857.HK",
            "0868.HK", "0881.HK", "0914.HK", "0916.HK", "0960.HK", "0968.HK", "0992.HK", "1044.HK", "1072.HK", "1093.HK",
            "1113.HK", "1171.HK", "1177.HK", "1211.HK", "1288.HK", "1336.HK", "1378.HK", "1816.HK", "1880.HK", "1928.HK"
        ],
        "🇨🇳 China": [
            "BABA", "JD", "BIDU", "NIO", "PDD", "BILI", "TME", "IQ", "NTES", "VIPS",
            "YMM", "LI", "XPEV", "EDU", "TAL", "WB", "DOYU", "KC", "TUYA", "DADA",
            "YSG", "TIGR", "FUTU", "RLX", "GOTU", "MOMO", "HUYA", "DOCU", "ZTO", "YTO",
            "STO", "BEST", "QFIN", "LKNCY", "ZLAB", "CAAS", "CBPO", "CANG", "CAN", "CARS",
            "CADC", "CXDC", "DQ", "EH", "FENG", "GSMG", "HEAR", "HCM", "HIMX", "HUIZ",
            "JOBS", "LAIX", "LX", "NAAS", "NIU", "QTT", "RERE", "SOHU", "TOUR", "WDH"
        ]
    }
    
    # Fetch data for all countries (using 1-year period)
    days = 365  # 1 year
    all_countries_data = {}
    
    for country, symbols in stock_data_by_country.items():
        # Only take first 6 stocks for dashboard display
        top_symbols = symbols[:6]
        with st.spinner(f"Loading {country} stock data (1-year history)..."):
            country_data = get_multiple_stocks_data(top_symbols, days)
            if country_data:
                all_countries_data[country] = country_data
    
    if all_countries_data:
        # Create tabs for each country
        country_tabs = st.tabs(list(all_countries_data.keys()))
        
        for tab, (country, country_data) in zip(country_tabs, all_countries_data.items()):
            with tab:
                st.write(f"### {country} Stock Market")
                
                if country_data:
                    # Create stock cards in a grid for this country (top 6 stocks)
                    cols = st.columns(3)  # 3 columns for the grid (6 stocks = 2 rows)
                    
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
                                        
                                        # Price with percentage change and delta
                                        st.metric("Price", f"${float(latest['Close']):.2f}", delta=f"{change_pct:+.2f}%")
                                        
                                        # Mini chart - 1 year historical data
                                        if 'Close' in data.columns and len(data) > 1:
                                            chart_data = data['Close'].tail(365).round(2)  # Show only last 365 days, rounded to 2dp
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
        
        # Stock search
        st.subheader("🔍 Stock Search")
        
        # Create consolidated list of all stocks from all countries
        all_stock_symbols = []
        for country, symbols in STOCK_SYMBOLS_BY_COUNTRY.items():
            all_stock_symbols.extend(symbols)
        
        # Remove duplicates and sort
        all_stock_symbols = sorted(list(set(all_stock_symbols)))
        
        # Search input
        search_query = st.text_input(
            "Search Stock Symbol",
            value="AAPL",
            placeholder="Type to search (e.g., AAPL, GOOGL, TSLA...)",
            help="Search from all available stocks across US, UK, Australia, Hong Kong, and China markets"
        )
        
        # Filter stocks based on search query
        if search_query:
            filtered_stocks = [stock for stock in all_stock_symbols if search_query.upper() in stock.upper()]
            
            # Show filtered results
            if filtered_stocks:
                if len(filtered_stocks) > 10:
                    st.caption(f"Found {len(filtered_stocks)} matches. Showing first 10:")
                    display_stocks = filtered_stocks[:10]
                else:
                    st.caption(f"Found {len(filtered_stocks)} matches:")
                    display_stocks = filtered_stocks
                
                # Create clickable buttons for search results
                cols = st.columns(2)
                for idx, stock in enumerate(display_stocks):
                    with cols[idx % 2]:
                        if st.button(stock, key=f"search_{stock}", use_container_width=True):
                            st.session_state.selected_stock_symbol = stock
                            search_query = stock
                            st.rerun()
                
                # Use the first match or exact match as selected stock
                selected_stock = search_query.upper() if search_query.upper() in [s.upper() for s in all_stock_symbols] else filtered_stocks[0]
            else:
                st.warning("No stocks found matching your search. Try different keywords.")
                selected_stock = "AAPL"  # Default fallback
        else:
            selected_stock = "AAPL"  # Default when no search
        
        # Use session state to persist selection if available
        if hasattr(st.session_state, 'selected_stock_symbol'):
            selected_stock = st.session_state.selected_stock_symbol
        
        # Time range - Fixed for detailed analysis
        st.info("📊 **Analysis Period:** 10 Years (3,650 days)")
        days = 90  # Keep for any remaining sidebar functionality
        
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
    
    # Fetch data - Fixed 10-year period for detailed analysis
    analysis_days = 3650  # 10 years (10 * 365)
    with st.spinner(f"Loading {selected_stock} data (10-year analysis)..."):
        data = get_stock_data(selected_stock, analysis_days)
    
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
            st.markdown("**Current Price**")
            st.markdown(f"${float(latest['Close']):.2f}")
            st.markdown(f"{change:+.2f} ({format_percentage_with_color(change_pct)})", unsafe_allow_html=True)
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
        col1, col2 = st.columns([3, 2])
        
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
        col1, col2 = st.columns([2, 3])
        
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
        
        # Recent Company News
        st.divider()
        st.subheader("📰 Company News")
        
        news_info = get_company_news_link(selected_stock)
        
        if news_info:
            st.write(f"**Company:** {news_info['company_name']}")
            st.write(f"**Stock Symbol:** {news_info['symbol']}")
            st.write(f"**Search Query:** {news_info['search_query']}")
            
            st.link_button(
                f"🔗 View {news_info['company_name']} News on Google", 
                news_info['news_url'],
                use_container_width=True
            )
            
            st.caption("Click the button above to view the latest news about this company on Google News.")
        else:
            st.info(f"📰 Unable to generate news link for {selected_stock}")
            st.caption("There might be an issue fetching company information.")
        
        
    else:
        st.error(f"Unable to load data for {selected_stock}")
        
        # Provide helpful suggestions for common errors
        st.info("**Possible solutions:**")
        suggestions = [
            "Check your internet connection",
            "Verify the stock symbol is correct",
            "Try adding market suffix (e.g., .L for London, .AX for Australia, .HK for Hong Kong)",
            "Make sure the symbol is currently traded"
        ]
        
        for suggestion in suggestions:
            st.write(f"• {suggestion}")
        
        # Show some examples of valid symbols
        st.info("**Valid symbol examples:**")
        examples = {
            "US Stocks": "AAPL, GOOGL, MSFT, TSLA",
            "UK Stocks": "LLOY.L, BP.L, SHEL.L",
            "Australian": "CBA.AX, BHP.AX, ANZ.AX", 
            "Hong Kong": "0700.HK, 0005.HK, 0941.HK"
        }
        
        for market, symbols in examples.items():
            st.write(f"**{market}:** {symbols}")


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
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Portfolio Value", f"${total_value:,.2f}", f"{total_change:+.2f} ({total_change_pct:+.2f}%)")
        with col2:
            st.metric("Number of Portfolios", len(sample_portfolios))
        with col3:
            best_performer = max(sample_portfolios, key=lambda p: p["change_pct"])
            st.metric("Best Performer", best_performer["name"], f"{best_performer['change_pct']:+.2f}%")
        with col4:
            st.metric("Active Portfolios", len([p for p in sample_portfolios if p.get('value', 0) > 0]))
    else:
        st.info("📝 No portfolios found. Create your first portfolio to get started!")
    
    st.divider()
    
    # My Portfolios section
    st.header("📈 My Portfolios")
    
    if sample_portfolios:
        # Bubble sort portfolios by value (highest first)
        def bubble_sort_portfolios_by_value(portfolios):
            """Sort portfolios by value using bubble sort (highest to lowest)"""
            n = len(portfolios)
            for i in range(n):
                for j in range(0, n - i - 1):
                    # Compare adjacent portfolios by value (descending order)
                    if portfolios[j]['value'] < portfolios[j + 1]['value']:
                        # Swap portfolios
                        portfolios[j], portfolios[j + 1] = portfolios[j + 1], portfolios[j]
            return portfolios
        
        # Sort portfolios by value (highest first)
        sorted_portfolios = bubble_sort_portfolios_by_value(sample_portfolios.copy())
        
        # Portfolio cards
        for portfolio in sorted_portfolios:
            with st.container():
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    st.markdown(f"### {portfolio['name']}")
                    st.write(f"**Created:** {portfolio['created']}")
                    st.write(f"**Holdings:** {', '.join(portfolio['stocks'])}")
                
                with col2:
                    # Create metrics for current value
                    st.metric(
                        "Current Value",
                        f"${portfolio['value']:.2f}",
                        f"{portfolio['change']:+.2f} ({portfolio['change_pct']:+.2f}%)"
                    )
                
                # Portfolio actions
                col_view, col_edit, col_share, col_delete = st.columns(4)
                with col_view:
                    if st.button(f"👁️ View", key=f"view_{portfolio['name']}"):
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
                
                with col_share:
                    if st.button(f"🔗 Share", key=f"share_{portfolio['name']}"):
                        # Store portfolio info for sharing
                        st.session_state.share_portfolio = {
                            '_id': portfolio['_id'],
                            'name': portfolio['name'],
                            'value': portfolio['value'],
                            'stocks': portfolio['stocks']
                        }
                
                with col_delete:
                    if st.button(f"🗑️ Delete", key=f"delete_{portfolio['name']}", type="secondary"):
                        st.session_state.confirm_delete_portfolio = portfolio['_id']
                        st.session_state.confirm_delete_name = portfolio['name']
                        st.rerun()
                
                # Share functionality (appears when share button is clicked)
                if st.session_state.get('share_portfolio') and st.session_state.share_portfolio['_id'] == portfolio['_id']:
                    with st.expander(f"🔗 Share Portfolio: {portfolio['name']}", expanded=True):
                        st.write("**Share your portfolio with others:**")
                        
                        # Generate shareable content
                        share_data = st.session_state.share_portfolio
                        
                        # Create shareable URL (in production, this would be a real shareable link)
                        portfolio_url = f"https://yourapp.com/shared-portfolio/{share_data['_id']}"
                        
                        # Portfolio template for sharing
                        share_text = f"""
🚀 Investment Portfolio Template: "{share_data['name']}"

📊 Portfolio Composition:
🎯 {len(share_data['stocks'])} stocks: {', '.join(share_data['stocks'])}

💡 Create your own version of this portfolio!
📱 View Template: {portfolio_url}
                        """.strip()
                        
                        # Portfolio template information
                        st.info("🔒 **Read-Only Portfolio Template** - Others can view your stock selection and create their own similar portfolio, but cannot edit your original portfolio.")
                        
                        # Share options
                        col_share_left, col_share_right = st.columns(2)
                        
                        with col_share_left:
                            st.write("**📋 Share Portfolio Template**")
                            st.text_area("Portfolio Template Message", value=share_text, height=120, key=f"share_text_{share_data['_id']}")
                            
                            col_copy, col_close = st.columns(2)
                            with col_copy:
                                if st.button("📋 Copy Template", key=f"copy_template_{share_data['_id']}", type="primary"):
                                    st.success("✅ Portfolio template copied to clipboard!")
                            
                            with col_close:
                                if st.button("❌ Close", key=f"close_share_{share_data['_id']}"):
                                    del st.session_state.share_portfolio
                                    st.rerun()
                        
                        with col_share_right:
                            st.write("**📈 Portfolio Composition**")
                            st.write("**Stock Holdings:**")
                            for stock in share_data['stocks']:
                                st.write(f"• {stock}")
                            
                            st.write("---")
                            st.write("**🎯 What others get:**")
                            st.caption("✅ Stock symbols and composition")
                            st.caption("✅ Portfolio structure template")
                            st.caption("❌ Your actual investment amounts")  
                            st.caption("❌ Ability to modify your portfolio")
                            
                            st.write("**🔗 Share URL:**")
                            st.code(portfolio_url, language=None)
                            
                            if st.button("🌐 Generate Share Link", key=f"generate_link_{share_data['_id']}"):
                                st.success("✅ Shareable link generated!")
                                st.info("Others can use this link to create a similar portfolio with the same stocks.")
                
                st.markdown("---")
    
    # Portfolio deletion confirmation popup
    if st.session_state.get('confirm_delete_portfolio'):
        show_delete_confirmation_popup()
    
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
    """Render the create portfolio page with country selection"""
    
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
        if portfolio_name and selected_countries:
            # Create portfolio in database
            from login import create_portfolio
            
            portfolio_data = {
                'name': portfolio_name,
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
                st.write(f"**Countries:** {', '.join(selected_countries)}")
                
                st.info("Your portfolio has been created! You can now add stocks and track your investments.")
                
                # Get the created portfolio from database to get the real ID
                from login import get_user_portfolios
                user_portfolios = get_user_portfolios(st.session_state.username)
                
                # Find the newly created portfolio (most recent)
                if user_portfolios:
                    latest_portfolio = user_portfolios[0]  # Sorted by created_at desc
                    st.session_state.current_portfolio = portfolio_data
                    st.session_state.current_portfolio['_id'] = str(latest_portfolio['_id'])
                else:
                    st.session_state.current_portfolio = portfolio_data
                    st.session_state.current_portfolio['_id'] = 'temp_id'
                
                # Auto redirect to my stocks page
                import time
                time.sleep(2)
                go_to("my_stocks")
            else:
                st.error(f"❌ {message}")
            
        else:
            st.error("❌ Please fill in all required fields (Portfolio name and at least one country)")
    
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
    
    # Get current portfolio from database
    portfolio = None
    if 'current_portfolio' in st.session_state:
        portfolio_id = st.session_state.current_portfolio.get('_id')
        if portfolio_id and portfolio_id != 'temp_id':
            from login import get_portfolio_by_id
            portfolio = get_portfolio_by_id(portfolio_id)
        
        if not portfolio:
            # Fallback to session state
            portfolio = st.session_state.current_portfolio
    
    if portfolio:
        # Use database name if available
        portfolio_name = portfolio.get('portfolio_name', portfolio.get('name', 'Unknown Portfolio'))
        st.markdown(f"### Portfolio: **{portfolio_name}**")
        
        # Portfolio summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Stocks Added", len(portfolio.get('stocks', [])))
        with col2:
            # Calculate total portfolio value
            total_value = sum(stock.get('price', 0) * stock.get('shares', 1) for stock in portfolio.get('stocks', []))
            st.metric("Total Value", f"${total_value:,.2f}")
    
    st.divider()
    
    # Stock list section
    st.subheader("📋 Stock Holdings")
    
    # Check if portfolio has stocks
    if portfolio and portfolio.get('stocks'):
        stocks = portfolio['stocks']  # Use database stocks
        
        # Display stocks in list format
        for idx, stock in enumerate(stocks):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1, 1.5, 1])
                
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
                        # Remove from database
                        portfolio_id = st.session_state.current_portfolio.get('_id')
                        if portfolio_id and portfolio_id != 'temp_id':
                            from login import remove_stock_from_portfolio
                            success, message = remove_stock_from_portfolio(portfolio_id, stock['symbol'])
                            if success:
                                st.success(f"✅ Removed {stock['symbol']} from portfolio")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to remove: {message}")
                        else:
                            # Fallback for session state only
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


def show_stock_historical_data(symbol, name):
    """Display historical stock data from 2000s with detailed analysis"""
    st.subheader(f"📊 Historical Analysis: {symbol}")
    st.caption(f"**{name}** - Long-term data from 2000s")
    
    with st.spinner(f"Loading historical data for {symbol} from 2000s..."):
        # Get complete stock info with historical data
        stock_info = get_stock_info_with_history(symbol)
        
        if stock_info and not stock_info['historical_data'].empty:
            historical_data = stock_info['historical_data']
            
            # Basic info - using single row layout to avoid nesting issues
            if 'price' in stock_info:
                st.metric("Current Price", f"${stock_info['price']:.2f}")
            if 'change' in stock_info:
                change_pct = (stock_info['change'] / stock_info['previous_price'] * 100) if stock_info.get('previous_price', 0) > 0 else 0
                st.metric("Daily Change", f"${stock_info['change']:+.2f}", f"{change_pct:+.2f}%")
            st.write(f"**Sector:** {stock_info.get('sector', 'N/A')}")
            st.write(f"**Industry:** {stock_info.get('industry', 'N/A')}")
            
            st.divider()
            
            # Historical performance metrics
            if len(historical_data) > 0:
                first_price = historical_data['Close'].iloc[0]
                last_price = historical_data['Close'].iloc[-1]
                total_return = ((last_price - first_price) / first_price) * 100
                years = len(historical_data) / 252  # Approximate trading days per year
                annualized_return = ((last_price / first_price) ** (1/years) - 1) * 100 if years > 0 else 0
                
                # Display metrics in a vertical layout to avoid column nesting
                st.metric("Total Return", f"{total_return:+.2f}%")
                st.metric("Annualized Return", f"{annualized_return:+.2f}%")
                st.metric("All-Time High", f"${historical_data['High'].max():.2f}")
                st.metric("All-Time Low", f"${historical_data['Low'].min():.2f}")
                
                st.divider()
                
                # Interactive charts
                tab1, tab2, tab3, tab4 = st.tabs(["📈 Price History", "📊 Volume", "🔄 Returns", "📋 Statistics"])
                
                with tab1:
                    st.subheader("Stock Price Over Time")
                    # Create price chart with multiple timeframes
                    timeframe = st.selectbox(
                        "Select Timeframe",
                        ["All Time", "Last 10 Years", "Last 5 Years", "Last 2 Years"],
                        key=f"timeframe_{symbol}"
                    )
                    
                    if timeframe == "All Time":
                        chart_data = historical_data
                    elif timeframe == "Last 10 Years":
                        chart_data = historical_data.tail(10 * 252)
                    elif timeframe == "Last 5 Years":
                        chart_data = historical_data.tail(5 * 252)
                    else:  # Last 2 Years
                        chart_data = historical_data.tail(2 * 252)
                    
                    st.line_chart(chart_data['Close'], height=400)
                    
                    # Show OHLC data
                    st.subheader("OHLC Data")
                    # OHLC charts in vertical layout
                    st.write("**Open Prices**")
                    st.line_chart(chart_data['Open'], height=150)
                    st.write("**High Prices**")
                    st.line_chart(chart_data['High'], height=150)
                    st.write("**Low Prices**")
                    st.line_chart(chart_data['Low'], height=150)
                    st.write("**Close Prices**")
                    st.line_chart(chart_data['Close'], height=150)
                
                with tab2:
                    st.subheader("Trading Volume Over Time")
                    st.bar_chart(chart_data['Volume'], height=400)
                    
                    # Volume statistics
                    avg_volume = chart_data['Volume'].mean()
                    max_volume = chart_data['Volume'].max()
                    st.metric("Average Volume", f"{avg_volume:,.0f}")
                    st.metric("Maximum Volume", f"{max_volume:,.0f}")
                
                with tab3:
                    st.subheader("Daily Returns Analysis")
                    # Calculate daily returns
                    returns = chart_data['Close'].pct_change().dropna()
                    
                    # Returns chart
                    st.line_chart(returns * 100, height=300)
                    
                    # Returns statistics
                    # Returns statistics in vertical layout
                    st.metric("Avg Daily Return", f"{returns.mean() * 100:.2f}%")
                    st.metric("Volatility", f"{returns.std() * 100:.2f}%")
                    st.metric("Best Day", f"{returns.max() * 100:.2f}%")
                    st.metric("Worst Day", f"{returns.min() * 100:.2f}%")
                
                with tab4:
                    st.subheader("Detailed Statistics")
                    
                    # Create comprehensive statistics table
                    stats_data = {
                        "Metric": ["Current Price", "52-Week High", "52-Week Low", "All-Time High", "All-Time Low",
                                 "Total Return", "Annualized Return", "Volatility", "Average Volume", "Market Cap"],
                        "Value": []
                    }
                    
                    # Calculate 52-week highs/lows
                    recent_year = historical_data.tail(252) if len(historical_data) > 252 else historical_data
                    fifty_two_week_high = recent_year['High'].max()
                    fifty_two_week_low = recent_year['Low'].min()
                    
                    stats_data["Value"] = [
                        f"${stock_info.get('price', last_price):.2f}",
                        f"${fifty_two_week_high:.2f}",
                        f"${fifty_two_week_low:.2f}",
                        f"${historical_data['High'].max():.2f}",
                        f"${historical_data['Low'].min():.2f}",
                        f"{total_return:+.2f}%",
                        f"{annualized_return:+.2f}%",
                        f"{returns.std() * 100:.2f}%",
                        f"{historical_data['Volume'].mean():,.0f}",
                        f"${stock_info.get('info', {}).get('marketCap', 'N/A')}"
                    ]
                    
                    stats_df = pd.DataFrame(stats_data)
                    st.dataframe(stats_df, use_container_width=True)
                    
                    # Additional company info
                    if stock_info.get('info'):
                        st.subheader("Company Information")
                        info = stock_info['info']
                        
                        # Company info in single column layout
                        st.write(f"**Country:** {info.get('country', 'N/A')}")
                        st.write(f"**Employees:** {info.get('fullTimeEmployees', 'N/A')}")
                        st.write(f"**Website:** {info.get('website', 'N/A')}")
                        st.write(f"**P/E Ratio:** {info.get('trailingPE', 'N/A')}")
                        st.write(f"**Dividend Yield:** {info.get('dividendYield', 'N/A')}")
                        st.write(f"**Beta:** {info.get('beta', 'N/A')}")
                        
                        # Business summary
                        if info.get('longBusinessSummary'):
                            st.subheader("Business Summary")
                            st.write(info['longBusinessSummary'])
        else:
            st.error(f"No historical data available for {symbol}")
            st.info("This stock may not have been trading since 2000, or there may be an issue fetching the data.")

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
                col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 1.5, 1.5, 2, 1])
                
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
                    # Shares input
                    shares_key = f"shares_{stock['symbol']}"
                    shares = st.number_input(
                        "Shares", 
                        min_value=1, 
                        max_value=10000, 
                        value=1,
                        key=shares_key,
                        help="Number of shares you purchased"
                    )
                    
                    # Purchase price input
                    purchase_price_key = f"purchase_price_{stock['symbol']}"
                    purchase_price = st.number_input(
                        "Avg. Purchase Price per Share ($)",
                        min_value=0.01,
                        max_value=100000.0,
                        value=float(stock['price']),
                        step=0.01,
                        key=purchase_price_key,
                        help="Enter the average price you paid per share (if you bought at different times, calculate the average)"
                    )
                    
                    total_cost = purchase_price * shares
                    st.caption(f"Total Investment: ${total_cost:.2f}")
                    st.caption(f"Current Market Price: ${stock['price']:.2f}")
                    
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
                            # Add stock with user-specified quantity and purchase price
                            new_stock = {
                                'symbol': stock['symbol'],
                                'name': stock['name'],
                                'purchase_price': purchase_price,  # User's actual purchase price
                                'current_price': stock['price'],   # Current market price
                                'price': purchase_price,           # Keep for backward compatibility
                                'shares': shares,
                                'purchase_value': total_cost       # Total amount invested
                            }
                            
                            if 'stocks' not in st.session_state.current_portfolio:
                                st.session_state.current_portfolio['stocks'] = []
                            
                            # Add to session state
                            st.session_state.current_portfolio['stocks'].append(new_stock)
                            
                            # Save to MongoDB database
                            from login import add_stock_to_portfolio
                            portfolio_id = st.session_state.current_portfolio.get('_id')
                            
                            if portfolio_id and portfolio_id != 'temp_id':
                                db_success, db_message = add_stock_to_portfolio(portfolio_id, new_stock)
                                if db_success:
                                    st.success(f"✅ Added {shares} shares of {stock['symbol']} at ${purchase_price:.2f}/share (${total_cost:.2f} total) to your portfolio!")
                                    st.balloons()
                                    
                                    # Redirect to My Portfolio (My Stocks) after balloons
                                    import time
                                    time.sleep(2)  # Wait for balloons animation
                                    go_to("my_stocks")
                                else:
                                    st.error(f"❌ Failed to save to database: {db_message}")
                            else:
                                st.error("❌ Portfolio not found in database")
                
                with col6:
                    # Historical data button
                    if st.button("📊 History", key=f"history_{stock['symbol']}", help="View historical data from 2000s"):
                        show_stock_historical_data(stock['symbol'], stock['name'])
                
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
        
        st.divider()
        
        # Actions
        st.subheader("🔧 Actions")
        
        if st.button("➕ Add More Stocks", use_container_width=True, type="primary"):
            # Set current portfolio for stock search
            st.session_state.current_portfolio = {
                '_id': portfolio_id,
                'name': portfolio['portfolio_name'],
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
    
    # Portfolio name editing section
    st.subheader("📝 Portfolio Information")
    
    col_name, col_name_btn = st.columns([3, 1])
    with col_name:
        # Show current name or edit field
        if st.session_state.get('editing_portfolio_name'):
            new_portfolio_name = st.text_input(
                "Portfolio Name",
                value=portfolio['portfolio_name'],
                key="portfolio_name_input",
                help="Enter the new name for your portfolio"
            )
        else:
            st.markdown(f"**Current Name:** {portfolio['portfolio_name']}")
    
    with col_name_btn:
        st.write("") # Spacing
        if st.session_state.get('editing_portfolio_name'):
            col_save, col_cancel = st.columns(2)
            with col_save:
                if st.button("💾", key="save_name", help="Save new name"):
                    if 'portfolio_name_input' in st.session_state and st.session_state.portfolio_name_input.strip():
                        # Update portfolio name in database
                        success, message = update_portfolio(portfolio_id, {'portfolio_name': st.session_state.portfolio_name_input.strip()})
                        
                        if success:
                            st.success(f"✅ Portfolio name updated to '{st.session_state.portfolio_name_input}'!")
                            st.session_state.editing_portfolio_name = False
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to update name: {message}")
                    else:
                        st.error("Please enter a valid portfolio name")
            
            with col_cancel:
                if st.button("❌", key="cancel_name", help="Cancel editing"):
                    st.session_state.editing_portfolio_name = False
                    st.rerun()
        else:
            if st.button("✏️ Edit Name", key="edit_name", help="Edit portfolio name"):
                st.session_state.editing_portfolio_name = True
                st.rerun()
    
    st.divider()
    
    # Portfolio summary
    st.subheader("💰 Portfolio Summary")
    total_value = sum(stock.get('price', 0) * stock.get('shares', 1) for stock in portfolio.get('stocks', []))
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Value", f"${total_value:.2f}")
    with col2:
        st.metric("Number of Stocks", len(portfolio.get('stocks', [])))
    
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
                col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1, 1.5, 1])
                
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
                        # Mark stock for removal (will be processed when Save is clicked)
                        st.session_state.stock_changes[stock['symbol']] = 0
                        st.info(f"{stock['symbol']} marked for removal. Click 'Save Changes' to confirm.")
                
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
                    # Note: Page will refresh on next interaction
                else:
                    st.error(f"Failed to update portfolio: {message}")
        
        with col2:
            if st.button("❌ Cancel Changes", use_container_width=True):
                st.session_state.stock_changes = {}  # Clear changes
                st.info("Changes cancelled")
    
    else:
        # Empty state
        st.info("📝 No stocks in this portfolio. Add stocks to get started!")
        
        if st.button("🚀 Add Your First Stock", type="primary", use_container_width=True):
            st.session_state.current_portfolio = {
                '_id': portfolio_id,
                'name': portfolio['portfolio_name'],
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
                'countries': portfolio['countries'],
                'stocks': []
            }
            go_to("stock_search")
        return
    
    # Calculate portfolio metrics using purchase prices
    total_purchase_value = 0
    for stock in stocks:
        purchase_price = stock.get('purchase_price', stock.get('price', 0))
        shares = stock.get('shares', 1)
        total_purchase_value += purchase_price * shares
    
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
                # If real-time data fails, try to use stored current_price, otherwise mark as unavailable
                stored_current = stock.get('current_price')
                if stored_current:
                    current_stock_data[stock['symbol']] = stored_current
                # If no current price available, don't store anything - let the display logic handle it
    
    # Calculate current total value using proper current prices
    current_total_value = 0
    for stock in stocks:
        symbol = stock['symbol']
        shares = stock.get('shares', 1)
        purchase_price = stock.get('purchase_price', stock.get('price', 0))
        # Get current price from live data, fallback to stored current_price, then purchase_price as last resort
        current_price = current_stock_data.get(symbol) or stock.get('current_price') or purchase_price
        current_total_value += current_price * shares
    
    # Portfolio overview metrics
    total_gain_loss = current_total_value - total_purchase_value
    total_gain_loss_pct = (total_gain_loss / total_purchase_value * 100) if total_purchase_value > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Purchase Value", f"${total_purchase_value:.2f}")
    with col2:
        st.metric("Current Value", f"${current_total_value:.2f}")
    with col3:
        st.markdown("**Total Gain/Loss**")
        st.markdown(f"${total_gain_loss:+.2f}")
        st.markdown(format_percentage_with_color(total_gain_loss_pct), unsafe_allow_html=True)
    
    st.divider()
    
    # Detailed stock breakdown
    st.subheader("📊 Stock Holdings Detail")
    
    # Create detailed table
    stock_details = []
    for stock in stocks:
        symbol = stock['symbol']
        shares = stock.get('shares', 1)
        # Use the specific purchase_price field, fallback to 'price' for backward compatibility
        purchase_price = stock.get('purchase_price', stock.get('price', 0))
        # Get current market price from live data, fallback to stored current_price, then purchase_price as last resort
        current_price = current_stock_data.get(symbol) or stock.get('current_price') or purchase_price
        # Flag if we're using purchase price as current price (indicates data unavailable)
        using_purchase_as_current = not (current_stock_data.get(symbol) or stock.get('current_price'))
        
        # Calculate metrics
        purchase_value = purchase_price * shares
        current_value = current_price * shares
        gain_loss = current_value - purchase_value
        gain_loss_pct = (gain_loss / purchase_value * 100) if purchase_value > 0 else 0
        
        # Format current price with indicator if it's actually the purchase price
        current_price_display = f"${current_price:.2f}"
        if using_purchase_as_current:
            current_price_display += " (est.)"
        
        stock_details.append({
            'Symbol': symbol,
            'Company Name': stock.get('name', symbol),
            'Number of Shares': shares,
            'Average Purchase Price': f"${purchase_price:.2f}",
            'Purchase Value': f"${purchase_value:.2f}",
            'Current Average Price': current_price_display,
            'Current Value': f"${current_value:.2f}",
            'Percentage Change': format_percentage_with_color(gain_loss_pct),
            'Value Change': f"${gain_loss:+.2f}"
        })
    
    # Display as interactive table
    if stock_details:
        df = pd.DataFrame(stock_details)
        # Convert to HTML to support color formatting
        st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
        
        st.divider()
        
        # Individual stock cards with charts
        st.subheader("📈 Individual Stock Performance")
        
        # Create columns for stock cards
        cols = st.columns(3)
        for idx, stock in enumerate(stocks):
            with cols[idx % 2]:
                symbol = stock['symbol']
                shares = stock.get('shares', 1)
                # Use the specific purchase_price field, fallback to 'price' for backward compatibility
                purchase_price = stock.get('purchase_price', stock.get('price', 0))
                # Get current market price from live data, fallback to stored current_price, then purchase_price
                current_price = current_stock_data.get(symbol) or stock.get('current_price') or purchase_price
                
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
                        st.markdown("**Performance**")
                        st.markdown(format_percentage_with_color(gain_loss_pct), unsafe_allow_html=True)
                    
                    # Stock details
                    st.write(f"**Shares:** {shares}")
                    st.write(f"**Purchase Price:** ${purchase_price:.2f}")
                    st.write(f"**Current Price:** ${current_price:.2f}")
                    
                    # Action buttons
                    button_col1, button_col2 = st.columns(2)
                    with button_col1:
                        if st.button("📊 View History", key=f"portfolio_history_{symbol}_{idx}", help="View historical data from 2000s"):
                            show_stock_historical_data(symbol, stock.get('name', symbol))
                    
                    # Try to show mini chart
                    try:
                        ticker = yf.Ticker(symbol)
                        hist_data = ticker.history(period="1mo")
                        if not hist_data.empty:
                            st.line_chart(hist_data['Close'], height=200)
                            st.caption("Last 30 days")
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