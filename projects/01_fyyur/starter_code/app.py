#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(240))
    image_link = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(240))
    image_link = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  res = 'bar'
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en_US')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')

def validate_boolean(value):
    # Formatting value to the expected type
    # since WTForm will output a True as 'y'
    # and False as None
    return value == 'y'
#----------------------------------------------------------------------------#
#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  areas = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state)
  data = [{
    "city": a.city,
    "state": a.state,
    "venues": [{
      "id": v.id,
      "name": v.name,
      "num_upcoming_shows": 0
      } for v in db.session.query(Venue.id, Venue.name).filter_by(city=a.city, state=a.state).all()]
    } for a in areas]

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')

  res = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  count = len(res)

  response={
    "count": count,
    "data": [{
      "id": r.id,
      "name": r.name,
      "num_upcoming_shows": 0,
    } for r in res]
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  try:
    data = Venue.query.get(venue_id)
  except:
    flash('Venue could not be found!')
  finally:
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # called upon submitting the new venue listing form

  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    address = request.form.get('address')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    seeking_talent = request.form.get('seeking_talent')
    seeking_description = request.form.get('seeking_description', '')
    facebook_link = request.form.get('facebook_link')
    image_link = request.form.get('image_link')

    seeking_talent = validate_boolean(seeking_talent)

    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, seeking_talent=seeking_talent, seeking_description=seeking_description, facebook_link= facebook_link, image_link=image_link)
    db.session.add(venue)
    db.session.commit()

    # on successful db insert, flash success
    flash('Venue ' + request.form.get('name') + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + name + ' could not be listed.')
  finally:
    db.session.close()
    return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/delete', methods=['DELETE', 'POST'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete();
    db.session.commit()
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + name + ' could not be deleted.')
  finally:
    db.session.close()
    return redirect(url_for('index'))


  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect th user to the homepage


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  artists = db.session.query(Artist.id, Artist.name).all()
  data = [{
    "id": a.id,
    "name": a.name
    } for a in artists]
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')

  res = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  count = len(res)

  response={
    "count": count,
    "data": [{
      "id": r.id,
      "name": r.name,
      "num_upcoming_shows": 0,
    } for r in res]
  }
  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/tags/search', methods=['POST'])
def search_tags():
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.genres.any(search_term)).all()
  count = len(artists)
  
  artists_response={
    "count": count,
    "data": [{
      "id": a.id,
      "name": a.name,
      "num_upcoming_shows": 0,
    } for a in artists]
  }

  venues = Venue.query.filter(Venue.genres.any(search_term)).all()
  count = len(venues)
  venues_response={
    "count": count,
    "data": [{
      "id": v.id,
      "name": v.name,
      "num_upcoming_shows": 0,
    } for v in venues]
  }
  return render_template('pages/search_tags.html', artists=artists_response, venues=venues_response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id

  try:
    data = Artist.query.get(artist_id)
  except:
    flash('Artist could not be found!')
  finally:
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  try:
    artist = Artist.query.get(artist_id)
  except:
    flash('Artist could not be found!')
  finally:
    return render_template('forms/edit_artist.html', form=form, artist=artist)


def change(current, new):
  if current != new and new:
    return new
  return current

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    artist = Artist.query.get(artist_id)

    artist.name = change(artist.name, request.form.get('name'))
    artist.city = change(artist.city, request.form.get('city'))
    artist.state = change(artist.state, request.form.get('state'))
    artist.phone = change(artist.phone, request.form.get('phone'))
    artist.genres = change(artist.genres, request.form.getlist('genres'))
    artist.seeking_venue = change(artist.seeking_venue, request.form.get('seeking_venue'))
    artist.seeking_description = change(artist.seeking_description, request.form.get('seeking_description'))
    artist.facebook_link = change(artist.facebook_link, request.form.get('facebook_link'))

    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  try:
    venue = Venue.query.get(venue_id)
  except:
    flash('Venue could not be found!')
  finally:
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    venue = Venue.query.get(venue_id)

    venue.name = change(venue.name, request.form.get('name'))
    venue.city = change(venue.city, request.form.get('city'))
    venue.state = change(venue.state, request.form.get('state'))
    venue.address = change(venue.address, request.form.get('address'))
    venue.phone = change(venue.phone, request.form.get('phone'))
    venue.genres = change(venue.genres, request.form.getlist('genres'))

    seeking_talent = validate_boolean(request.form.get('seeking_talent'))
    venue.seeking_talent = change(venue.seeking_talent, seeking_talent)
    venue.seeking_description = change(venue.seeking_description, request.form.get('seeking_description'))
    venue.facebook_link = change(venue.facebook_link, request.form.get('facebook_link'))

    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form

  try:
    name = request.form.get('name')
    city = request.form.get('city')
    state = request.form.get('state')
    phone = request.form.get('phone')
    genres = request.form.getlist('genres')
    seeking_venue = request.form.get('seeking_venue')
    seeking_description = request.form.get('seeking_description', '')
    facebook_link = request.form.get('facebook_link')
    image_link = request.form.get('image_link')

    seeking_venue = validate_boolean(seeking_venue)
    
    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, seeking_venue=seeking_venue, seeking_description=seeking_description, facebook_link= facebook_link, image_link=image_link)

    db.session.add(artist)
    db.session.commit()

    # on successful db insert, flash success
    flash('Artist ' + request.form.get('name') + ' was successfully listed!')
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + name + ' could not be listed.')
    print(sys.exc.info)
  finally:
    db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21T21:30:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15T23:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-01T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-08T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-15T20:00:00.000Z"
  }]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
