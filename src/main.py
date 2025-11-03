import streamlit as st
from login import (verify_user, register_user, get_user_info, 
                   change_password, update_last_login, create_portfolio, 
                   get_user_portfolios, get_portfolio_by_id, update_portfolio, 
                   delete_portfolio, add_stock_to_portfolio, remove_stock_from_portfolio)
from ui import login_page, register_page, dashboard_page, stock_analysis_page, portfolios_page, create_portfolio_page, my_stocks_page, stock_search_page, edit_portfolio_page, portfolio_details_page
from database import initialize_database

# Page config
st.set_page_config(
    page_title="Secure Login App", 
    layout="centered",
    initial_sidebar_state="collapsed",
    page_icon=""
)


# Initialize database on first run
if "db_initialized" not in st.session_state:
    if initialize_database():
        st.session_state.db_initialized = True
    else:
        st.error("Failed to initialise database. Please check your MongoDB connection.")
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
    .positive-percentage {
        color: #28a745;
        font-weight: bold;
    }
    .negative-percentage {
        color: #dc3545;
        font-weight: bold;
    }
    .neutral-percentage {
        color: #6c757d;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Add connection status indicator
    if st.session_state.get("db_initialized"):
        st.markdown('<div class="status-indicator"> Connected</div>', unsafe_allow_html=True)
    
    # Route to appropriate page
    if st.session_state.logged_in:
        if st.session_state.page == "stock_analysis":
            stock_analysis_page(go_to, get_user_info, change_password)
        elif st.session_state.page == "portfolios":
            portfolios_page(go_to, get_user_info, change_password)
        elif st.session_state.page == "create_portfolio":
            create_portfolio_page(go_to, get_user_info, change_password)
        elif st.session_state.page == "my_stocks":
            my_stocks_page(go_to, get_user_info, change_password)
        elif st.session_state.page == "stock_search":
            stock_search_page(go_to, get_user_info, change_password)
        elif st.session_state.page == "edit_portfolio":
            edit_portfolio_page(go_to, get_user_info, change_password)
        elif st.session_state.page == "portfolio_details":
            portfolio_details_page(go_to, get_user_info, change_password)
        else:
            dashboard_page(go_to, get_user_info, change_password)
    elif st.session_state.page == "register":
        register_page(go_to, register_user)
    else:
        login_page(go_to, verify_user, update_last_login)

if __name__ == "__main__":
    main()