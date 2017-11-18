from ramen import *
import datetime
import twy

neko = NekoRamen() 
new_post = neko.get_latest_post()

if new_post.check_status() == OPEN:
    tweet = u"本日営業\n" + new_post.content
elif new_post.check_status()  ==  CLOSED:
    tweet = u"本日休業\n" + new_post.content
elif new_post.check_status()  == SOLD_OUT:
    tweet = u"売り切れました\n" + new_post.content

if len(tweet) > 140:
    tweet = tweet[:140] + "..."

api = twy.api
last_tweet = api.user_timeline()[0].text
# when tweet is already posted, 
print(last_tweet)
print(tweet)

if last_tweet.split()[:2]  == tweet.split()[:2]:
    print("already tweeded")
else:
    print("new tweet") 
    api.update_status(status=tweet)
