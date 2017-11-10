# coding: utf-8
from bs4 import BeautifulSoup
import ScrapingFunctions

import re
import datetime
import os
import time


OPEN = "open"
CLOSED = "close"
SOLD_OUT = "sold_out"
NOT_POSTED = "not_posted"


class NekoRamen(object):

    def __init__(self, url):
        self.url = url
        self.soup = ScrapingFunctions.make_soup(self.url)
        self.post_num = 0
        self.page = 1

    def __iter__(self):
        return self

    def __str__(self):
        return soup.prettify()

    def __next__(self):
        self.post_num += 1
        blog_posts = self.soup.find_all("div", class_="blogBlock")
        try:
            blogBlock = blog_posts[self.post_num]
        except IndexError:
            self.page += 1
            time.sleep(1)
            self.soup = ScrapingFunctions.make_soup(
                self.url + "/" + str(self.page))
            self.post_num = 0
            blog_posts = self.soup.find_all("div", class_="blogBlock")
            try:
                blogBlock = blog_posts[self.post_num]
            except:
                raise StopIteration

        latest_post = Post()
        latest_post.set_time(blogBlock.find("h2").string)
        if blogBlock.find("div", class_="blogP").string is None:
            latest_post.set_content(str(blogBlock.find("div", class_="blogP")))
        else:
            latest_post.set_content(
                blogBlock.find("div", class_="blogP").string)
        latest_post.set_title(blogBlock.find("p").string)
        return latest_post

    def reload_page(self):
        self.soup = ScrapingFunctions.make_soup(self.url)

    def get_latest_post(self):
        self.__init__(self.url)
        blogBlock = self.soup.find_all("div", class_="blogBlock")
        blogBlock = blogBlock[0]

        latest_post = Post()
        latest_post.set_time(blogBlock.find("h2").string)
        if blogBlock.find("div", class_="blogP").string is None:
            latest_post.set_content(str(blogBlock.find("div", class_="blogP")))
        else:
            latest_post.set_content(
                blogBlock.find("div", class_="blogP").string)
        latest_post.set_title(blogBlock.find("p").string)
        return latest_post

    def check_status_today(self):
        """
        return status of today's post'
        """
        today = datetime.date.today()
        latest_post = self.get_latest_post().post_time
        latest_post = latest_post.date()
        if today == latest_post:
            print("information posted already!")
            return self.get_latest_post().check_status()
        else:
            return NOT_POSTED

    def check_update(self):
        """
        check if there is new post
        ramen.info contains datetime when its last checked 
        """
        update = True
        with open("ramen.info", "r") as f:
            info = f.read()
        # get last checked date
        try:
            last_checked_date = eval(info)
            # get last posted date 
            latest_post_date = self.get_latest_post().post_time

            # if the post is newer than last checked date
            if latest_post_date > last_checked_date:
                update = True
            else:
                update = False
        except SyntaxError:
            print("ramen.info is deleted or broken")
            update = True 
        with open("ramen.info", "w") as f:
            current_time = datetime.datetime.now()
            f.write(repr(current_time))
        return update
            
class Post(object):

    def __init__(self):
        self.title = None
        self.post_time = None
        self.content = None

    def set_title(self, title):
        self.title = str( title)

    def set_time(self, post_time):
        date_element = re.findall(r"[0-9]+", post_time)
        date_element = map(int, date_element)
        self.post_time = datetime.datetime(*date_element)

    def set_content(self, content):
        self.content = str( content )

    def check_status(self):
        """
        return if the post means OPEN,  CLOSE,  or SOLD_OUT
        """
        if u"売り切れです" in self.title:
            return SOLD_OUT

        elif u"営業いたします" in self.content:
            return OPEN
        elif u"休みとなります" in self.content:
            return CLOSED
        else:
            print("no much'")
            print(self.content)
            return False

if __name__ == "__main__":
    import pickle
    neko = NekoRamen("https://www5.hp-ez.com/hp/haratyan/blog")
    post = neko.get_latest_post()
    posts = []
    if neko.check_update():
        print(neko.check_status_today())
    print(post.content)

    for i, post in enumerate( neko ):
        if i <= 2000:
            posts.append(post)
            print(post.post_time)
        else:
            break

    with open("all_posts.pickle", mode="wb") as f:
        pickle.dump(posts, f)

    
