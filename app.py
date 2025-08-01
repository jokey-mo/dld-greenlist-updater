from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import hashlib
import os
from bs4 import BeautifulSoup
import re
import pandas as pd
from io import BytesIO
import bcrypt

# Date parsing utility
def parse_date_string(date_str):
    """Parse various date formats and return a standardized YYYY-MM-DD string"""
    if not date_str or date_str.strip() == '':
        return ''
    
    date_str = date_str.strip()
    
    # Common date patterns
    patterns = [
        r'(\d{1,2})/(\d{1,2})/(\d{4})',     # DD/MM/YYYY or MM/DD/YYYY
        r'(\d{1,2})-(\d{1,2})-(\d{4})',     # DD-MM-YYYY or MM-DD-YYYY
        r'(\d{4})-(\d{1,2})-(\d{1,2})',     # YYYY-MM-DD
        r'(\d{1,2})\.(\d{1,2})\.(\d{4})',   # DD.MM.YYYY
        r'(\d{1,2}) (\d{1,2}) (\d{4})',     # DD MM YYYY
    ]
    
    for pattern in patterns:
        match = re.match(pattern, date_str)
        if match:
            part1, part2, part3 = match.groups()
            
            # If it's already YYYY-MM-DD format
            if len(part1) == 4:
                year, month, day = part1, part2, part3
            else:
                # Assume DD/MM/YYYY format (common in UAE)
                day, month, year = part1, part2, part3
            
            try:
                # Validate and format the date
                day = int(day)
                month = int(month)
                year = int(year)
                
                # Basic validation
                if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                    return f"{year:04d}-{month:02d}-{day:02d}"
            except (ValueError, TypeError):
                continue
    
    # If no pattern matches, return the original string
    return date_str

