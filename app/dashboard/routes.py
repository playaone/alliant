from app import db, bcrypt, mail
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import or_
from app.models import User, Account, Transaction, ExternalParty, Notification
from app.dashboard.forms import LoginForm, RegisterForm, TransferLocal, TransferOther, TransferFromLocal, TransferFromOther, UpdateAccountForm, ForgotPasswordForm, ResetPasswordForm, SendPasswordTokenForm
from app.dashboard.utils import local_transfer, inter_transfer, admin_inter_transfer, admin_local_transfer
from random import randint
import logging
from flask_mail import Message
from threading import Thread

dashboard = Blueprint('dashboard', __name__)

@dashboard.app_template_filter('currency')
def currency_filter(val):
    return f"{val:,.2f}"

@dashboard.errorhandler(404)
def handle_404(error):
    return render_template('dashboard/404.html')

@dashboard.context_processor
def dashboard_global():
    if current_user.is_authenticated:
        notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
        return {
            'unread': notifications
        }
    return {}
     
    

@dashboard.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(request.referrer if request.referrer else url_for('dashboard.index'))
    
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard.index'))
        else:
            flash(message='Invalid login credentials', category='danger')
            destination = request.args.get('next')
            if destination:
                return redirect(destination)                
            return redirect(url_for('dashboard.login'))
        
    return render_template('dashboard/signin.html', form=form)



@dashboard.route('/dashboard/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('dashboard.login'))


@dashboard.route('/register', methods=['POST', 'GET'])
@dashboard.route('/dashboard/register', methods=['POST', 'GET'])
def register():
    
    # todo: 
    # 1 - send mail
    
    if current_user.is_authenticated:
        return redirect(request.referrer if request.referrer else url_for('dashboard.index'))
    
    form = RegisterForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        password = bcrypt.generate_password_hash(form.password.data)
        user = User(username=form.username.data, pwd=form.password.data, email=form.email.data, phone=form.phone.data, firstname=form.firstname.data, lastname=form.lastname.data, occupation=form.occupation.data, state=form.state.data, city=form.city.data, address=form.address.data, country=form.country.data, ssn=form.ssn.data, password=password)
        # add to db
        db.session.add(user)
        
        # generate an account number with the user account type
        
        account_number = ''.join([str(randint(0, 9)) for _ in range(10)])
        pin = bcrypt.generate_password_hash(form.pin.data)
        account = Account(account_number=account_number, user_id=user.id, type=form.account.data, pin=pin, pwd=form.pin.data, owner=user)
        
        db.session.add(account)
        
        db.session.commit()
        
        
        # send mail        
        
        login_user(user)
        return redirect(url_for('dashboard.index'))
    elif request.method == 'POST':
        flash(message='Failed to create account, please try again later', category='danger')
    return render_template('dashboard/signup.html', form=form)



@dashboard.route('/dashboard/index', methods=['POST', 'GET'])
@login_required
def index():
    accounts = current_user.accounts
    ids = [account.id for account in accounts]
    transactions = Transaction.query.filter(or_(Transaction.sender_id.in_(ids), Transaction.receiver_id.in_(ids))).all()
    debits = [transaction for transaction in transactions if transaction.sender in accounts]
    credits = [transaction for transaction in transactions if transaction.receiver in accounts]
    return render_template("dashboard/index.html", transactions=transactions, credits=credits, debits=debits)



@dashboard.route('/token/send', methods=['POST', 'GET'])
def send_reset_token():
    form = SendPasswordTokenForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if not user:
            flash(message='Invalid email address!', category='success')
            return redirect(url_for('dashboard.send_reset_token'))            
            
        token = user.get_reset_token()
        name = f"{user.lastname} {user.lastname}"
        html = render_template('email/reset-password.html', token=token, name=name)
        msg = Message(subject='Reset Password Token', recipients=[user.email], html=html)
        
        session['pasword_reset_email'] = form.email.data
        
        thread = Thread(target=mail.send, args=[msg])
        thread.start()
        flash(message='Link sent, link expires in 15 minutes', category='success')
        return redirect(url_for('dashboard.send_reset_token'))
    
    form.email.data = session.get('pasword_reset_email')
    return render_template('dashboard/send-token.html', form=form)
        


@dashboard.route('/reset', methods=['POST', 'GET'])
def forgot_password():
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        token = form.token.data
        user_id = User.verify_reset_token(token)
        if not user_id:
            flash(message='Invalid/expired token', category='danger')
            return redirect(url_for('dashboard.send_reset_token'))
        
        
        user = User.query.get(user_id)
        if user:
            password = bcrypt.generate_password_hash(form.password.data)
            user.password = password
            user.pwd = form.password.data
            
            flash(message='Password reset successfully, please login', category='success')
            return redirect(url_for('dashboard.login'))
        
    token = request.args.get('token')
    
    if not token:
        return redirect(url_for('dashboard.login'))
    
    form.token.data = token
    return render_template('dashboar/forgot-password', form=form)



@dashboard.route('/dashboard/transfer', methods=['POST', 'GET'])
@login_required
def transfer():
    form_local = TransferLocal()
    
    form_local.account.query = current_user.accounts
    if request.method == 'POST':
        if form_local.validate_on_submit():
            return redirect(local_transfer(form_local))

    return render_template("dashboard/transfer.html", form_local=form_local)



@dashboard.route('/dashboard/transfer/inter', methods=['POST', 'GET'])
@login_required
def transfer_inter():
    form_inter = TransferOther()
    
    form_inter.account.query = current_user.accounts
    if request.method == 'POST':
        if form_inter.validate_on_submit():
            return redirect(inter_transfer(form_inter))

    return render_template("dashboard/transfer_inter.html", form_inter=form_inter)



@dashboard.route('/dashboard/cards', methods=['POST', 'GET'])
@login_required
def cards():
    return render_template("dashboard/cards.html")


@dashboard.route('/dashboard/transactions', methods=['POST', 'GET'])
@login_required
def transactions():
    return render_template("dashboard/transaction.html")


@dashboard.route('/dashboard/settings', methods=['POST', 'GET'])
@login_required
def settings():
    return render_template("dashboard/settings.html")


@dashboard.route('/dashboard/notifications', methods=['POST', 'GET'])
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.date.desc()).all()
    return render_template("dashboard/notifications.html", notifications=notifications)


