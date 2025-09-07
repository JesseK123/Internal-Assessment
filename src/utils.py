"""
General utility functions
"""

import streamlit as st
import time
import re


def logout_user():
    """Clear all session state and logout user"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("Logged out successfully!")


def format_percentage_with_color(percentage):
    """Format percentage with color coding - green for positive, red for negative"""
    if percentage > 0:
        return f'<span class="positive-percentage">{percentage:+.2f}%</span>'
    elif percentage < 0:
        return f'<span class="negative-percentage">{percentage:+.2f}%</span>'
    else:
        return f'<span class="neutral-percentage">{percentage:.2f}%</span>'


@st.dialog("Delete Portfolio")
def show_delete_confirmation_popup():
    """Show portfolio deletion confirmation popup"""
    portfolio_id = st.session_state.get('confirm_delete_portfolio')
    portfolio_name = st.session_state.get('confirm_delete_name', 'Unknown Portfolio')
    
    st.warning(f"**Confirm Deletion**")
    st.write(f"Are you sure you want to delete the portfolio **{portfolio_name}**?")
    st.write("**This action cannot be undone.**")
    st.write("")
    
    col_confirm, col_cancel = st.columns(2)
    
    with col_confirm:
        if st.button("Yes, Delete", type="primary", use_container_width=True):
            try:
                from login import delete_portfolio
                success, message = delete_portfolio(portfolio_id, st.session_state.username)
                
                if success:
                    st.success(f"Portfolio '{portfolio_name}' deleted successfully!")
                    del st.session_state.confirm_delete_portfolio
                    del st.session_state.confirm_delete_name
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"Failed to delete portfolio: {message}")
                    
            except Exception as e:
                st.error(f"Error deleting portfolio: {str(e)}")
    
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            del st.session_state.confirm_delete_portfolio
            del st.session_state.confirm_delete_name
            st.rerun()


def calculate_password_strength(password):
    """Calculate password strength score"""
    score = 0
    feedback = []
    
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("At least 8 characters")
    
    if re.search(r"[a-z]", password):
        score += 1
    else:
        feedback.append("Lowercase letter")
    
    if re.search(r"[A-Z]", password):
        score += 1
    else:
        feedback.append("Uppercase letter")
    
    if re.search(r"\d", password):
        score += 1
    else:
        feedback.append("Number")
    
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 1
    else:
        feedback.append("Special character")
    
    strength_levels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
    strength = strength_levels[min(score, len(strength_levels) - 1)]
    
    return score, strength, feedback