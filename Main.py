import streamlit as st
import Authentication, 

# Page config
st.set_page_config(page_title="Login App", layout="centered")

# Session state
if "page" not in st.session_state:
    st.session_state.page = "login"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Navigation
def go_to(page):
    st.session_state.page = page
    st.rerun()

def login():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if verify_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success("Login successful")
            go_to("dashboard")
        else:
            st.error("Invalid credentials")

    st.write("Don't have an account?")
    if st.button("Register here"):
        go_to("register")

def register():
    st.title("Register")

    username = st.text_input("Choose a username")
    email = st.text_input("Email")
    password = st.text_input("Choose a password", type="password")
    confirm_password = st.text_input("Confirm password", type="password")

    if st.button("Register"):
        if password != confirm_password:
            st.error("Passwords do not match")
        elif user_exists(username):
            st.error("Username already exists")
        else:
            success = register_user(username, password, email)
            if success:
                st.success("Registration successful! Please log in.")
                go_to("login")
            else:
                st.error("Registration failed. Try again.")

    if st.button("Back to login"):
        go_to("login")

def dashboard():
    st.title("Dashboard")
    st.write(f"Welcome, **{st.session_state.username}**!")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        go_to("login")

# Main router
if st.session_state.logged_in:
    dashboard()
elif st.session_state.page == "register":
    register()
else:
    login()
