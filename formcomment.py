#!/usr/bin/env python
import os
import jinja2
import webapp2
from datetime import datetime

from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import ndb
import event as e
from createevent import Event
from google.appengine.api import channel
from google.appengine.api import users

template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.getcwd()))

class Comment(ndb.Model):
    """Models an individual Comment entry for posting to nosql database."""
    event = ndb.StringProperty()
    user = ndb.StringProperty()
    content = ndb.TextProperty()

class CreateCommentHandler(webapp2.RequestHandler):
    """
    Generates the create comment page
    """
    def get(self):
        upload_url = blobstore.create_upload_url('/imageupload')
        template = template_env.get_template('templates/commentform.html')
        login_url = users.create_login_url(self.request.url)
        logout_url = users.create_logout_url(self.request.url)

        user=users.get_current_user()
        context = {
            'user': user,
            'login_url': login_url,
            'logout_url': logout_url,
            'upload_url': upload_url}

        self.response.write(template.render(context))

class CommentHandler(blobstore_handlers.BlobstoreUploadHandler):
    """
    Creates a comment from the Comment model above and the input fields at /createcomment.
    This should only be accessible by the delegates. Comment is preformatted in the same
    manner as message to save on format time later.

    image upload does not work, blob store produced a lot of bugs which weren't present in
    video serving. This requires investigation.
    """
    def post(self):
        upload_files = self.get_uploads('image')
        try:
            blob_info = upload_files[0]
        except:
            blob_info = None
        print blob_info

        comment = Comment()

        user=users.get_current_user()
        time=datetime.now()
        # newcomment = '!!comment!!<span>' + str(user) + '<br />' + self.request.get('comment') + '<br />' + time.strftime('%H:%m') + '<br /></span>'
        newcomment='!!comment!!<span class="media"><a class="media-left" href="#"></a><div class="media-body"><h4 class="media-heading">'+str(user)+'</h4>'+self.request.get('comment')+'<div>'+time.strftime('%H:%M')+'</div></div></span>'
        if blob_info:
            newcomment.replace('</div></div></span>','<image src=' +  + '></image></div></div></span>')

        events = Event.query().fetch()
        eventkey=None
        for event in events:
            print event
            if str(event.name) == self.request.get('event'):
                 eventkey = event.key.urlsafe()

        comment.event = eventkey
        comment.content = newcomment
        if blob_info:
            comment.image = blob_info.key()
        comment.put()
        print "put"
        print eventkey

        if eventkey:
            clientquery = e.ChatUser.query(e.ChatUser.event == eventkey)
            clients=clientquery.fetch()
            for client in clients:
                channel.send_message(client.uuid, newcomment)

app = webapp2.WSGIApplication([
    ('/createcomment', CreateCommentHandler),
    ('/imageupload', CommentHandler)
], debug=True)