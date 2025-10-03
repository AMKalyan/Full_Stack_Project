from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime, timedelta
import os
import hashlib
from functools import wraps

app = Flask(__name__, template_folder='project/templates', static_folder='project/static')
app.secret_key = 'your_secret_key'  # Required for flash messages and sessions
app.permanent_session_lifetime = timedelta(days=7)  # Session lasts for 7 days

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Hash password function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Ensure the instance folder exists
if not os.path.exists('instance'):
    os.makedirs('instance')

# Database setup
DATABASE = 'instance/tasks.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Create users table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create tasks table with user_id and completed status
    conn.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        priority TEXT,
        completed BOOLEAN DEFAULT 0,
        user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if not username or not password or not email:
            flash('All fields are required!', 'error')
            return redirect(url_for('register'))
        
        # Hash the password
        hashed_password = hash_password(password)
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                        (username, hashed_password, email))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists!', 'error')
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required!', 'error')
            return redirect(url_for('login'))
        
        # Hash the password
        hashed_password = hash_password(password)
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                          (username, hashed_password)).fetchone()
        conn.close()
        
        if user:
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/')
@app.route('/filter/<priority>')
def index(priority=None):
    if 'user_id' in session:
        conn = get_db_connection()
        
        # Apply priority filter if specified
        if priority and priority in ['low', 'medium', 'high']:
            tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ? AND priority = ? ORDER BY created_at DESC',
                               (session['user_id'], priority)).fetchall()
        else:
            tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ? ORDER BY created_at DESC',
                               (session['user_id'],)).fetchall()
        
        conn.close()
        return render_template('index.html', tasks=tasks, active_page='home', current_filter=priority)
    else:
        return redirect(url_for('login'))

@app.route('/active')
@login_required
def active_tasks():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ? AND completed = 0 ORDER BY created_at DESC',
                       (session['user_id'],)).fetchall()
    conn.close()
    return render_template('tasks.html', tasks=tasks, active_page='active', page_title='Active Tasks')

@app.route('/completed')
@login_required
def completed_tasks():
    conn = get_db_connection()
    tasks = conn.execute('SELECT * FROM tasks WHERE user_id = ? AND completed = 1 ORDER BY created_at DESC',
                       (session['user_id'],)).fetchall()
    conn.close()
    return render_template('tasks.html', tasks=tasks, active_page='completed', page_title='Completed Tasks')

@app.route('/submit', methods=['POST'])
@login_required
def submit():
    title = request.form.get('title')
    description = request.form.get('description')
    due_date = request.form.get('due_date')
    priority = request.form.get('priority')
    
    if not title:
        flash('Title is required!', 'error')
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    conn.execute('INSERT INTO tasks (title, description, due_date, priority, user_id) VALUES (?, ?, ?, ?, ?)',
                (title, description, due_date, priority, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Task added successfully!', 'success')
    return redirect(url_for('success'))

@app.route('/success')
@login_required
def success():
    return render_template('success.html')

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tasks WHERE id = ? AND user_id = ?', (id, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/complete/<int:id>', methods=['POST'])
@login_required
def complete_task(id):
    conn = get_db_connection()
    task = conn.execute('SELECT completed FROM tasks WHERE id = ? AND user_id = ?', 
                      (id, session['user_id'])).fetchone()
    
    if task:
        new_status = 0 if task['completed'] else 1
        conn.execute('UPDATE tasks SET completed = ? WHERE id = ? AND user_id = ?', 
                    (new_status, id, session['user_id']))
        conn.commit()
        status_text = 'incomplete' if new_status == 0 else 'complete'
        flash(f'Task marked as {status_text}!', 'success')
    else:
        flash('Task not found!', 'error')
    
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)