from app import db
from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, current_user
from app.models import User

public = Blueprint('public', __name__)


@public.route('/')
def index():
    return render_template('public/index.html')


@public.route('/contact')
def contact():
    page_title = 'Contact Us'
    return render_template('public/contact.html', page_title=page_title)


@public.route('/borrow')
def borrow():
    page_title = 'AD&D Insurance'
    return render_template('public/life.html', page_title=page_title)


@public.route('/about')
def about():
    page_title = 'About Us'
    return render_template('public/about.html', page_title=page_title)

# ================================================ credit card ===================================================

@public.route('/loan/credit-card')
def credit_card():
    page_title = "Credit card"
    return render_template('public/credit-card.html', page_title=page_title)


@public.route('/loan/vehicle')
def vehicle():
    page_title = "Vehicle Loan"
    return render_template('public/vehicle.html', page_title=page_title)


@public.route('/loan/home')
def home():
    page_title = "Home Loan"
    return render_template('public/home.html', page_title=page_title)


@public.route('/loan/personal-loan')
def personal_loan():
    return render_template('public/personal-loan.html')

# ================================================ credit card ===================================================


@public.route('/invest/ira')
def ira():
    page_title = 'Traditional IRA'
    return render_template('public/ira.html', page_title=page_title)


@public.route('/invest/others')
def others():
    return render_template('public/others.html')

# ================================================ protect ===================================================

@public.route('/protect/life')
def life():
    page_title = 'AD&D Insurance'
    return render_template('public/life.html', page_title=page_title)


@public.route('/protect/home')
def protect_home():
    page_title = 'Homeowners Insurance'
    return render_template('public/protect_home.html', page_title=page_title)


@public.route('/protect/auto')
def auto():
    page_title = 'Auto & Home Insurance'
    return render_template('public/auto.html', page_title=page_title)