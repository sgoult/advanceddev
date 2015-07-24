#!/usr/bin/env python
import webapp2
import datetime

from createevent import Event
from event import ChatUser

from google.appengine.api import channel
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from formcomment import Comment

class EmailHandler(InboundMailHandler):
    """
    Email handler, builds a whitelisted delegates comment from email body.
    Couldnt get attachments to upload to blobstore so removed to avoid bugs
    Uses the Comment object from formcomment.py

    tests for delegates and logs unauthorised use

    preformats comment with html so that it can just be dumped to the page

    uses channel api to update comment section through connected client ids
    on event page and in database
    """
    def receive(self, mail_message):
        user = mail_message.sender
        eventname = mail_message.subject
        eventlist = Event.query().fetch()
        time=datetime.datetime.now()
        for event in eventlist:
            whitelist=str(event.whitelist)
            if user in whitelist:
                content='!!comment!!<span class="media"><a class="media-left" href="#"></a><div class="media-body"><h4 class="media-heading">'+str(user)+'</h4>'+mail_message.body.decode()+'<div>'+time.strftime('%H:%M')+'</div></div></span>'
                eventkey = event.key.urlsafe()
                cmnt = Comment()
                cmnt.event = eventkey
                cmnt.content = content
                cmnt.user = user
                cmnt.put()
                clientquery = ChatUser.query(ChatUser.event == eventkey)
                clients=clientquery.fetch()
                for client in clients:
                    channel.send_message(client.uuid, content)
            else:
                print "false request from " + user

app = webapp2.WSGIApplication([
    ('/_ah/mail/.+', EmailHandler)
], debug=True)