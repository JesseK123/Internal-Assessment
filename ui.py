import streamlit as st
from Authentication import verify_user, user_exists, register_user

# Session state initialization
def initialize_session():
    if "page" not in st.session_state:
        st.session_state.page = "login"
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = ""

# Navigation logic
def go_to(page):
    st.session_state.page = page
    st.rerun()

# Authentication business logic
def handle_login(username, password):
    if verify_user(username, password):
        st.session_state.logged_in = True
        st.session_state.username = username
        st.success("Login successful")
        go_to("dashboard")
        return True
    else:
        st.error("Incorrect")
        return False

def handle_registration(username, email, password, confirm_password):
    if password != confirm_password:
        st.error("Passwords do not match")
        return False
    elif user_exists(username):
        st.error("Username already exists")
        return False
    else:
        success = register_user(username, password, email)
        if success:
            st.success("Registration successful! Please log in.")
            go_to("login")
            return True
        else:
            st.error("Registration failed. Try again.")
            return False

def handle_logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    go_to("login")

# UI Components
def login_page():
    st.title("Login")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        handle_login(username, password)
    
    st.write("Don't have an account?")
    if st.button("Register here"):
        go_to("register")

def register_page():
    st.title("Register")
    
    username = st.text_input("Choose a username")
    email = st.text_input("Email")
    password = st.text_input("Choose a password", type="password")
    confirm_password = st.text_input("Confirm password", type="password")
    
    if st.button("Register"):
        handle_registration(username, email, password, confirm_password)
    
    if st.button("Back to login"):
        go_to("login")

def dashboard_page():
    st.title("Dashboard")
    st.write(f"Welcome, **{st.session_state.username}**!")
    
    if st.button("Logout"):
        handle_logout()

# Main routing logic
def run_app():
    st.set_page_config(page_title="Login App", layout="centered")
    initialize_session()
    
    if st.session_state.logged_in:
        dashboard_page()
    elif st.session_state.page == "register":
        register_page()
    else:
        login_page()