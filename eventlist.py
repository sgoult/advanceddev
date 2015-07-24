#!/usr/bin/env python
import os
import jinja2
import webapp2
import datetime

from google.appengine.api import users
from createevent import Event

template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.getcwd()))

class EventListHandler(webapp2.RequestHandler):
    """
    Creates a group of lists for events dependant on time.
    These are posted in the page that greets the user at app load, to avoid multiquery
    the lists are compared for selection of event type
    """
    def get(self):
        template = template_env.get_template('templates/eventlist.html')
        futureeventquery = Event.query(Event.startdatetime > datetime.datetime.now())
        futureevents = futureeventquery.fetch()

        currenteventquery = Event.query(Event.enddatetime > datetime.datetime.now())
        currentevents = currenteventquery.fetch()

        pasteventquery = Event.query(Event.enddatetime < datetime.datetime.now())
        pastevents = pasteventquery.fetch()

        login_url = users.create_login_url(self.request.url)
        logout_url = users.create_logout_url(self.request.url)

        user=users.get_current_user()
        #avoids multiple queries
        for item in futureevents:
            if item in currentevents:
                futureevents.remove(item)

        context = {
            'user': user,
            'login_url': login_url,
            'logout_url': logout_url,
            'futureevents': futureevents,
            'currentevents': currentevents,
            'pastevents': pastevents}
        self.response.write(template.render(context))



app = webapp2.WSGIApplication([
    ('/eventlist', EventListHandler),
    ('/', EventListHandler)
], debug=True)