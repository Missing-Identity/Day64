import os
from flask import Flask, render_template, redirect, url_for, request, session
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from dotenv import load_dotenv
import json

load_dotenv()

# create the extension
db = SQLAlchemy()
# create the app
app = Flask(__name__)
# configure the SQLite database, relative to the app instance folder
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies-collection.db"
# initialize the app with the extension
db.init_app(app)

Bootstrap5(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False, unique=True)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250))
    rating = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    review = db.Column(db.String(250))
    img_url = db.Column(db.String(250), nullable=False)

class MovieTitleForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Search Movies')


with app.app_context():
    db.create_all()

# Define the headers for The Movie Database API
MOVIE_DB_HEADERS = {
    "accept": "application/json",
    "Authorization": os.environ.get('API_TOKEN'),
}


@app.route("/create_db", methods=["GET"])
def create_db():
    db.create_all()
    return "Database created successfully!"

@app.route("/")
def home():
    # Fetch movies sorted by rating in descending order
    movie_list = Movie.query.order_by(Movie.rating.desc()).all()
    return render_template('index.html', movies=movie_list)


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = MovieTitleForm()
    if form.validate_on_submit():
        title = form.title.data
        response = requests.get(f"{os.environ.get('API_URL')}/search/movie", 
                                params={"query": title},
                                headers=MOVIE_DB_HEADERS)
        session['movie_data'] = [{ 'id': movie['id'], 'title': movie['title']} for movie in response.json().get('results', [])]
        return redirect(url_for('select_movie'))
    return render_template('add.html', form=form)

@app.route("/edit/<int:movie_id>", methods=["GET", "POST"])
def edit_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if request.method == "POST":
        movie.rating = request.form.get('rating', type=float)
        movie.review = request.form.get('review', "")
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie)

@app.route("/delete/<int:movie_id>", methods=["GET", "POST"])
def delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/select", methods=["GET", "POST"])
def select_movie():
    movie_data = session.get('movie_data', [])
    return render_template('select.html', movie_data=movie_data)

@app.route("/movie_details/<int:movie_id>", methods=["GET"])
def movie_details(movie_id):
    response = requests.get(f"{os.environ.get('API_URL')}/movie/{movie_id}", 
                            params={"api_key": os.environ.get('API_KEY')},
                            headers=MOVIE_DB_HEADERS)
    movie_details = response.json()

    # Create a new movie object and add it to the database
    new_movie = Movie(
        title=movie_details['title'],
        year=movie_details['release_date'].split("-")[0],  # Extract year from release_date
        description=movie_details['overview'],
        img_url=f"https://image.tmdb.org/t/p/w500{movie_details['poster_path']}",
        rating=0,  # Default rating
        ranking=0,  # Default ranking
        review=""   # Default review
    )
    db.session.add(new_movie)
    db.session.commit()

    # Redirect to the edit page for the newly added movie
    return redirect(url_for('edit_movie', movie_id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
