import streamlit as st
from login import (verify_user, register_user, get_user_info, 
                   change_password, is_account_locked, handle_failed_login, 
                   update_last_login)
from ui import login_page, register_page, dashboard_page
from database import initialize_database

# Page config
st.set_page_config(
    page_title="Secure Login App", 
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon="🔐"
)

# Initialize database on first run
if "db_initialized" not in st.session_state:
    if initialize_database():
        st.session_state.db_initialized = True
    else:
        st.error("Failed to initialize database. Please check your MongoDB connection.")
        st.stop()

# Session state initialization
if "page" not in st.session_state:
    st.session_state.page = "login"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Navigation function
def go_to(page):
    st.session_state.page = page
    st.rerun()

# Main application router
def main():
    # Add custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
    .status-indicator {
        position: fixed;
        top: 10px;
        right: 10px;
        background: green;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 12px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Add connection status indicator
    if st.session_state.get("db_initialized"):
        st.markdown('<div class="status-indicator">🟢 Connected</div>', unsafe_allow_html=True)
    
    # Route to appropriate page
    if st.session_state.logged_in:
        if st.session_state.page == "profile":
            profile_page(go_to, get_user_info, change_password)
        elif st.session_state.page == "stock_analysis":
            stock_analysis_page(go_to, get_user_info, change_password)
        else:
            dashboard_page(go_to, get_user_info, change_password)
    elif st.session_state.page == "register":
        register_page(go_to, register_user)
    else:
        # login_page(go_to, verify_user, is_account_locked, handle_failed_login, update_last_login)
        st.title("🔐 Login Page Disabled")
        st.info("Login page is temporarily disabled for development.")
        if st.button("Go to Dashboard (Test)"):
            st.session_state.logged_in = True
            st.session_state.username = "test_user"
            go_to("dashboard")

if __name__ == "__main__":
    main()