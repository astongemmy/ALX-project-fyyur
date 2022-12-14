#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import os
import re
import datetime
from datetime import datetime
import dateutil.parser
import babel
from flask import Flask, abort, jsonify, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import desc, or_
from models import db, Artist, Venue, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

migrate = Migrate(app, db)

# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:postgres@localhost:5432/fyyur"

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
# Models have been moved to models.py and imported as above

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  # date = dateutil.parser.parse(value)
	if isinstance(value, str):
		date = dateutil.parser.parse(value)
	else:
		date = value
		
	if format == 'full':
		format="EEEE MMMM, d, y 'at' h:mma"
	elif format == 'medium':
		format="EE MM, dd, y h:mma"
	elif format == 'timeonly':
		format="h:mma"
	return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Custom utils
#----------------------------------------------------------------------------#

# Checks if show is past or upcoming
def isUpcomingShow(start_time):
  current_time = datetime.now()
  return start_time > current_time

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
	data = {
		'artists': Artist.query.order_by(desc('id')).limit(10).all(),
		'venues': Venue.query.order_by(desc('id')).limit(10).all()
	}
	return render_template('pages/home.html', data=data)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
	venues = Venue.query.order_by('city').all()
	
	data = []	
	area_list = []
	
	for venue in venues: area_list.append({ 'city': venue.city, 'state': venue.state	})

	area_list = list({ v['state']: v for v in area_list }.values())
	
	for area in area_list:
		venue_list = []
		for venue in venues:
			if (venue.city == area['city']) and (venue.state == area['state']):
				venue_list.append({
					'id': venue.id,
					'name': venue.name,
					'num_upcoming_shows': Show.query.filter(isUpcomingShow(Show.start_time)).filter(Show.venue_id == venue.id).count()
				})
		
		data.append({
			**area,
			'venues': venue_list
		})

	# data=[{
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "venues": [{
  #     "id": 1,
  #     "name": "The Musical Hop",
  #     "num_upcoming_shows": 0,
  #   }, {
  #     "id": 3,
  #     "name": "Park Square Live Music & Coffee",
  #     "num_upcoming_shows": 1,
  #   }]
  # }, {
  #   "city": "New York",
  #   "state": "NY",
  #   "venues": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   }]
  # }]
	return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
	search_term = request.form.get('search_term', '').strip()
	venues = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()

	venue_list = []

	for venue in venues:
		venue_list.append({
			'id': venue.id,
			'name': venue.name,
			'num_upcoming_shows': Show.query.filter(isUpcomingShow(Show.start_time)).filter(Show.venue_id == venue.id).count()
		})

	response = {
		'count': len(venues),
		'data': venue_list
	}
  # response={
  #   "count": 1,
  #   "data": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   }]
  # }
	return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id	
	venue = Venue.query.get(venue_id)
	
	if not venue: return redirect(url_for('index'))
	
	venue_data = {
		'id': venue.id,
		'name': venue.name,
		'genres': venue.genres,
		'address': venue.address,
		'city': venue.city,
		'state': venue.state,
		'phone': venue.phone.international,
		'website': venue.website_link,
		'facebook_link': venue.facebook_link,
		'seeking_talent': venue.seeking_talent,
		'seeking_description': venue.seeking_description,
		'image_link': venue.image_link,
	}

	data = {
		**venue_data,
		'past_shows': [],
		'upcoming_shows': [],
		'past_shows_count': 0,
    'upcoming_shows_count': 0
	}

	for show in venue.shows:
		show_dict = {
			'artist_id': show.artist_id,
			'artist_name': show.artist.name,
			'artist_image_link': show.artist.image_link,
			'start_time': show.start_time
		}

		if isUpcomingShow(show.start_time):
			data['upcoming_shows'].append(show_dict)
		else:
			data['past_shows'].append(show_dict)
	
	data['upcoming_shows_count'] = len(data['upcoming_shows'])

	# data1={
  #   "id": 1,
  #   "name": "The Musical Hop",
  #   "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
  #   "address": "1015 Folsom Street",
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "123-123-1234",
  #   "website": "https://www.themusicalhop.com",
  #   "facebook_link": "https://www.facebook.com/TheMusicalHop",
  #   "seeking_talent": True,
  #   "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
  #   "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
  #   "past_shows": [{
  #     "artist_id": 4,
  #     "artist_name": "Guns N Petals",
  #     "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #     "start_time": "2019-05-21T21:30:00.000Z"
  #   }],
  #   "upcoming_shows": [],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 0,
  # }
  # data2={
  #   "id": 2,
  #   "name": "The Dueling Pianos Bar",
  #   "genres": ["Classical", "R&B", "Hip-Hop"],
  #   "address": "335 Delancey Street",
  #   "city": "New York",
  #   "state": "NY",
  #   "phone": "914-003-1132",
  #   "website": "https://www.theduelingpianos.com",
  #   "facebook_link": "https://www.facebook.com/theduelingpianos",
  #   "seeking_talent": False,
  #   "image_link": "https://images.unsplash.com/photo-1497032205916-ac775f0649ae?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=750&q=80",
  #   "past_shows": [],
  #   "upcoming_shows": [],
  #   "past_shows_count": 0,
  #   "upcoming_shows_count": 0,
  # }
  # data3={
  #   "id": 3,
  #   "name": "Park Square Live Music & Coffee",
  #   "genres": ["Rock n Roll", "Jazz", "Classical", "Folk"],
  #   "address": "34 Whiskey Moore Ave",
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "415-000-1234",
  #   "website": "https://www.parksquarelivemusicandcoffee.com",
  #   "facebook_link": "https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
  #   "seeking_talent": False,
  #   "image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #   "past_shows": [{
  #     "artist_id": 5,
  #     "artist_name": "Matt Quevedo",
  #     "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #     "start_time": "2019-06-15T23:00:00.000Z"
  #   }],
  #   "upcoming_shows": [{
  #     "artist_id": 6,
  #     "artist_name": "The Wild Sax Band",
  #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #     "start_time": "2035-04-01T20:00:00.000Z"
  #   }, {
  #     "artist_id": 6,
  #     "artist_name": "The Wild Sax Band",
  #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #     "start_time": "2035-04-08T20:00:00.000Z"
  #   }, {
  #     "artist_id": 6,
  #     "artist_name": "The Wild Sax Band",
  #     "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #     "start_time": "2035-04-15T20:00:00.000Z"
  #   }],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 1,
  # }
  # data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
	 
	return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
	form = VenueForm(request.form)
	error = False
	
	name = form.name.data.strip()
	city = form.city.data.strip()
	state = form.state.data.strip()
	address = form.address.data.strip()
	phone = form.phone.data
	genres = form.genres.data
	seeking_talent = form.seeking_talent.data
	seeking_description = form.seeking_description.data.strip()
	image_link = form.image_link.data.strip()
	website_link = form.website_link.data.strip()
	facebook_link = form.facebook_link.data.strip()
	
	if not form.validate():
		flash( form.errors )
		return redirect(url_for('create_venue_submission'))
	else:
		try:
			venue = Venue(
				name = name,
				city = city,
				state = state,
				genres = genres,
				address = address,
				phone = phone,
				seeking_talent = seeking_talent,
				seeking_description = seeking_description,
				image_link = image_link,
				website_link = website_link,
				facebook_link = facebook_link
			)

			db.session.add(venue)
			db.session.commit()
		except:
			error = True
			db.session.rollback()
		finally:
			db.session.close()
    
	if error == True:
		# TODO: on unsuccessful db insert, flash an error instead.
		# e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
		# see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
		flash('An error occurred. Venue ' + name + ' could not be listed.')
	else:
		# on successful db insert, flash success
		flash('Venue ' + name + ' was successfully listed!')
	
	return redirect(url_for('index'))
  
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
	venue = Venue.query.get(venue_id)
	
	error = False
	stashed_venue = venue
	
	if venue:
		try:
			db.session.delete(venue)
			db.session.commit()
		except:
			error = True
			db.session.rollback()
		finally:
			db.session.close()
	
	if error == True:
		flash(f'An error occurred Could not delete venue {stashed_venue.name}.')
		abort(500)
	else:
		flash(f'{stashed_venue.name} delete successfully.')
		return jsonify({
			'status': True,
			'Message': stashed_venue.name + ' deleted successfully.',
			'next': '/'
		})

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  # return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
	artists = Artist.query.order_by('name').all()

	data = []

	for artist in artists:
		data.append({
			'id': artist.id,
			'name': artist.name
		})
	
  # data=[{
  #   "id": 4,
  #   "name": "Guns N Petals",
  # }, {
  #   "id": 5,
  #   "name": "Matt Quevedo",
  # }, {
  #   "id": 6,
  #   "name": "The Wild Sax Band",
  # }]
	
	return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
	search_term = request.form.get('search_term', '').strip()
	
	artists = Artist.query.filter(Artist.name.ilike('%' + search_term + '%')).all()
	
	artist_list = []
	
	for artist in artists:
		artist_list.append({
			'id': artist.id,
			'name': artist.name,
			'num_upcoming_shows': Show.query.filter(isUpcomingShow(Show.start_time)).filter(Show.artist_id == artist.id).count()
		})

	response = {
		'count': len(artists),
		'data': artist_list
	}

	# response={
  #   "count": 1,
  #   "data": [{
  #     "id": 4,
  #     "name": "Guns N Petals",
  #     "num_upcoming_shows": 0,
  #   }]
  # }
	return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
	artist = Artist.query.get(artist_id)
	
	if not artist: return redirect(url_for('index'))
	
	artist_data = {
		'id': artist.id,
		'name': artist.name,
		'genres': artist.genres,
		'availability': artist.availability,
		'city': artist.city,
		'state': artist.state,
		'phone': artist.phone.international,
		'website': artist.website_link,
		'facebook_link': artist.facebook_link,
		'seeking_venue': artist.seeking_venue,
		'seeking_description': artist.seeking_description,
		'image_link': artist.image_link,
	}

	data = {
		**artist_data,
		'past_shows': [],
		'upcoming_shows': [],
		'past_shows_count': 0,
    'upcoming_shows_count': 0
	}

	for show in artist.shows:
		show_dict = {
			'venue_id': show.venue_id,
			'venue_name': show.venue.name,
			'venue_image_link': show.venue.image_link,
			'start_time': show.start_time
		}

		if isUpcomingShow(show.start_time):
			data['upcoming_shows'].append(show_dict)
		else:
			data['past_shows'].append(show_dict)
	
	data['upcoming_shows_count'] = len(data['upcoming_shows'])
	
	# data1={
  #   "id": 4,
  #   "name": "Guns N Petals",
  #   "genres": ["Rock n Roll"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "326-123-5000",
  #   "website": "https://www.gunsnpetalsband.com",
  #   "facebook_link": "https://www.facebook.com/GunsNPetals",
  #   "seeking_venue": True,
  #   "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
  #   "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #   "past_shows": [{
  #     "venue_id": 1,
  #     "venue_name": "The Musical Hop",
  #     "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
  #     "start_time": "2019-05-21T21:30:00.000Z"
  #   }],
  #   "upcoming_shows": [],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 0,
  # }
  # data2={
  #   "id": 5,
  #   "name": "Matt Quevedo",
  #   "genres": ["Jazz"],
  #   "city": "New York",
  #   "state": "NY",
  #   "phone": "300-400-5000",
  #   "facebook_link": "https://www.facebook.com/mattquevedo923251523",
  #   "seeking_venue": False,
  #   "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #   "past_shows": [{
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2019-06-15T23:00:00.000Z"
  #   }],
  #   "upcoming_shows": [],
  #   "past_shows_count": 1,
  #   "upcoming_shows_count": 0,
  # }
  # data3={
  #   "id": 6,
  #   "name": "The Wild Sax Band",
  #   "genres": ["Jazz", "Classical"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "432-325-5432",
  #   "seeking_venue": False,
  #   "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "past_shows": [],
  #   "upcoming_shows": [{
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-01T20:00:00.000Z"
  #   }, {
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-08T20:00:00.000Z"
  #   }, {
  #     "venue_id": 3,
  #     "venue_name": "Park Square Live Music & Coffee",
  #     "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
  #     "start_time": "2035-04-15T20:00:00.000Z"
  #   }],
  #   "past_shows_count": 0,
  #   "upcoming_shows_count": 3,
  # }
  # data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
	 
	return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
	artist = Artist.query.get(artist_id)
	
	if not artist: return redirect(url_for('index'))
  
	form = ArtistForm(obj = artist)

	artist = {
		'id': artist.id,
		'name': artist.name,
		'genres': artist.genres,
		'availability': artist.availability,
		'city': artist.city,
		'state': artist.state,
		'phone': artist.phone.international,
		'website_link': artist.website_link,
		'facebook_link': artist.facebook_link,
		'seeking_venue': artist.seeking_venue,
		'seeking_description': artist.seeking_description,
		'image_link': artist.image_link
	}
	
	# artist={
  #   "id": 4,
  #   "name": "Guns N Petals",
  #   "genres": ["Rock n Roll"],
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "326-123-5000",
  #   "website": "https://www.gunsnpetalsband.com",
  #   "facebook_link": "https://www.facebook.com/GunsNPetals",
  #   "seeking_venue": True,
  #   "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
  #   "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80"
  # }
  # TODO: populate form with fields from artist with ID <artist_id>
	
	return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
	form = ArtistForm(request.form)
	error = False
	
	name = form.name.data.strip()
	city = form.city.data.strip()
	state = form.state.data.strip()
	phone = form.phone.data
	genres = form.genres.data
	availability = form.availability.data
	seeking_venue = form.seeking_venue.data
	seeking_description = form.seeking_description.data.strip()
	image_link = form.image_link.data.strip()
	website_link = form.website_link.data.strip()
	facebook_link = form.facebook_link.data.strip()
	
	if not form.validate():
		flash( form.errors )
		return redirect(url_for('edit_artist_submission', artist_id = artist_id))
	else:
		try:
			artist = Artist.query.get(artist_id)

			artist.name = name
			artist.city = city
			artist.state = state
			artist.genres = genres
			artist.availability = availability
			artist.phone = phone
			artist.image_link = image_link
			artist.website_link = website_link
			artist.facebook_link = facebook_link
			artist.seeking_venue = seeking_venue
			artist.seeking_description = seeking_description
			
			db.session.commit()
		except:
			error = True
			db.session.rollback()
		finally:
			db.session.close()
			
	if error == True:
		flash('An error occurred. Artist ' + name + ' could not be updated.')
	else:
		# on successful db update, flash success
		flash('Artist ' + name + ' was successfully updated!')
	
	return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
	venue = Venue.query.get(venue_id)

	if not venue: return redirect(url_for('index'))
  
	form = VenueForm(obj = venue)

	venue = {
		'id': venue.id,
		'name': venue.name,
		'genres': venue.genres,
		'city': venue.city,
		'state': venue.state,
		'address': venue.address,
		'phone': venue.phone.international,
		'website_link': venue.website_link,
		'facebook_link': venue.facebook_link,
		'seeking_talent': venue.seeking_talent,
		'seeking_description': venue.seeking_description,
		'image_link': venue.image_link
	}
  
	# venue={
  #   "id": 1,
  #   "name": "The Musical Hop",
  #   "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
  #   "address": "1015 Folsom Street",
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "phone": "123-123-1234",
  #   "website": "https://www.themusicalhop.com",
  #   "facebook_link": "https://www.facebook.com/TheMusicalHop",
  #   "seeking_talent": True,
  #   "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
  #   "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  # }
	
  # TODO: populate form with values from venue with ID <venue_id>
	return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
	form = VenueForm(request.form)
	error = False

	name = form.name.data.strip()
	city = form.city.data.strip()
	state = form.state.data.strip()
	address = form.address.data.strip()
	phone = form.phone.data
	genres = form.genres.data
	seeking_talent = form.seeking_talent.data
	seeking_description = form.seeking_description.data.strip()
	image_link = form.image_link.data.strip()
	website_link = form.website_link.data.strip()
	facebook_link = form.facebook_link.data.strip()
	
	if not form.validate():
		flash( form.errors )
		return redirect(url_for('edit_venue_submission', artist_id = venue_id))
	else:
		try:
			venue = Venue.query.get(venue_id)

			venue.name = name
			venue.city = city
			venue.state = state
			venue.address = address
			venue.genres = genres
			venue.phone = phone
			venue.image_link = image_link
			venue.website_link = website_link
			venue.facebook_link = facebook_link
			venue.seeking_talent = seeking_talent
			venue.seeking_description = seeking_description
			
			db.session.commit()
		except:
			error = True
			db.session.rollback()
		finally:
			db.session.close()
			
	if error == True:
		flash('An error occurred. Venue ' + name + ' could not be updated.')
	else:
		# on successful db update, flash success
		flash('Venue ' + name + ' was successfully updated!')
	
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
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
	form = ArtistForm(request.form)
	error = False
	
	name = form.name.data.strip()
	city = form.city.data.strip()
	state = form.state.data.strip()
	phone = form.phone.data
	genres = form.genres.data
	availability = form.availability.data
	seeking_venue = form.seeking_venue.data
	seeking_description = form.seeking_description.data.strip()
	image_link = form.image_link.data.strip()
	website_link = form.website_link.data.strip()
	facebook_link = form.facebook_link.data.strip()

	if not form.validate():
		flash( form.errors )
		return redirect(url_for('create_artist_submission'))
	else:
		try:
			artist = Artist(
				name = name,
				city = city,
				state = state,
				phone = phone,
				image_link = image_link,
				facebook_link = facebook_link,
				website_link = website_link,
				genres = genres,
				availability = availability,
				seeking_venue = seeking_venue,
				seeking_description = seeking_description
			)

			db.session.add(artist)
			db.session.commit()
		except:
			error = True
			db.session.rollback()
		finally:
			db.session.close()
    
	if error == True:
		# TODO: on unsuccessful db insert, flash an error instead.
		# e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
		# see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
		flash('An error occurred. Artist ' + name + ' could not be listed.')
		return redirect(url_for('create_artist_submission'))
	else:
		# on successful db insert, flash success
		flash('Artist ' + name + ' was successfully listed!')
		return redirect(url_for('index'))

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
	shows = Show.query.order_by('start_time').all()
	
	data = []
	
	for show in shows:
		# if isUpcomingShow(show.start_time):
		data.append({
			'venue_id': show.venue_id,
			'venue_name': show.venue.name,
			'artist_id': show.artist_id,
			'artist_name': show.artist.name,
			'artist_image_link': show.artist.image_link,
			'start_time': show.start_time
		})
		 
	# data=[{
  #   "venue_id": 1,
  #   "venue_name": "The Musical Hop",
  #   "artist_id": 4,
  #   "artist_name": "Guns N Petals",
  #   "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
  #   "start_time": "2019-05-21T21:30:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 5,
  #   "artist_name": "Matt Quevedo",
  #   "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
  #   "start_time": "2019-06-15T23:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-01T20:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-08T20:00:00.000Z"
  # }, {
  #   "venue_id": 3,
  #   "venue_name": "Park Square Live Music & Coffee",
  #   "artist_id": 6,
  #   "artist_name": "The Wild Sax Band",
  #   "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
  #   "start_time": "2035-04-15T20:00:00.000Z"
  # }]
	return render_template('pages/shows.html', shows=data)

@app.route('/shows/search', methods=['POST'])
def search_shows():
  # TODO: implement shows search with partial string search. Ensuring case-insensitivity.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
	search_term = request.form.get('search_term', '').strip()
	
	shows = Show.query.join(Venue).filter(or_(Venue.name.ilike('%' + search_term +'%'), Venue.city.ilike('%' + search_term +'%'))).join(Artist).filter(or_(Artist.name.ilike('%' + search_term +'%'), Artist.city.ilike('%' + search_term +'%'))).all()
	
	show_list = []

	for show in shows:
		show_list.append({
			'venue_id': show.venue_id,
			'venue_name': show.venue.name,
			'artist_id': show.artist_id,
			'artist_name': show.artist.name,
			'artist_image_link': show.artist.image_link,
			'start_time': show.start_time
		})

	response = {
		'count': len(shows),
		'data': show_list
	}

	# response={
  #   "count": 1,
  #   "data": [{
  #     "id": 4,
  #     "name": "Guns N Petals",
  #     "num_upcoming_shows": 0,
  #   }]
  # }
	return render_template('pages/show.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
	form = ShowForm(request.form)
	error = False
	_message = 'An error occurred! Show could not be listed.'

	artist_id = form.artist_id.data
	venue_id = form.venue_id.data
	start_time = form.start_time.data
	
	intended_start_time = start_time.strftime('%H:%M')

	try:
		artist = Artist.query.get(artist_id)
		venue = Venue.query.get(venue_id)

		if not isUpcomingShow(start_time):
			_message = 'Cannot create show past show!'
			abort(500)

		if not artist or not venue:
			_message = 'Invalid artist or venue ID!. Check and try again.'
			abort(400)

		if artist.availability and (intended_start_time not in artist.availability):
			_message = 'Cannot book artist out of availability time.'
			abort(500)

		for show in artist.shows:
			if show.start_time == start_time:
				_message = 'This artist is already book for ' + format_datetime(start_time) + ' in another venue. Try another start time!'
				abort(500)

		for show in venue.shows:
			if show.start_time == start_time:
				_message = 'This venue is already booked for a show on ' + format_datetime(start_time) + '. Try another venue!'
				abort(500)
				
		show = Show(
			artist_id = artist_id,
			venue_id = venue_id,
			start_time = start_time
		)

		db.session.add(show)
		db.session.commit()
		_message = 'Show was successfully listed!'
	except:
		error = True
		db.session.rollback()
	finally:
		db.session.close()
	
	flash(_message)

	if error == True:
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
		return redirect(url_for('create_show_submission'))
	else:
    # on successful db insert, flash success
		return redirect(url_for('index'))

@app.route('/artists/availability/<int:artist_id>', methods=['POST'])
def get_artist_availability(artist_id):
	artist = Artist.query.get(artist_id)
	
	if not artist: return jsonify({
		'status': False,
		'message': 'Artist not found!',
		'availability': []
	})

	formatted_availability = []

	if artist.availability:
		for time in artist.availability:
			formatted_time = format_datetime(time, 'timeonly')
			formatted_availability.append(formatted_time)

	return jsonify({
		'status': True,
		'message': 'Artist availability returned successfully!',
		'availability': formatted_availability
	})


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
# if __name__ == '__main__':
#   app.run()

# Or specify port manually:
if __name__ == '__main__':
	port = int(os.environ.get('PORT', 3000))
	app.run(host='0.0.0.0', port=port)
