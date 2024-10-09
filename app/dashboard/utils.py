from app import bcrypt, db, mail
from uuid import uuid4
from functools import cache
from flask import flash, url_for, render_template
from flask_login import current_user
from flask_mail import Message
from app.models import Account, Transaction, ExternalParty, Notification
import json
from datetime import datetime
from threading import Thread

@cache
def get_countries() -> list[str]:
    with open(file='app/countries.json', mode='r') as f:
            countries = json.loads(f.read())
            return [country['country'] for country in countries]


@cache
def get_banks() -> list[str]:
    with open(file='app/banknames.json', mode='r') as f:
            banks = json.loads(f.read())
            return list(banks.values())
        


def get_mail_details(sender_account=None, receiver_account=None):
    if sender_account:
        sender = {
            'name': sender_account.owner.firstname +' ' + sender_account.owner.lastname,
            'account_number': sender_account.account_number,
            'balance': sender_account.balance,
            'email': sender_account.owner.email
        }
    else:
        sender = None
    
    
    if receiver_account:
        receiver = {
            'name': receiver_account.owner.firstname +' ' + receiver_account.owner.lastname,
            'account_number': receiver_account.account_number,
            'balance': receiver_account.balance,
            'email': receiver_account.owner.email
        }
    else:
        receiver = None
    return sender, receiver


def transaction_message(form, reference, sender_account=None, receiver_account=None):
    
    if sender_account:
        debit = f"""
            You transferred ${form.amount.data} to {receiver_account.owner.lastname} {receiver_account.owner.firstname} </br>
            <h4>Transaction Details</h4>
            <b>Amount:</b> ${form.amount.data} </br>
            <b>From:</b> {sender_account.type} - {sender_account.account_number.replace(sender_account.account_number[2:7],'XXX')}  </br>
            <b>To:</b> {receiver_account.type} - {receiver_account.account_number.replace(receiver_account.account_number[2:7], 'XXX')} </br>
            <b>Balance:</b> ${sender_account.balance} </br>
            <b>Transaction Reference:</b> {reference.replace(reference[5:13], 'XXXX')} </br>
            <b>Date:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}</br>
        """
        
    if receiver_account:
        credit = f"""
            You Received ${form.amount.data} from {sender_account.owner.lastname} {sender_account.owner.firstname} </br>
            <h4>Transaction Details</h4>
            <b>Amount:</b> ${form.amount.data} </br>
            <b>From:</b> {sender_account.owner.lastname} {sender_account.owner.firstname} </br>
            <b>To:</b> {receiver_account.type} - {receiver_account.account_number.replace(receiver_account.account_number[2:7], 'XXX')} </br>
            <b>Balance:</b> ${receiver_account.balance} </br>
            <b>Transaction Reference:</b> {reference.replace(reference[5:13], 'XXXX')} </br>
            <b>Date:</b> {datetime.now().strftime('%d-%m-%Y %H:%M')}  </br>
        """

    return debit, credit

        
