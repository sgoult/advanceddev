#!/usr/bin/env python
import os
import jinja2
import webapp2
from datetime import datetime

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import ndb
from google.appengine.api import users

DEFAULT_EVENT_NAME="event"

template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.getcwd()))

class Event(ndb.Model):
    """Models an individual event entry for posting to nosql database."""
    name = ndb.StringProperty(indexed=False)
    description = ndb.StringProperty(indexed=False)
    hashtag = ndb.StringProperty(indexed=False)
    whitelist = ndb.TextProperty()
    nobadwords = ndb.BooleanProperty()
    startdatetime = ndb.DateTimeProperty()
    enddatetime = ndb.DateTimeProperty()
    #for streaming the video from the blobstore later
    video = ndb.BlobKeyProperty()

class CreateEventHandler(webapp2.RequestHandler):
    """
    Create event handler, builds the webpage for the post request in EventHandler

    not very interesting, upload url provides blobsore functionality
    """
    def get(self):
        upload_url = blobstore.create_upload_url('/upload')
        template = template_env.get_template('templates/createevent.html')
        login_url = users.create_login_url(self.request.url)
        logout_url = users.create_logout_url(self.request.url)
        user=users.get_current_user()
        context = {
            'user': user,
            'login_url': login_url,
            'logout_url': logout_url,
            'upload_url': upload_url}
        self.response.write(template.render(context))

class EventHandler(blobstore_handlers.BlobstoreUploadHandler):
    """
    Takes the post request from the form above, builds an Event model instance from
    post values then puts into datastore. blob_info contains video file information
    which allows querying of blobstore key.
    """
    def post(self):
        upload_files = self.get_uploads('video')
        blob_info = upload_files[0]

        event = Event()

        event.name=self.request.get('name')
        event.description=self.request.get('description')
        event.hashtag=self.request.get('hashtag')
        event.whitelist=self.request.get('whitelist')
        if self.request.get('nobadwords') == 'True':
            nbw=True
        else:
            nbw=False
        event.nobadwords=nbw
        event.startdatetime=datetime.strptime(self.request.get('startdate'), "%d/%m/%Y %H:%M") #dd/mm/yyyy hh:mm
        event.enddatetime=datetime.strptime(self.request.get('enddate'), "%d/%m/%Y %H:%M")
        event.video=blob_info.key()
        event.put()

        self.redirect('/createevent')


app = webapp2.WSGIApplication([
    ('/createevent', CreateEventHandler),
    ('/upload', EventHandler)
], debug=True)