def format_date_for_display(date_str):
    """Convert YYYY-MM-DD format to DD/MM/YYYY for display"""
    if not date_str or date_str.strip() == '':
        return ''
    
    try:
        # Parse YYYY-MM-DD format
        match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
        if match:
            year, month, day = match.groups()
            return f"{int(day):02d}/{int(month):02d}/{year}"
    except:
        pass
    
    # If parsing fails, return original
    return date_str

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///clients.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Add custom template filter for date formatting
@app.template_filter('format_date')
def format_date_filter(date_str):
    return format_date_for_display(date_str)

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=True)  # For admin approval workflow
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    clients = db.relationship('Client', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Admin Settings model for system configuration
class AdminSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_name = db.Column(db.String(50), unique=True, nullable=False)
    setting_value = db.Column(db.String(200), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def get_setting(name, default_value=''):
        setting = AdminSettings.query.filter_by(setting_name=name).first()
        return setting.setting_value if setting else default_value

    @staticmethod
    def set_setting(name, value):
        setting = AdminSettings.query.filter_by(setting_name=name).first()
        if setting:
            setting.setting_value = value
            setting.updated_at = datetime.utcnow()
        else:
            setting = AdminSettings(setting_name=name, setting_value=value)
            db.session.add(setting)
        db.session.commit()

# Client model (renamed from Broker)
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    service_category = db.Column(db.String(100))
    property_type = db.Column(db.Text)
    area = db.Column(db.Text)
    budget = db.Column(db.String(50))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    subscription_end_date = db.Column(db.String(20))
    data_hash = db.Column(db.String(64), nullable=False)  # For detecting duplicates within user's data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_new = db.Column(db.Boolean, default=True)  # To track new entries in latest upload

    def __repr__(self):
        return f'<Client {self.name}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class HTMLParser:
    @staticmethod
    def clean_text(text):
        """Clean and normalize text data"""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove any "View More" button text
        text = re.sub(r'View More', '', text).strip()
        return text

    @staticmethod
    def generate_hash(client_data, user_id):
        """Generate a hash for the client data to detect duplicates within user's data"""
        # Create a string combining key fields for hashing (including user_id for isolation)
        hash_string = f"{user_id}{client_data['name']}{client_data['email']}{client_data['phone']}"
        return hashlib.sha256(hash_string.encode()).hexdigest()

    @staticmethod
    def parse_html_file(file_path):
        """Parse the HTML file and extract client data"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        clients = []
        
        # Find the table with client data
        table = soup.find('table', class_='table-striped')
        if not table:
            return clients
        
        tbody = table.find('tbody')
        if not tbody:
            return clients
        
        rows = tbody.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 8:  # Ensure we have all required columns
                client_data = {
                    'name': HTMLParser.clean_text(cells[0].get_text()),
                    'service_category': HTMLParser.clean_text(cells[1].get_text()),
                    'property_type': HTMLParser.clean_text(cells[2].get_text()),
                    'area': HTMLParser.clean_text(cells[3].get_text()),
                    'budget': HTMLParser.clean_text(cells[4].get_text()),
                    'email': HTMLParser.clean_text(cells[5].get_text()),
                    'phone': HTMLParser.clean_text(cells[6].get_text()),
                    'subscription_end_date': parse_date_string(HTMLParser.clean_text(cells[7].get_text()))
                }
                
                clients.append(client_data)
        
        return clients

class ClientService:
    @staticmethod
    def process_html_upload(file_path, user_id):
        """Process uploaded HTML file and update database for specific user"""
        clients_data = HTMLParser.parse_html_file(file_path)
        
        # Mark all existing records for this user as not new
        db.session.query(Client).filter_by(user_id=user_id).update({Client.is_new: False})
        
        new_clients = []
        updated_clients = []
        processed_hashes = set()  # Track hashes within this upload to handle duplicates
        
        for client_data in clients_data:
            # Generate hash with user_id for isolation
            client_data['data_hash'] = HTMLParser.generate_hash(client_data, user_id)
            current_hash = client_data['data_hash']
            
            # Check if we've already processed this exact client in this upload
            if current_hash in processed_hashes:
                # Skip duplicate within the same upload
                continue
                
            processed_hashes.add(current_hash)
            
            existing_client = Client.query.filter_by(
                data_hash=current_hash, 
                user_id=user_id
            ).first()
            
            if existing_client:
                # Update existing client
                for key, value in client_data.items():
                    if key != 'data_hash':
                        setattr(existing_client, key, value)
                existing_client.updated_at = datetime.utcnow()
                existing_client.is_new = False  # Not new since it existed before
                updated_clients.append(existing_client)
            else:
                # Create new client
                new_client = Client(user_id=user_id, **client_data)
                new_client.is_new = True
                db.session.add(new_client)
                new_clients.append(new_client)
        
        db.session.commit()
        
        return {
            'new_count': len(new_clients),
            'updated_count': len(updated_clients),
            'total_processed': len(clients_data),
            'duplicates_skipped': len(clients_data) - len(new_clients) - len(updated_clients),
            'new_clients': new_clients
        }

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            # Check if user is approved
            if not user.is_approved:
                flash('Your account is pending admin approval. Please wait for approval.', 'warning')
                return render_template('login.html', title='Sign In', form=form)
            
            login_user(user)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            return redirect(next_page)
        flash('Invalid email or password', 'error')
    return render_template('login.html', title='Sign In', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Check if registration is enabled
    registration_enabled = AdminSettings.get_setting('registration_enabled', 'true') == 'true'
    if not registration_enabled:
        flash('Registration is currently disabled. Please contact an administrator.', 'error')
        return redirect(url_for('login'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if this is the first user (will be admin)
        user_count = User.query.count()
        is_first_user = user_count == 0
        
        # Check if admin approval is required
        requires_approval = AdminSettings.get_setting('require_admin_approval', 'false') == 'true'
        
        user = User(
            name=form.name.data, 
            email=form.email.data,
            is_admin=is_first_user,  # First user becomes admin
            is_approved=is_first_user or not requires_approval  # First user or no approval required
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        if is_first_user:
            # Initialize default admin settings
            AdminSettings.set_setting('registration_enabled', 'true')
            AdminSettings.set_setting('require_admin_approval', 'false')
            flash('Congratulations! You are now registered as the system administrator!', 'success')
        elif requires_approval:
            flash('Registration successful! Your account is pending admin approval.', 'info')
        else:
            flash('Congratulations, you are now registered!', 'success')
        
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Main routes
@app.route('/')
@login_required
def index():
    """Main dashboard"""
    total_clients = Client.query.filter_by(user_id=current_user.id).count()
    new_clients = Client.query.filter_by(user_id=current_user.id, is_new=True).all()
    recent_clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.created_at.desc()).limit(10).all()
    
    return render_template('index.html', 
                         total_clients=total_clients,
                         new_clients=new_clients,
                         recent_clients=recent_clients)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    """Upload and process HTML file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and file.filename.lower().endswith('.html'):
            # Create uploads directory if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            # Save file
            filename = f"clients_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            try:
                # Process the file
                result = ClientService.process_html_upload(file_path, current_user.id)
                
                message_parts = [
                    f"File processed successfully!",
                    f"New clients: {result['new_count']}",
                    f"Updated: {result['updated_count']}"
                ]
                
                if result.get('duplicates_skipped', 0) > 0:
                    message_parts.append(f"Duplicates skipped: {result['duplicates_skipped']}")
                    
                message_parts.append(f"Total processed: {result['total_processed']}")
                
                flash(' | '.join(message_parts), 'success')
                
                return redirect(url_for('view_new_clients'))
                
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Please upload an HTML file', 'error')
    
    return render_template('upload.html')

@app.route('/clients')
@login_required
def list_clients():
    """List all clients with pagination, sorting, and filtering"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    service_categories = request.args.getlist('service_category')
    status_filter = request.args.get('status', '')
    
    query = Client.query.filter_by(user_id=current_user.id)
    
    # Search filter
    if search:
        query = query.filter(
            db.or_(
                Client.name.contains(search),
                Client.email.contains(search),
                Client.phone.contains(search),
                Client.area.contains(search)
            )
        )
    
    # Service category filter
    if service_categories:
        query = query.filter(Client.service_category.in_(service_categories))
    
    # Status filter
    if status_filter:
        if status_filter == 'new':
            query = query.filter(Client.is_new == True)
        elif status_filter == 'existing':
            query = query.filter(Client.is_new == False)
    
    # Sorting
    if sort_by == 'subscription_end_date':
        # Handle date sorting for subscription_end_date stored as string in YYYY-MM-DD format
        if sort_order == 'asc':
            # Put empty dates at the end for ascending order
            query = query.order_by(
                db.case(
                    (Client.subscription_end_date == '', '9999-12-31'),
                    (Client.subscription_end_date.is_(None), '9999-12-31'),
                    else_=Client.subscription_end_date
                ).asc()
            )
        else:
            # Put empty dates at the end for descending order
            query = query.order_by(
                db.case(
                    (Client.subscription_end_date == '', '0000-01-01'),
                    (Client.subscription_end_date.is_(None), '0000-01-01'),
                    else_=Client.subscription_end_date
                ).desc()
            )
    else:
        sort_column = getattr(Client, sort_by, Client.created_at)
        if sort_order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
    
    clients = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get all unique service categories for the filter dropdown
    all_categories = db.session.query(Client.service_category).filter_by(user_id=current_user.id).distinct().all()
    available_categories = [cat[0] for cat in all_categories if cat[0]]
    
    return render_template('clients.html', 
                         clients=clients, 
                         search=search,
                         sort_by=sort_by,
                         sort_order=sort_order,
                         service_categories=service_categories,
                         status_filter=status_filter,
                         available_categories=available_categories)

@app.route('/new-clients')
@login_required
def view_new_clients():
    """View only new clients from the latest upload"""
    new_clients = Client.query.filter_by(user_id=current_user.id, is_new=True).order_by(Client.created_at.desc()).all()
    return render_template('new_clients.html', clients=new_clients)

@app.route('/mark-reviewed')
@login_required
def mark_reviewed():
    """Mark new clients as reviewed (not new anymore)"""
    Client.query.filter_by(user_id=current_user.id, is_new=True).update({Client.is_new: False})
    db.session.commit()
    flash('All new clients marked as reviewed', 'success')
    return redirect(url_for('index'))

@app.route('/api/clients')
@login_required
def api_clients():
    """API endpoint for clients data"""
    clients = Client.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': client.id,
        'name': client.name,
        'email': client.email,
        'phone': client.phone,
        'area': client.area,
        'created_at': client.created_at.isoformat(),
        'is_new': client.is_new
    } for client in clients])

@app.route('/export')
@login_required
def export_data():
    """Export clients data as Excel file with current filters and sorting"""
    # Get the same parameters as list_clients
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    service_categories = request.args.getlist('service_category')
    status_filter = request.args.get('status', '')
    
    query = Client.query.filter_by(user_id=current_user.id)
    
    # Apply the same filters as in list_clients
    if search:
        query = query.filter(
            db.or_(
                Client.name.contains(search),
                Client.email.contains(search),
                Client.phone.contains(search),
                Client.area.contains(search)
            )
        )
    
    if service_categories:
        query = query.filter(Client.service_category.in_(service_categories))
    
    if status_filter:
        if status_filter == 'new':
            query = query.filter(Client.is_new == True)
        elif status_filter == 'existing':
            query = query.filter(Client.is_new == False)
    
    # Apply the same sorting as in list_clients
    if sort_by == 'subscription_end_date':
        # Handle date sorting for subscription_end_date stored as string in YYYY-MM-DD format
        if sort_order == 'asc':
            # Put empty dates at the end for ascending order
            query = query.order_by(
                db.case(
                    (Client.subscription_end_date == '', '9999-12-31'),
                    (Client.subscription_end_date.is_(None), '9999-12-31'),
                    else_=Client.subscription_end_date
                ).asc()
            )
        else:
            # Put empty dates at the end for descending order
            query = query.order_by(
                db.case(
                    (Client.subscription_end_date == '', '0000-01-01'),
                    (Client.subscription_end_date.is_(None), '0000-01-01'),
                    else_=Client.subscription_end_date
                ).desc()
            )
    else:
        sort_column = getattr(Client, sort_by, Client.created_at)
        if sort_order == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
    
    clients = query.all()
    
    # Create DataFrame
    data = []
    for client in clients:
        data.append({
            'Name': client.name,
            'Service Category': client.service_category,
            'Property Type': client.property_type,
            'Area': client.area,
            'Budget (AED)': client.budget,
            'Email': client.email,
            'Phone': client.phone,
            'Subscription End Date': client.subscription_end_date,
            'Created Date': client.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Updated Date': client.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Status': 'New' if client.is_new else 'Existing'
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Clients', index=False)
        
        # Auto-adjust columns width
        worksheet = writer.sheets['Clients']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    
    from flask import Response
    filename = f"clients_export_{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@app.route('/export-json')
@login_required
def export_json():
    """Export clients data as JSON"""
    clients = Client.query.filter_by(user_id=current_user.id).all()
    data = []
    
    for client in clients:
        data.append({
            'name': client.name,
            'service_category': client.service_category,
            'property_type': client.property_type,
            'area': client.area,
            'budget': client.budget,
            'email': client.email,
            'phone': client.phone,
            'subscription_end_date': client.subscription_end_date,
            'created_at': client.created_at.isoformat(),
            'updated_at': client.updated_at.isoformat(),
            'is_new': client.is_new
        })
    
    response = jsonify(data)
    filename = f'clients_export_{current_user.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response

# Import fix for url_parse
from urllib.parse import urlparse as url_parse

# Admin routes
def admin_required(f):
    """Decorator to require admin access"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    """Admin dashboard"""
    total_users = User.query.count()
    pending_users = User.query.filter_by(is_approved=False).count()
    admin_users = User.query.filter_by(is_admin=True).count()
    
    # Get system settings
    registration_enabled = AdminSettings.get_setting('registration_enabled', 'true') == 'true'
    require_approval = AdminSettings.get_setting('require_admin_approval', 'false') == 'true'
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         pending_users=pending_users,
                         admin_users=admin_users,
                         registration_enabled=registration_enabled,
                         require_approval=require_approval,
                         recent_users=recent_users)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    
    query = User.query
    
    if status == 'pending':
        query = query.filter_by(is_approved=False)
    elif status == 'approved':
        query = query.filter_by(is_approved=True)
    elif status == 'admin':
        query = query.filter_by(is_admin=True)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, status=status)

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_settings():
    """Admin settings"""
    if request.method == 'POST':
        # Update registration settings
        registration_enabled = 'registration_enabled' in request.form
        require_approval = 'require_admin_approval' in request.form
        
        AdminSettings.set_setting('registration_enabled', 'true' if registration_enabled else 'false')
        AdminSettings.set_setting('require_admin_approval', 'true' if require_approval else 'false')
        
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    # Get current settings
    registration_enabled = AdminSettings.get_setting('registration_enabled', 'true') == 'true'
    require_approval = AdminSettings.get_setting('require_admin_approval', 'false') == 'true'
    
    return render_template('admin/settings.html',
                         registration_enabled=registration_enabled,
                         require_approval=require_approval)

@app.route('/admin/approve-user/<int:user_id>')
@login_required
@admin_required
def approve_user(user_id):
    """Approve a user"""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot modify your own approval status.', 'error')
    else:
        user.is_approved = True
        db.session.commit()
        flash(f'User {user.name} has been approved.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/reject-user/<int:user_id>')
@login_required
@admin_required
def reject_user(user_id):
    """Reject/unapprove a user"""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot modify your own approval status.', 'error')
    else:
        user.is_approved = False
        db.session.commit()
        flash(f'User {user.name} has been rejected.', 'warning')
    return redirect(url_for('admin_users'))

@app.route('/admin/make-admin/<int:user_id>')
@login_required
@admin_required
def make_admin(user_id):
    """Make a user admin"""
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    user.is_approved = True  # Admins are automatically approved
    db.session.commit()
    flash(f'User {user.name} is now an administrator.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/remove-admin/<int:user_id>')
@login_required
@admin_required
def remove_admin(user_id):
    """Remove admin privileges"""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot remove your own admin privileges.', 'error')
    else:
        user.is_admin = False
        db.session.commit()
        flash(f'Admin privileges removed from {user.name}.', 'warning')
    return redirect(url_for('admin_users'))

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user account"""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
    else:
        user_name = user.name
        db.session.delete(user)
        db.session.commit()
        flash(f'User account {user_name} has been deleted.', 'success')
    return redirect(url_for('admin_users'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
