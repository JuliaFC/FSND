#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from datetime import datetime
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
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
    image_link = db.Column(db.String(240))
    facebook_link = db.Column(db.String(120))
    show = db.relationship('Show', backref=db.backref('Venue', lazy=True))


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
    facebook_link = db.Column(db.String(120))
    image_link = db.Column(db.String(240))
    website = db.Column(db.String(120))
    show = db.relationship('Show', backref=db.backref('Artist', lazy=True))


class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
    start_time = db.Column(db.DateTime)

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
  recent_artists = Artist.query.order_by(db.desc(Artist.id)).limit(10)
  recent_venues = Venue.query.order_by(db.desc(Venue.id)).limit(10)
  return render_template('pages/home.html', artists=recent_artists, venues=recent_venues)

def format_boolean(value):
    # Formatting value to the expected type
    # since WTForm will output a True as 'y'
    # and False as None
    return value == 'y'

#----------------------------------------------------------------------------#
#  Venues
#----------------------------------------------------------------------------#

@app.route('/venues')
def venues():
  areas = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state)
  data = [{
    "city": a.city,
    "state": a.state,
    "venues": [{
      "name": v.name,
      } for v in db.session.query(Venue.id, Venue.name).filter_by(city=a.city, state=a.state).all()]
    } for a in areas]
  s = Show.query

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
    venue = Venue.query.get(venue_id)

    upcoming_shows =  Show.query.filter(Show.start_time > datetime.utcnow(), Show.venue_id==venue_id).all()
    past_shows =  Show.query.filter(Show.start_time < datetime.utcnow(), Show.venue_id==venue_id).all()

    upcoming_shows_data = [{
      "venue_id": s.venue_id,
      "venue_name": Venue.query.get(s.venue_id).name,
      "artist_id": s.artist_id,
      "artist_name": Artist.query.get(s.artist_id).name,
      "artist_image_link": Artist.query.get(s.artist_id).image_link,
      "start_time": s.start_time
      } for s in upcoming_shows]

    past_shows_data = [{
      "venue_id": s.venue_id,
      "venue_name": Venue.query.get(s.venue_id).name,
      "artist_id": s.artist_id,
      "artist_name": Artist.query.get(s.artist_id).name,
      "artist_image_link": Artist.query.get(s.artist_id).image_link,
      "start_time": s.start_time.strftime("%m/%d/%Y, %H:%M")
      } for s in past_shows]

    data = {
        "id": venue.id,
        "name": venue.name,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "genres": venue.genres,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "facebook_link": venue.facebook_link,
        "upcoming_shows_count": len(upcoming_shows_data),
        "upcoming_shows": upcoming_shows_data,
        "past_shows_count": len(past_shows_data),
        "past_shows": past_shows_data
    }

  except SQLAlchemyError as e:
    data = {}
    error = str(e.__dict__['orig'])
    print(error)
    flash('Venue could not be found!')
  finally:
    return render_template('pages/show_venue.html', venue=data)

#----------------------------------------------------------------------------#
#  Create Venue
#----------------------------------------------------------------------------#

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

    seeking_talent = format_boolean(seeking_talent)

    venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, seeking_talent=seeking_talent, seeking_description=seeking_description, facebook_link= facebook_link, image_link=image_link)
    db.session.add(venue)
    db.session.commit()

    # on successful db insert, flash success
    flash('Venue ' + request.form.get('name') + ' was successfully listed!')
  except SQLAlchemyError as e:
    db.session.rollback()
    flash('An error occurred. Venue ' + name + ' could not be listed.')
  finally:
    db.session.close()
    return redirect(url_for('index'))

@app.route('/venues/<int:venue_id>/delete', methods=['DELETE', 'POST'])
def delete_venue(venue_id):
  try:
    venue = db.session.query(Venue).filter(Venue.id==venue_id).first()
    shows = db.session.query(Show).filter(Show.venue_id==venue_id).all()

    for show in shows:
      db.session.delete(show)
      
    db.session.delete(venue)

    db.session.commit()
    flash('Venue ' + venue.name + ' deleted successfully!')
  except SQLAlchemyError as e:
    error = str(e.__dict__['orig'])
    print(error)
    db.session.rollback()
    flash('An error occurred. Venue could not be deleted.')
  finally:
    db.session.close()
    return redirect(url_for('index'))



#----------------------------------------------------------------------------#
#  Artists
#----------------------------------------------------------------------------#
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