def admin_local_transfer(form):
    sender_account = Account.query.get(form.from_account.data.id)
    receiver_account = Account.query.get(form.to_account.data.id)
    
    if not sender_account:
        flash(message='Sender account is invalid', category='danger')
        return url_for('dashboard.admin_transfer')
    
    if not receiver_account:
        flash(message='Sender account is invalid', category='danger')
        return url_for('dashboard.admin_transfer')
    
    sender_account.balance -= form.amount.data
    receiver_account.balance += form.amount.data
    
    reference = str(uuid4())
    transaction = Transaction(
        amount=form.amount.data,
        reference=reference,
        sender_id=sender_account.id,
        receiver_id=receiver_account.id,
        sender=sender_account,
        receiver=receiver_account,
        sender_balance = sender_account.balance,                          
        receiver_balance = receiver_account.balance   
        )
    
    db.session.add(transaction)
    
    title = form.amount.data
    
    credit, debit = transaction_message(form=form, reference=reference, sender_account=sender_account, receiver_account=receiver_account)
    
    sender_notification = Notification(title=title, message=debit, sub_title='Debit', user_id=sender_account.owner.id, owner=sender_account.owner)
    db.session.add(sender_notification)
    
    
    receiver_notification = Notification(title=title, message=credit, sub_title='Credit', user_id=receiver_account.owner.id, owner=receiver_account.owner)
    db.session.add(receiver_notification)
    
    
    db.session.commit()
    
    sender, receiver = get_mail_details(sender_account=sender_account, receiver_account=receiver_account)
    
    
    # Debit email for sender
    to = [sender['email']]
    subject = 'Debit Alert'
    html = render_template('email/debit-alert.html', sender=sender, receiver=receiver, amount=transaction.amount, date=transaction.date)
    
    msg = Message(subject=subject, recipients=to, html=html)
    thread1 = Thread(target=mail.send, args=(msg))
    thread1.start()
    
    
    # credit email for receiver
    to = [receiver['email']]
    subject = 'Credit Alert'
    html = render_template('email/credit-alert.html', sender=sender, receiver=receiver, amount=transaction.amount, date=transaction.date)
    
    msg = Message(subject=subject, recipients=to, html=html)
    thread2 = Thread(target=mail.send, args=(msg))
    thread2.start()
    
    
    flash(message='Transfer Successful', category='success')
    return url_for('dashboard.admin_transfer')


# ================================================Admin Inter Bank transfer ====================================


def admin_inter_transfer(form):
    receiver_account = Account.query.get(account_number = form.to_account.data.id)
    
    if not receiver_account:
        flash(message='Receiver account is invalid', category='danger')
        return url_for('dashboard.admin_transfer_inter')
    
    receiver_account.balance = receiver_account.balance + form.amount.data
    
    reference = str(uuid4())
    sender = ExternalParty(
        firstname=form.firstname.data,
        lastname=form.lastname.data,
        country=form.country.data,
        bank=form.bank.data,
        account_number=form.account_number.data
    )
    
    db.session.add(sender)
    
    transaction = Transaction(
        amount=form.amount.data,
        reference=reference,
        receiver_id=receiver_account.id,
        external_sender_id=sender.id,
        receiver=receiver_account,
        external_sender=sender,
        receiver_balance = receiver_account.balance,
        )
    db.session.add(transaction)
    
    title = form.amount.data
    
    _, credit = transaction_message(form=form, reference=reference, receiver_account=receiver_account)
    
    receiver_notification = Notification(title=title, message=credit, sub_title='Credit', user_id=receiver_account.owner.id, owner=receiver_account.owner)
    db.session.add(receiver_notification)
    
    
    db.session.commit()
    
    _, receiver = get_mail_details(receiver_account=receiver_account)
    
    
    # credit email for receiver
    to = [receiver['email']]
    subject = 'Credit Alert'
    html = render_template('email/credit-alert.html', sender=sender, receiver=receiver, amount=transaction.amount, date=transaction.date)
    
    msg = Message(subject=subject, recipients=to, html=html)
    
    thread1 = Thread(target=mail.send, args=(msg))
    thread1.start()
    
    
    flash(message='Transfer Completed', category='success')
    return url_for('dashboard.admin_transfer_inter')


# ========================================================= Customer Local Transfer =======================================
        
