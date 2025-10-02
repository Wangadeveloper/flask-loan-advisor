from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,TextAreaField,IntegerField,SelectField,FileField,SubmitField,ValidationError
from wtforms.validators import DataRequired,Length,Email,EqualTo
from loan.models import User


class LoanRiskAssessmentForm(FlaskForm):
    loan_amount = IntegerField('Loan Amount', validators=[DataRequired()])
    monthly_income = IntegerField('Monthly Income', validators=[DataRequired()])
    business_type = SelectField('Business Type', choices=[('Sole Proprietorship', 'Sole Proprietorship'),
                                                          ('Partnership', 'Partnership'),
                                                          ('Corporation', 'Corporation')],
                               validators=[DataRequired()])
    business_level = SelectField('Business Level', choices=[('Startup', 'Startup'),
                                                            ('Growing', 'Growing'),
                                                            ('Established', 'Established')],
                                 validators=[DataRequired()])
    repayment_period = IntegerField('Repayment Period (in months)', validators=[DataRequired()])
    business_desc=TextAreaField('bussiness_desc',validators=[DataRequired()])
    submit = SubmitField('Submit Assessment')


class PeerToPeerAdviceForm(FlaskForm):
    username= StringField('username', validators=[DataRequired()])
    message = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

class FinalizeLoanApplicationForm(FlaskForm):
    submit = SubmitField('Finalize Application')

class RegistrationForm(FlaskForm):
    username=StringField('username',validators=[DataRequired(),Length(min=2,max=50)])
    email=StringField('email',validators=[DataRequired(),Length(min=2,max=50)])
    password=PasswordField('password',validators=[DataRequired()])
    confirm_password=PasswordField('confirm password',validators=[DataRequired(),EqualTo('password')])
    submit=SubmitField('submit')
    def validate_username(self,username):
        user=User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('username already taken')
        
    def validate_email(self,email):
        user=User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('email already taken')

class UserProfileForm(FlaskForm):
    full_names=StringField('full_names',validators=[DataRequired(),Length(min=2,max=50)])
    email=StringField('email',validators=[DataRequired(),Length(min=2,max=50)])
    monthly_income = IntegerField('Monthly Income', validators=[DataRequired()])
    business_type = SelectField('Business Type', choices=[('Sole Proprietorship', 'Sole Proprietorship'),
                                                          ('Partnership', 'Partnership'),
                                                          ('Corporation', 'Corporation')],
                               validators=[DataRequired()])
    business_level = SelectField('Business Level', choices=[('Startup', 'Startup'),
                                                            ('Growing', 'Growing'),
                                                            ('Established', 'Established')],
                                 validators=[DataRequired()])
    phone=StringField('phone',validators=[DataRequired(),Length(min=2,max=50)])
    country=StringField('country',validators=[DataRequired(),Length(min=2,max=50)])
    location=StringField('location',validators=[DataRequired(),Length(min=2,max=50)])
    submit = SubmitField('save profile')



class LoginForm(FlaskForm):
    email=StringField('email',validators=[DataRequired(),Length(min=2,max=20)])
    password=PasswordField('password',validators=[DataRequired()])
    submit=SubmitField('submit')
    
