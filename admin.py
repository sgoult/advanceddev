#!/usr/bin/env python
import os
import jinja2
import webapp2

from google.appengine.ext import blobstore
from google.appengine.api import users
from createevent import Event

template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.getcwd()))

class AdminHandler(webapp2.RequestHandler):
    """
    Admin.html handler, deals with user authentication for the admin page determining if delegate or admin and
    showing options appropriate to them (or none at all if invalid) this currently allows the delegate to post
    to any event, something which could be remedied using events they are whitelisted on.

    uses appengines users api for authentication, future additions would be self made validation for non google
    users.
    """
    def get(self):
        isadmin=False
        isdelegate=False
        if users.is_current_user_admin():
            isadmin=True
        if not users.is_current_user_admin():
            events = Event.query().fetch()
            for event in events:
                whitelist=str(event.whitelist)
                print whitelist
                print type(whitelist)
                if users.get_current_user():
                    try:
                        if users.get_current_user() in whitelist:
                            isdelegate=True
                    except:
                        continue
                else:
                    self.error(403)
        #generates template items for admin.html
        upload_url = blobstore.create_upload_url('/upload')
        template = template_env.get_template('templates/admin.html')
        login_url = users.create_login_url(self.request.url)
        logout_url = users.create_logout_url(self.request.url)
        user = users.get_current_user()
        context = {
            'user': user,
            'login_url': login_url,
            'logout_url': logout_url,
            'upload_url': upload_url,
            'isdelegate': isdelegate,
            'isadmin': isadmin}
        self.response.write(template.render(context))


app = webapp2.WSGIApplication([
    ('/admin', AdminHandler)
], debug=True)