@app.route('/search', methods=['POST'])
def search_location():
  search_term = request.form.get('search_term', '')
  tokens = search_term.split(',')

  city = tokens[0]
  state = tokens[1][1:] # removes the extra space between the comma and the state
  
  artists = Artist.query.filter(Artist.city.ilike(f'%{city}%'), Artist.state.ilike(f'%{state}%')).all()
  count = len(artists) 
  artists_response={
    "count": count,
    "data": [{
      "id": a.id,
      "name": a.name,
    } for a in artists]
  }

  venues = Venue.query.filter(Venue.city.ilike(f'%{city}%'), Venue.state.ilike(f'%{state}%')).all()
  count = len(venues)
  venues_response={
    "count": count,
    "data": [{
      "id": v.id,
      "name": v.name,
    } for v in venues]
  }
  return render_template('pages/search_location.html', artists=artists_response, venues=venues_response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  
  try:
    artist = Artist.query.get(artist_id)
    upcoming_shows =  Show.query.filter(Show.start_time > datetime.utcnow(), Show.artist_id==artist_id).all()
    past_shows =  Show.query.filter(Show.start_time < datetime.utcnow(), Show.artist_id==artist_id).all()

    upcoming_shows_data = [{
      "venue_id": s.venue_id,
      "venue_name": Venue.query.get(s.venue_id).name,
      "venue_image_link": Venue.query.get(s.venue_id).image_link,
      "artist_id": s.artist_id,
      "artist_name": Artist.query.get(s.artist_id).name,
      "start_time": s.start_time.strftime("%m/%d/%Y, %H:%M")
      } for s in upcoming_shows]

    past_shows_data = [{
      "venue_id": s.venue_id,
      "venue_name": Venue.query.get(s.venue_id).name,
      "venue_image_link": Venue.query.get(s.venue_id).image_link,
      "artist_id": s.artist_id,
      "artist_name": Artist.query.get(s.artist_id).name,
      "start_time": s.start_time.strftime("%m/%d/%Y, %H:%M")
      } for s in past_shows]

    data = {
      "id": artist.id,
      "name": artist.name,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "genres": artist.genres,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "facebook_link": artist.facebook_link,
      "website": artist.website,
      "upcoming_shows_count": len(upcoming_shows_data),
      "upcoming_shows": upcoming_shows_data,
      "past_shows_count": len(past_shows_data),
      "past_shows": past_shows_data
    }

  except SQLAlchemyError as e:
    data = {}
    flash('Artist could not be found!')
  finally:
    return render_template('pages/show_artist.html', artist=data)

@app.route('/artists/<int:artist_id>/delete', methods=['DELETE', 'POST'])
def delete_artist(artist_id):
  try:
    artist = db.session.query(Artist).filter(Artist.id==artist_id).first()
    shows = db.session.query(Show).filter(Show.artist_id==artist_id).all()

    for show in shows:
      db.session.delete(show)
      
    db.session.delete(artist)

    db.session.commit()
    flash('Artist ' + artist.name + ' deleted successfully!')
  except SQLAlchemyError as e:
    error = str(e.__dict__['orig'])
    print(error)
    db.session.rollback()
    flash('An error occurred. Artist could not be deleted.')
  finally:
    db.session.close()
    return redirect(url_for('index'))
#----------------------------------------------------------------------------#
#  Update
#----------------------------------------------------------------------------#

def change(current, new):
  if current != new and new:
    return new
  return current

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  try:
    artist = Artist.query.get(artist_id)
  except SQLAlchemyError as e:
    flash('Artist could not be found!')
  finally:
    return render_template('forms/edit_artist.html', form=form, artist=artist)

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
    artist.website = change(artist.website, request.form.get('website'))
    artist.facebook_link = change(artist.facebook_link, request.form.get('facebook_link'))
    artist.image_link = change(artist.image_link, request.form.get('image_link'))
    
    db.session.commit()
  except SQLAlchemyError as e:
    error = str(e.__dict__['orig'])
    print(error)
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  try:
    venue = Venue.query.get(venue_id)
  except SQLAlchemyError as e:
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

    seeking_talent = format_boolean(request.form.get('seeking_talent'))
    venue.seeking_talent = change(venue.seeking_talent, seeking_talent)
    venue.seeking_description = change(venue.seeking_description, request.form.get('seeking_description'))
    venue.facebook_link = change(venue.facebook_link, request.form.get('facebook_link'))
    venue.image_link = change(venue.facebook_link, request.form.get('image_link'))

    db.session.commit()
  except SQLAlchemyError as e:
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#----------------------------------------------------------------------------#
#  Create Artist
#----------------------------------------------------------------------------#

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
    website = request.form.get('website', '')
    facebook_link = request.form.get('facebook_link')
    image_link = request.form.get('image_link')

    seeking_venue = format_boolean(seeking_venue)
    
    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, seeking_venue=seeking_venue, seeking_description=seeking_description, website=website, facebook_link= facebook_link, image_link=image_link)

    db.session.add(artist)
    db.session.commit()

    # on successful db insert, flash success
    flash('Artist ' + request.form.get('name') + ' was successfully listed!')
  except SQLAlchemyError as e:
    db.session.rollback()
    flash('An error occurred. Artist ' + name + ' could not be listed.')
  finally:
    db.session.close()
    return redirect(url_for('index'))

#----------------------------------------------------------------------------#
#  Shows
#----------------------------------------------------------------------------#

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  shows = db.session.query(Show).all()
  data = [{
    "venue_id": s.venue_id,
    "venue_name": Venue.query.get(s.venue_id).name,
    "artist_id": s.artist_id,
    "artist_name": Artist.query.get(s.artist_id).name,
    "artist_image_link": Artist.query.get(s.artist_id).image_link,
    "start_time": s.start_time.strftime("%m/%d/%Y, %H:%M")
    } for s in shows]

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
 
  try:
    artist_id = request.form.get('artist_id')
    venue_id = request.form.get('venue_id')
    start_time = request.form.get('start_time')

    show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)

    db.session.add(show)
    db.session.commit()

    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except SQLAlchemyError as e:
    error = str(e.__dict__['orig'])
    print(error)
    db.session.rollback()
    flash('Could not list show.')  
  finally:
    db.session.close()
    return redirect(url_for('index'))

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