def local_transfer(form):
    sender_account = Account.query.get(form.account.data.id)
    receiver_account = Account.query.filter_by(account_number = form.account_number.data).first()
        
    if not sender_account:
        flash(message='Account selected is invalid', category='danger')
        return url_for('dashboard.transfer')
    
    if not receiver_account:
        flash(message='Incorrect account number, Please confirm and try again', category='danger')
        return url_for('dashboard.transfer')
    
    if not bcrypt.check_password_hash(sender_account.pin, form.pin.data):
        flash(message='Incorrect Pin', category='danger')
        return url_for('dashboard.transfer')
    
    sender_account.balance = sender_account.balance - form.amount.data
    receiver_account.balance = receiver_account.balance + form.amount.data   
    
    reference = str(uuid4())
    transaction = Transaction(
        amount=form.amount.data,
        reference=reference,
        sender_id=sender_account.id,
        receiver_id=receiver_account.id,
        sender=sender_account,
        receiver=receiver_account,
        sender_balance = sender_account.balance,                          
        receiver_balance = receiver_account.balance   
        )
    db.session.add(transaction)
    
    title = form.amount.data
    
    debit, credit = transaction_message(sender_account=sender_account, receiver_account=receiver_account, form=form, reference=reference)
    
    sender_notification = Notification(title=title, message=debit, sub_title='Debit', user_id=sender_account.owner.id, owner=sender_account.owner)
    receiver_notification = Notification(title=title, message=credit, sub_title='Credit', user_id=receiver_account.owner.id, owner=receiver_account.owner)
    
    db.session.add(sender_notification)    
    db.session.add(receiver_notification)
    
    
    db.session.commit()
    
    sender, receiver = get_mail_details(sender_account=sender_account, receiver_account=receiver_account)
    
    
    # Debit email for sender
    to = [sender['email']]
    subject = 'Debit Alert'
    html = render_template('email/debit-alert.html', sender=sender, receiver=receiver, amount=transaction.amount, date=transaction.date)
    
    msg = Message(subject=subject, recipients=to, html=html)
    thread1 = Thread(target=mail.send, args=(msg))
    thread1.start()
    
    
    # credit email for receiver
    to = [receiver['email']]
    subject = 'Credit Alert'
    html = render_template('email/credit-alert.html', sender=sender, receiver=receiver, amount=transaction.amount, date=transaction.date)
    
    msg = Message(subject=subject, recipients=to, html=html)
    
    thread2 = Thread(target=mail.send, args=(msg))
    thread2.start()
    
    flash(message='Transfer Completed', category='success')
    return url_for('dashboard.transfer')
        
        
def inter_transfer(form):
    account = Account.query.get(form.account.data.id)
        
    if not account:
        flash(message='Invalid Account', category='danger')
        return url_for('dashboard.transfer')
    
    if not bcrypt.check_password_hash(account.pin, form.pin.data):
        flash(message='Incorrect Pin', category='danger')
        return url_for('dashboard.transfer')
    
    account.balance = account.balance + form.amount.data
    reference = str(uuid4())
    receiver = ExternalParty(
        firstname=form.firstname.data,
        lastname=form.lastname.data,
        country=form.country.data,
        bank=form.bank.data,
        account_number=form.account_number.data
    )
    
    db.session.add(receiver)
    
    transaction = Transaction(
        amount=form.amount.data,
        reference=reference,
        sender_id=account.id,
        external_receiver_id=receiver.id,
        sender=account,
        external_receiver=receiver,
        sender_balance = account.balance,
        )
    db.session.add(transaction)
    
    title = form.amount.data
    
    credit, _ = transaction_message(form=form, reference=reference, sender_account=form.account)
    
    sender_notification = Notification(title=title, message=credit, sub_title='Debit', user_id=account.owner.id, owner=account.owner)
    db.session.add(sender_notification)    
    
    db.session.commit()
    
    sender, _ = get_mail_details(sender_account=account)
    
    
    # Debit email for sender
    to = [sender['email']]
    subject = 'Debit Alert'
    html = render_template('email/debit-alert.html', sender=sender, receiver=receiver, amount=transaction.amount, date=transaction.date)
    
    msg = Message(subject=subject, recipients=to, html=html)
    
    thread2 = Thread(target=mail.send, args=(msg))
    thread2.start()
    
    
    flash(message='Transfer Completed', category='success')
    return url_for('dashboard.transfer')

    