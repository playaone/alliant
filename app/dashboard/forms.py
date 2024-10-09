from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, BooleanField, SubmitField, PasswordField, TelField, SelectField, FloatField, IntegerField, HiddenField
from wtforms.validators import Email, EqualTo, Length, DataRequired, ValidationError
from wtforms_alchemy import QuerySelectField
from app.dashboard.utils import get_countries, get_banks
from app.models import User



class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[Email(), DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


class ForgotPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    token = HiddenField(validators=[DataRequired()])
    submit = SubmitField('Reset')


class SendPasswordTokenForm(FlaskForm):
    email = EmailField('Email', validators=[Email(), DataRequired()])
    submit = SubmitField('Send Link')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError(message='This email address is not registered with us')

class ResetPasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset')


class RegisterForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    lastname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    email = EmailField('Email', validators=[Email(), DataRequired()])
    phone = TelField('Phone number', validators=[DataRequired(), Length(min=10, max=50)])
    ssn = StringField('SSN', validators=[DataRequired(), Length(min=2, max=50)])
    occupation = StringField('Occupation', validators=[DataRequired(), Length(min=2, max=50)])
    address = StringField('Address', validators=[DataRequired(), Length(min=2, max=50)])
    city = StringField('Address', validators=[DataRequired(), Length(min=2, max=50)])
    state = StringField('Address', validators=[DataRequired(), Length(min=2, max=50)])
    country = SelectField('Address', validators=[DataRequired()], choices=get_countries())
    account = SelectField('Account Type', validators=[DataRequired()], choices=['Savings', 'Current', 'Checking'])
    pin = PasswordField('Pin', validators=[DataRequired(), Length(min=4, max=8)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=30)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    agree = BooleanField(validators=[DataRequired(message='You must accept our terms and conditions')])
    submit = SubmitField('Sign Up')
    
    def validate_email(self, email):
        user = User.query.filter_by(email = email.data).first()
        if user:
            raise ValidationError(message='Email address already exists')
        else: 
            return None
    
    def validate_username(self, username):
        user = User.query.filter_by(username = username.data).first()
        if user:
            raise ValidationError(message='Username already exists')
        else: 
            return None
    
    def validate_phone(self, phone):
        user = User.query.filter_by(phone = phone.data).first()
        if user:
            raise ValidationError(message='Phone number already exists')
        else: 
            return None


# transfer to same bank
class TransferLocal(FlaskForm):
    """ 
    Intra bank transfer
    """
    amount = FloatField('Amount', validators=[DataRequired()])
    account_number = IntegerField('Account Number', validators=[DataRequired()])
    remark = StringField('Remark', validators=[DataRequired(), Length(min=2, max=50)])
    account = QuerySelectField('Account', validators=[DataRequired()])
    pin = PasswordField('Pin', validators=[DataRequired()])
    submit = SubmitField('Transfer')
    
    def validate_amount(self, amount):
        if amount.data > self.account.data.balance:
            raise ValidationError(message='Insufficient funds')


# transfer to Other banks
class TransferOther(FlaskForm):
    """ 
    Inter bank transfer
    """
    firstname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    lastname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    routing = StringField('SWIFT/ROUTING NUMBER', validators=[DataRequired(), Length(min=7, max=7)])
    country = SelectField('Country', validators=[DataRequired()], choices=get_countries())  
    bank = SelectField('Bank', validators=[DataRequired()], choices=get_banks())  
    account_number = StringField('Account Number', validators=[DataRequired()])
    account_type = SelectField('Account Type', validators=[DataRequired()], choices=['Savings', 'Current', 'Checking'])
    account = QuerySelectField('Account', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    remark = StringField('Remark', validators=[DataRequired(), Length(min=2, max=50)])
    pin = PasswordField('Pin', validators=[DataRequired()])
    submit = SubmitField('Transfer')
    
    def validate_amount(self, amount):
        if amount.data > self.account.data.balance:
            raise ValidationError(message='Insufficient funds')
        



# transfer to same bank
class TransferFromLocal(FlaskForm):
    """ 
    Intra bank transfer
    """
    amount = FloatField('Amount', validators=[DataRequired()])
    from_account = QuerySelectField('From', validators=[DataRequired()])
    to_account = QuerySelectField('To', validators=[DataRequired()])
    remark = StringField('Remark', validators=[DataRequired(), Length(min=2, max=50)])
    submit = SubmitField('Transfer')
    
    def validate_amount(self, amount):
        if amount.data <= 0:
            raise ValidationError(message='Amount must be greater than zero(0)')
        elif amount.data > self.from_account.data.balance:
            raise ValidationError(message='Insufficient funds')


# transfer from other banks
class TransferFromOther(FlaskForm):
    """ 
    trnasfer from other banks
    """
    
    firstname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    lastname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    routing = StringField('SWIFT/ROUTING NUMBER', validators=[DataRequired(), Length(min=7, max=7)])
    country = SelectField('Country', validators=[DataRequired()], choices=get_countries())  
    bank = SelectField('Bank', validators=[DataRequired()], choices=get_banks())  
    amount = FloatField('Amount', validators=[DataRequired()])
    account_number = IntegerField('Account Number', validators=[DataRequired()])
    account_type = SelectField('Account Type', validators=[DataRequired()], choices=['Savings', 'Current', 'Checking'])
    
    remark = StringField('Remark', validators=[DataRequired(), Length(min=2, max=50)])
    
    amount = FloatField('Amount', validators=[DataRequired()])
    to_account = QuerySelectField('To', validators=[DataRequired()])
    submit = SubmitField('Transfer')
    
    def validate_amount(self, amount):
        if amount.data <= 0:
            raise ValidationError(message='Amount must be greater than zero(0)')
        

class UpdateAccountForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    lastname = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    email = EmailField('Email', validators=[Email(), DataRequired()])
    phone = TelField('Phone number', validators=[DataRequired(), Length(min=10, max=50)])
    ssn = StringField('SSN', validators=[DataRequired(), Length(min=2, max=50)])
    occupation = StringField('Occupation', validators=[DataRequired(), Length(min=2, max=50)])
    address = StringField('Address', validators=[DataRequired(), Length(min=2, max=50)])
    city = StringField('Address', validators=[DataRequired(), Length(min=2, max=50)])
    state = StringField('Address', validators=[DataRequired(), Length(min=2, max=50)])
    country = SelectField('Address', validators=[DataRequired()], choices=get_countries())
    id = HiddenField(validators=[DataRequired()])
    submit = SubmitField('Update')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != self.id.data:
            raise ValidationError(message=f'{email.data} is registered to another account')
    
    
    def validate_phone(self, phone):
        user = User.query.filter_by(phone=phone.data).first()
        if user and user.id != self.id.data:
            raise ValidationError(message=f'{phone.data} is already registered')
    
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user and user.id != self.id.data:
            raise ValidationError(message=f'{username.data} is unavailable')