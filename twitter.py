#!/usr/bin/env python
import base64
import json
import urllib
import urllib2
import webapp2
import unicodedata
import datetime
from event import ChatUser

from formcomment import Comment
from createevent import Event
from google.appengine.api import channel

#Super secret private keys that I shouldn't be telling anyone
consumerkey="DS4ug7ZxMfPiTZZmUKuaOLPCh"
consumersecret="B2qVPRwa773wT7z4SqkAGH1gSba6HhjfnDqvyC5wWtS2U6xlzX"

#super secret url encoding method
urlencode=consumerkey+':'+consumersecret

#encoding for twitter interaction
b64 = base64.b64encode(urlencode)

class TwitterHandler(webapp2.RequestHandler):
    """
    basic twitter scraper. Searches for hashtags then checks the twitter user for if they are
    in the whitelist. If they are the comment is posted through channel api.

    this is run in a cron job (cron.yaml) to scrape every 20 minutes, can increase but didn't
    want to spoil my licence straight away
    """
    def get(self):
        currentevents = Event.query().fetch()
        liveevents=[]
        for event in currentevents:
            if event.startdatetime < datetime.datetime.now():
                liveevents.append(event)
        print liveevents

        for event in liveevents:
            #initial post to twitter for authentication
            url = 'https://api.twitter.com/oauth2/token'
            values = {'grant_type' : 'client_credentials'}
            headers = {'Authorization': 'Basic '+b64,
                       'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}
            data = urllib.urlencode(values)
            req = urllib2.Request(url, data, headers)
            content = urllib2.urlopen(req).read()

            #above returns the key for use below, it needs to run every time to ensure twitter havent
            #killed the key

            #load response into json parser
            authjson = json.loads(content)
            twitterurl="https://api.twitter.com/1.1/search/tweets.json?q=%23"+str(event.hashtag)
            #get the whitelist
            whitelist=str(event.whitelist)

            #post to get the twitter scrape
            url = twitterurl
            headers = {'Authorization': 'Bearer '+authjson['access_token'],
                       'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}
            req = urllib2.Request(url, headers=headers)
            searchresult=json.loads(urllib2.urlopen(req).read())

            #iterate through the response json looking for tweets
            for tweet in searchresult['statuses']:
                name = str(unicodedata.normalize('NFKD', tweet['user']['name']).encode('ascii', 'ignore'))
                screen_name = str(unicodedata.normalize('NFKD', tweet['user']['screen_name']).encode('ascii', 'ignore'))
                #check user is delegate
                if name in whitelist or screen_name in whitelist:
                    #make the tweets nice
                    text = str(unicodedata.normalize('NFKD', tweet['text']).encode('ascii', 'ignore'))
                    created = str(unicodedata.normalize('NFKD', tweet['created_at']).encode('ascii', 'ignore'))
                    profile_imgurl = str(unicodedata.normalize('NFKD', tweet['user']['profile_image_url']).encode('ascii', 'ignore'))
                    content='!!comment!!<span class="media"><a class="media-left" href="https://twitter.com/'+screen_name+'"><img src="'+profile_imgurl+'" alt="profile picture"></a><div class="media-body"><h4 class="media-heading">'+screen_name+'</h4>'+text+'<div>'+created+'</div></div></span>'
                    eventkey=str(event.key.urlsafe())
                    cmnt=Comment()
                    cmnt.event=eventkey
                    cmnt.content=content
                    cmnt.put()
                    #send out the comment to the comments section
                    clientquery = ChatUser.query(ChatUser.event == eventkey)
                    clients=clientquery.fetch()
                    for client in clients:
                        channel.send_message(client.uuid, content)

app = webapp2.WSGIApplication([
    ('/twitter', TwitterHandler)
                              ], debug=True)