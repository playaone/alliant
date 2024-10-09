from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from datetime import datetime
from dotenv import load_dotenv, dotenv_values
from flask_mail import Mail


# instantiate modules and packages
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
login_manager  = LoginManager()
mail = Mail()


# setup login paramenters
login_manager.login_view = 'dashboard.login'

# load env values
load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    
    # app configurations
    config = dotenv_values()
    
    app.config.from_mapping(config)
    
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 3600
    }
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USE_TLS'] =False
    
    # initialize required packages and modules
    db.init_app(app)
    migrate.init_app(app, db=db, render_as_batch=True)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # app global variables
    @app.context_processor
    def site_globals():
        return {
            'sitename': 'Alliant',
            'sitelink': 'alliant.com',
            'site_email': 'support@alliant.com',
            'site_phone': '+1(321) 325-5363',
            'site_address': '5824 Kishwaukee Rd Rockford, IL 61109 USA.',
            'email_images': 'https://images.alliantmobilebanking.com',
            'date': datetime.now()
        }

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('public/404.html')
        
    
    # import blueprints
    
    from app.public.routes import public
    from app.dashboard.routes import dashboard
    
    # register blueprints
    app.register_blueprint(public)
    app.register_blueprint(dashboard)
    
    
    # create db
    
    with app.app_context():
        db.create_all()
    
    
    # run db create_all
    
    return app