The items below will not work offline, you can find a working version online at: http://indigo-night-782.appspot.com/
- cron jobs
- channel (this seems to be because the local version recognises a disconnect after the first message is sent. Intermittent though!)
- email (actually works offline but easier not to) (simulate it if you want though!)

Images on webform comments won't work - I can't find the way to fix it though I think it's to do with the way I was handing them to channel.

At the online version an event will already be set up, although the time might have passed already the event will still be present under "Past Events"
You can email this event (I've set your BU email as a delegate already) The hashtag is fairly unique, and only authenticates to my user.

Feel free to create your own event on the online version (you can circumvent the admin check by going directly to http://indigo-night-782.appspot.com/createevent).

the delegates field on the create event page is just a plaintext entry. List as many email addresses, twitter handles and names as needed.
Capitalisation is vital here as python is case specific in its comparisons,though the code exists to remove this I have tried to avoid using any additional
libraries (outside the already included google appengine ones) in this project

The event page is made up of three major elements:
- the video stream
- the chatbox (right)
- the comments box
    > contains email, webform and twitter comments

These update on the fly as comments and messages are sent to each.

************************
Technology Choices
************************
---------
Python
---------
I have used python to build the application as it is my language of best expertise. My year in industry was spent building and maintaining Python scripts and programs for use in unix and as such
most of my experience in programming has been in python recently. Other options included looking at java or google go, the amount of code required for java implementations was considerably above
that of python which steered the decision back and hands on experience with go among other developers is low so help in development and maintenance would be low.

Python provides an easy solution to both development and later maintaining the app.

---------
cron jobs
---------
I am using a cron job for the twitter scrape functionality to reduce requests (over say, doing it everytime a user connects) the cron job batches twitter scrapes down to one every 20 minutes.
This reduces requests from app engine and avoids twitter rejecting authentication. This works functionally for the intended purpose but if a high volume of tweets is required at a persistent
rate the more expensive api keys will be needed for scaling up the twitter requests.
(although the number delegates probably wouldn't be so high that the comments section became a second chat room)

Cron jobs provide a protection from link overuse.

-------
channel - scalability (1 cent per user)
--------
https://cloud.google.com/pricing/ puts the cost of this solution at $0.01 / 100 channels a day, or $0.01 (not £0.01) per user. This makes it extremely scalable, the site could create 1,000,000 users and
still only have to pay $100, a very good overhead assuming advertising was included in the broadcast. (even assuming a 0.01% click through the likelihood is $100 could be reconciled).

Channel is both scalable and efficient and, most importantly, reuseable.
--------
datastore
---------
using the nosql datastore