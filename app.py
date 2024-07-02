from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_sqlalchemy import SQLAlchemy
import requests
import bcrypt
from config import Config
from models import db, User, Movie

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    db.create_all()

TMDB_API_KEY = 'd13ffdf8612413fdf3d97ca7c527606b'

@app.route('/recommendations', methods=['POST'])
def get_recommendations():
    movie_name = request.form['movie_name']
    tmdb_url = f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_name}'
    
    try:
        response = requests.get(tmdb_url)
        response.raise_for_status()
        data = response.json()

        recommendations = []
        poster_urls = []
        if 'results' in data:
            for movie in data['results']:
                recommendations.append(movie['title'])
                if 'poster_path' in movie:
                    poster_urls.append(f"https://image.tmdb.org/t/p/w500{movie['poster_path']}")
                else:
                    poster_urls.append(None)

        return render_template('recom.html', recommendations=recommendations, poster_urls=poster_urls)
    
    except requests.exceptions.RequestException as e:
        error_message = "Error fetching data from TMDB API. Please try again later."
        return render_template('recom.html', error=error_message)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        image = request.files['image']
        genre = request.form['genre']
        director = request.form['director']
        release_date = request.form['release_date']
        rating = float(request.form['rating'])

        image.save(f'static/images/{image.filename}')

        new_movie = Movie(title=title, description=description, image=image.filename,
                          genre=genre, director=director, release_date=release_date, rating=rating)
        db.session.add(new_movie)
        db.session.commit()

        flash('Movie added successfully!', 'success')
        return redirect(url_for('show_movie', movie_id=new_movie.id))

    return render_template('admin.html')

@app.route('/movie/<int:movie_id>')
def show_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return render_template('movie.html', movie=movie)

@app.route('/movie')
def all_movies():
    movies = Movie.query.all()
    return render_template('movie_list.html', movies=movies)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/details')
def details():
    return render_template('movie-details.html')

@app.route('/recommd')
def recommd():
    return render_template('recom.html')

@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        email = session['email']
        user = User.query.filter_by(email=email).first()
        return render_template('dashboard.html', user=user)
    return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('You have been logged out.', 'success')
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
            session['email'] = user.email
            flash('Login successful!', 'success')
            return redirect('/')
        else:
            flash('Invalid email or password', 'error')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already exists', 'error')
            return render_template('register.html')

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect('/login')

    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