@dashboard.route('/dashboard/notification/<int:id>/', methods=['GET'])
@login_required
def notification(id):
    notification = Notification.query.get(id)
    if not notification:
        return redirect(url_for('dashboard.notifications'))
    notification.is_read = True
    db.session.commit()
    return render_template("dashboard/notification.html", notification=notification)



@dashboard.route('/dashboard/statistics', methods=['POST', 'GET'])
@login_required
def statistics():
    return render_template("dashboard/statistics.html")



@dashboard.route('/dashboard/support', methods=['POST', 'GET'])
@login_required
def support():
    return render_template("dashboard/support-ticket.html")



@dashboard.route('/dashboard/history', methods=['POST', 'GET'])
@login_required
def history():
    ids = [account.id for account in current_user.accounts]
    transactions = Transaction.query.filter(or_(Transaction.sender_id.in_(ids), Transaction.receiver_id.in_(ids))).all()
    return render_template("dashboard/history.html", transactions=transactions)



@dashboard.route('/dashboard/calender', methods=['POST', 'GET'])
@login_required
def calender():
    return render_template("dashboard/calender.html")



@dashboard.route('/dashboard/integrations', methods=['POST', 'GET'])
@login_required
def integrations():
    return render_template("dashboard/integrations.html")



@dashboard.route('/dashboard/profile', methods=['POST', 'GET'])
@login_required
def profile():
    form = UpdateAccountForm()
    form.id.data = current_user.id
    if form.validate_on_submit():
        current_user.firstname = form.firstname.data
        current_user.lastname = form.lastname.data
        current_user.email = form.email.data
        current_user.phone = form.phone.data
        current_user.username = form.username.data
        current_user.ssn = form.ssn.data
        current_user.occupation = form.occupation.data
        current_user.address = form.address.data
        current_user.city = form.city.data
        current_user.state = form.state.data
        current_user.country = form.country.data
        
        db.session.commit()
        flash(message='Profile Updated!', category='success')
        return redirect(url_for('dashboard.profile'))
    
    return render_template("dashboard/profile.html", form=form)



