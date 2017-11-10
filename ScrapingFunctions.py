# coding: utf-8

"""Module which contains useful function for scraping"""
import requests
from bs4 import BeautifulSoup
import subprocess
from PIL import Image
from io import BytesIO


def make_soup(url):
    """make soup from url"""
    html = requests.get(url)
    return BeautifulSoup(html.content, "html5lib")


def find_link(url, keys=None):
    """
    return links in a web page. return links which contains keys when keys is given
    :param url: string
        url of web page
    :param keys: list
        search links which contains key in keys
    :return: list
        list of url
    """
    soup = make_soup(url)
    links = []
    hyper_links = soup.find_all("a")
    if keys is None:
        for link in hyper_links:
            link = link.get("href")
            if link is not None:
                links.append(link)
    else:
        for link in hyper_links:
            link = link.get("href")
            if link is not None:
                for key in keys:
                    if key in link:
                        links.append(link)

    return links


def open_browser(url):
    """open url in a browser"""
    subprocess.call("start %s" % url, shell=True)


def get_image(url):
    """get image from url"""
    img_html = requests.get(url)
    img = Image.open(BytesIO(img_html.content))

    return img


if __name__ == "__main__":
    pass
