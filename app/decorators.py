from functools import wraps
from flask import session, flash, redirect, url_for


def login_required(func):
    """Decorator to ensure user is logged in."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('user_authenticated'):
            flash('You need to be logged in to access this page.', 'warning')
            return redirect(url_for('routes.login'))
        return func(*args, **kwargs)
    return wrapper