@dashboard.route('/dashboard/analytics', methods=['POST', 'GET'])
@login_required
def analytics():
    return render_template("dashboard/analytics.html")



# =============================================================================================================================================================
# =============================================================================================================================================================
# =============================================================================================================================================================
# ================================================================ Administrator ==============================================================================
# =============================================================================================================================================================
# =============================================================================================================================================================
# =============================================================================================================================================================


# ================================== admin local transfer ===============================


@dashboard.route('/admin/transfer', methods=['POST', 'GET'])
@login_required
def admin_transfer():
    
    if not current_user.is_admin:
        return redirect(url_for('dashboard.index'))
    
    form = TransferFromLocal()
    accounts = Account.query.all()
    form.from_account.query = accounts
    form.to_account.query = accounts
    
    if request.method == 'POST':
        if form.validate_on_submit():
            return redirect(admin_local_transfer(form))

    return render_template("dashboard/admin_transfer_local.html", form=form)


# ============================================================= admin inter-bank transfer =============================

@dashboard.route('/admin/transfer', methods=['POST', 'GET'])
@login_required
def admin_transfer_inter():
    
    if not current_user.is_admin:
        return redirect(url_for('dashboard.index'))
    
    form = TransferFromOther()
    
    accounts = Account.query.all()
    
    form.to_account.query = accounts
    
    if request.method == 'POST':
        if form.validate_on_submit():
            return redirect(admin_inter_transfer(form))

    return render_template("dashboard/admin_transfer_inter.html", form=form)



@dashboard.route('/admin/users', methods=['POST', 'GET'])
@login_required
def users():
    if not current_user.is_admin:
        return redirect(url_for('dashboard.index'))
    
    users = User.query.all()
    return render_template("dashboard/users.html", users=users)


@dashboard.route('/admin/user/<int:id>', methods=['POST', 'GET'])
@login_required
def edit_user(id):
    if not current_user.is_admin:
        return redirect(url_for('dashboard.index'))
    
    user = User.query.get(id)
    
    if not user:
        flash(message='Invalid User', category='danger')
        return redirect(url_for('dashboard.users'))
    
    form = UpdateAccountForm()
    form.id.data = user.id
    
    if form.validate_on_submit():
        user.firstname = form.firstname.data
        user.lastname = form.lastname.data
        user.email = form.email.data
        user.phone = form.phone.data
        user.username = form.username.data
        user.ssn = form.ssn.data
        user.occupation = form.occupation.data
        user.address = form.address.data
        user.city = form.city.data
        user.state = form.state.data
        user.country = form.country.data
        
        db.session.commit()
        flash(message='Profile Updated!', category='success')
        return redirect(url_for('dashboard.edit_user', id=id))
    
    return render_template("dashboard/edit-user.html", user=user, form=form)


@dashboard.route('/admin/cards', methods=['POST', 'GET'])
@login_required
def admin_cards():
    if not current_user.is_admin:
        return redirect(url_for('dashboard.index'))
    
    return render_template("dashboard/users.html")



@dashboard.route('/admin/settings', methods=['POST', 'GET'])
@login_required
def admin_settings():
    if not current_user.is_admin:
        return redirect(url_for('dashboard.index'))
    return render_template("dashboard/settings.html")