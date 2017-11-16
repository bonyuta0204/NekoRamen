from ramen import *
import datetime
import twy

neko = NekoRamen() 
if neko.check_update():
    new_post = neko.get_latest_post()
    if new_post.check_status() == OPEN:
        tweet = u"本日営業\n" + new_post.content
    elif new_post.check_status()  ==  CLOSED:
        tweet = u"本日休業\n" + new_post.content
    elif new_post.check_status()  == SOLD_OUT:
        tweet = u"売り切れました\n" + new_post.content

    if len(tweet) > 140:
        tweet = tweet[:140] + "..."
else:
    tweet = "This is for debug use"+ str( datetime.datetime.now() )
print(tweet)
api = twy.api
api.update_status(status=tweet)
