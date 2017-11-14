
import tweepy

# 各種キーをセット
CONSUMER_KEY = '7SwvV3B0guW81Qtfz45JHo2fs'
CONSUMER_SECRET = 'Bo7ujF8oAMTnXRZ2hw5jFfqJqihTl2tgpHCJVTXewWr7RMsm3h'
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
ACCESS_TOKEN = '4801461192-dEsH8vyZzLRagXTX3iU0WYD2shEkxru1d1u8MhX'
ACCESS_SECRET = 'in7yAlZqf2s4J9Z6p67MjiKdiaECgzjIEHLmEb2vnkG4n'
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

#APIインスタンスを作成
api = tweepy.API(auth)

# これだけで、Twitter APIをPythonから操作するための準備は完了。
print('Done!')

