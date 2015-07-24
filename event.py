#!/usr/bin/env python
import os
import jinja2
import webapp2
import datetime
import uuid

from createevent import Event

from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
import formcomment

client_id = 0

template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.getcwd()))

class Message(ndb.Model):
    """Models an individual message entry for posting to nosql database."""
    content = ndb.StringProperty()
    event = ndb.StringProperty()
    image = ndb.BlobProperty()

class ChatUser(ndb.Model):
    """Models an individual chatuser entry for posting to nosql database."""
    event = ndb.StringProperty()
    username = ndb.StringProperty()
    uuid = ndb.StringProperty()

class EventHandler(webapp2.RequestHandler):
    """
    Handler for main event streaming page and event.html

    event key (read at beginning) defines the event attributes to be
    loaded to the page.

    client id is made global in place of cookies to ensure posting to
    database. This would be resolved in a production release.

    each client that connects to the page is given a unique identifier
    for use with googles channel api. This ensures no message crossover.
    """
    def get(self):
        eventkey = self.request.get('key')
        actualkey = ndb.Key(urlsafe=eventkey)
        event = Event.query(Event.key == actualkey).fetch(1)[0]

        user=users.get_current_user()
        #assigning users for client list in datastore
        global client_id
        #creating unique id
        client_id = str(uuid.uuid1())
        if user:
            #if user is logged in
            chatuser = ChatUser()
            chatuser.event = eventkey
            chatuser.username = user.nickname()
            chatuser.uuid = str(client_id)
            chatuser.put()
            print 'put'
        else:
            #else we don't have a user name for the datastore
            chatuser = ChatUser()
            chatuser.event = eventkey
            chatuser.uuid = str(client_id)
            chatuser.put()
            print 'put'
        #instantiate users access to channel for pushed data (messages and comments)
        channel_token = channel.create_channel(client_id)
        template = template_env.get_template('templates/event.html')

        #login and out urls for the users api, passed to html
        login_url = users.create_login_url(self.request.url)
        logout_url = users.create_logout_url(self.request.url)

        #load the messages and comments prestored in the datastore so that they are
        #up to date with the current event feed
        messages = Message.query(Message.event == eventkey).fetch(500)
        comments = formcomment.Comment.query(formcomment.Comment.event == eventkey).fetch(500)

        context = {
        'user': user,
        'eventkey': eventkey,
        'videokey': event.video,
        'login_url': login_url,
        'logout_url': logout_url,
        'token': channel_token,
        'client_id': client_id,
        'eventdescription': event.description,
        'messages': messages,
        'comments': comments}
        self.response.write(template.render(context))

class MessageHandler(webapp2.RequestHandler):
    """
    Post handler for new messages in the event chat room, recieves the message,
    queries datastore for client ids and uses these with channel to distribute
    to all connected clients.

    Message is also put into datastore for preloading and analyses post video
    stream
    """
    def post(self):

        message = Message()

        eventkey = self.request.get('eventkey')
        message_content = self.request.get('message')
        user = users.get_current_user()
        if not user:
            user = 'Anon'
        time=datetime.datetime.now()

        #preformatting for ease of posting
        message.content = "<span>" + str(user) + ':' + self.request.get('message') + ' - ' + time.strftime('%H:%M') + "</span>"
        message.event = eventkey
        message.put()

        #pushing through channel
        clientquery = ChatUser.query(ChatUser.event == eventkey)
        clients = clientquery.fetch()
        for client in clients:
            channel.send_message(client.uuid, "<span>" + str(user) + ':' + self.request.get('message') + ' - ' + time.strftime('%H:%M') + "</span>")

class VideoHandler(blobstore_handlers.BlobstoreDownloadHandler):
    """
    Blobstore handler for putting the video into <video> in event.html
    retrieves the key using the key applied in jinja
    """
    def get(self):
        blob_info = blobstore.BlobInfo.get(self.request.get('id'))
        self.send_blob(blob_info)

class ChannelConnectHandler(webapp2.RequestHandler):
    def post(self):
        """
        Channel connection handler. Will be called when a client connects.
        """
        #using channel id to avoid crossover with global client_id
        channel_id = self.request.get('from')
        print "Channel Connect. Id: %s" % channel_id


CHANNEL_DISCONNECT_URL_PATTERN = '/_ah/channel/disconnected/'

class ChannelDisconnectHandler(webapp2.RequestHandler):

    @classmethod
    def mapping(cls):
        return CHANNEL_DISCONNECT_URL_PATTERN, cls

    def post(self):
        """
        Channel disconnection handler. Will be called when a client disconnects.
        """
        channel_id = self.request.get('from')
        print "Channel Disconnect. Id: %s" % channel_id
        userlist=ChatUser.query(ChatUser.uuid == channel_id).fetch(None, keys_only=True)
        ndb.delete_multi(userlist)

class VideoDownloadHandler(blobstore_handlers.BlobstoreDownloadHandler):
    """
    Blobstore handler for downloading the video of the event called on click
    of the relevant link in event.html
    """
    def get(self):
        blob_info = blobstore.BlobInfo.get(self.request.get('id'))
        self.send_blob(blob_info, save_as=blob_info.filename)


app = webapp2.WSGIApplication([
    ('/event', EventHandler),
    ('/message', MessageHandler),
    ('/_ah/channel/connected/', ChannelConnectHandler),
    ('/_ah/channel/disconnected/', ChannelDisconnectHandler),
    ('/video', VideoHandler),
    ('/save', VideoDownloadHandler)
                              ], debug=True)