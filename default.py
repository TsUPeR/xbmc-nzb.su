"""
 Copyright (c) 2010 Popeye

 Permission is hereby granted, free of charge, to any person
 obtaining a copy of this software and associated documentation
 files (the "Software"), to deal in the Software without
 restriction, including without limitation the rights to use,
 copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the
 Software is furnished to do so, subject to the following
 conditions:

 The above copyright notice and this permission notice shall be
 included in all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 OTHER DEALINGS IN THE SOFTWARE.
"""

import urllib
import urllib2

import re

import xbmcaddon
import xbmcgui
import xbmcplugin

from xml.dom.minidom import parse, parseString

__settings__ = xbmcaddon.Addon(id='plugin.video.nzbsu')
__language__ = __settings__.getLocalizedString

NZBS_URL = "plugin://plugin.video.nzbs"

NS_REPORT = "http://www.newzbin.com/DTD/2007/feeds/report/"
NS_NEWZNAB = "http://www.newznab.com/DTD/2010/feeds/attributes/"

NUMBER = [25,50,75,100][int(__settings__.getSetting("num"))]

MODE_LIST = "list"
MODE_DOWNLOAD = "download"
MODE_INCOMPLETE = "incomplete"
           
# ---NZB.SU---
# <li>Rating: 5.8</li>
RE_RATING = ">Rating: (.*?)</"
RE_PLOT = ">Plot: (.*?)</"
RE_YEAR = ">Year: (.*?)</"
RE_GENRE = ">Genre: (.*?)</"
RE_DIRECTOR = ">Director: (.*?)</"
RE_ACTORS = ">Actors: (.*?)</"

MODE_NZB_SU = "nzb.su"
MODE_NZB_SU_SEARCH = "nzb.su&nzb.su=search"
MODE_NZB_SU_MY = "nzb.su&nzb.su=mycart"

NZB_SU_URL = ("http://nzb.su/rss?dl=1&i=" + __settings__.getSetting("nzb_su_id") + 
            "&r=" + __settings__.getSetting("nzb_su_key") + "&num=" + str(NUMBER) + "&")
NZB_SU_URL_SEARCH = ("http://nzb.su/api?dl=1&apikey=" + __settings__.getSetting("nzb_su_key") + 
            "&num=" + str(NUMBER) + "&")

TABLE_NZB_SU = [['Movies', 2000],
        [' - HD', 2040],
        [' - SD', 2030],
        [' - Other', 2020],
        [' - Foreign', 2010],
        ['TV', 5000],
        [' - HD', 5040],
        [' - SD', 5030],
        [' - other', 5050],
        [' - Foreign', 5020],
        [' - Sport', 5060],
        [' - Anime', 5070],
        ['XXX', 6000],
        [' - DVD', 6010],
        [' - WMV', 6020],
        [' - XviD', 6030],
        [' - x264', 6040]]

def nzb_su(params):
    if not(__settings__.getSetting("nzb_su_id") and __settings__.getSetting("nzb_su_key")):
        __settings__.openSettings()
    else:
        if params:
            get = params.get
            catid = get("catid")
            nzb_su = get("nzb.su")
            if nzb_su:
                if nzb_su == "mycart":
                    url = NZB_SU_URL + "&t=-2"
                if nzb_su == "search":
                    search_term = search('Nzb.su')
                    if search_term:
                        url = (NZB_SU_URL_SEARCH + "&t=search" + "&cat=" + catid + "&q=" 
                        + search_term)
            elif catid:
                url = NZB_SU_URL + "&t=" + catid
                key = "&catid=" + catid
                addPosts('Search...', key, MODE_NZB_SU_SEARCH)
            list_feed_nzb_su(url)
        else:
            # if not catid:
            # Build Main menu
            for name, catid in TABLE_NZB_SU:
                if ("XXX" in name) and (__settings__.getSetting("nzb_su_hide_xxx").lower() == "true"):
                 break
                key = "&catid=" + str(catid)
                addPosts(name, key, MODE_NZB_SU)
            # TODO add settings toggle
            addPosts("My Cart", '', MODE_NZB_SU_MY)
    return

def list_feed_nzb_su(feedUrl):
    doc = load_xml(feedUrl)
    for item in doc.getElementsByTagName("item"):
        title = get_node_value(item, "title")
        description = get_node_value(item, "description")
        rating = re.search(RE_RATING, description, re.IGNORECASE|re.DOTALL)
        if rating:
            rating = float(rating.group(1))
        else:
            rating = 0
        plot = re.search(RE_PLOT, description, re.IGNORECASE|re.DOTALL)
        if plot:
            plot = plot.group(1)
        else:
            plot = ""
        year = re.search(RE_YEAR, description, re.IGNORECASE|re.DOTALL)
        if year:
            year = int(year.group(1))
        else:
            year = 0
        genre = re.search(RE_GENRE, description, re.IGNORECASE|re.DOTALL)
        if genre:
            genre = genre.group(1)
        else:
            genre = ""
        director = re.search(RE_DIRECTOR, description, re.IGNORECASE|re.DOTALL)
        if director:
            director = director.group(1)
        else:
            director = ""
        actors = re.search(RE_ACTORS, description, re.IGNORECASE|re.DOTALL)
        if actors:
            actors = actors.group(1)
        else:
            actors = ""
        nzb = get_node_value(item, "link")
        thumb = ""
        for attribute in item.getElementsByTagName("newznab:attr"):
            name = attribute.getAttribute("name")
            if name == "imdb":
                thumbid = attribute.getAttribute("value")
                thumb = "http://nzb.su/covers/movies/" + thumbid + "-cover.jpg"
        nzb = "&nzb=" + urllib.quote_plus(nzb) + "&nzbname=" + urllib.quote_plus(title)
        mode = MODE_LIST
        addPosts(title, nzb, mode, plot, thumb, rating, year, genre, director, actors)
    return

def addPosts(title, url, mode, description='', thumb='', rating = 0, year = 0, genre = '', director = '', actors = '', folder=True):
    listitem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage=thumb)
    listitem.setInfo(type="Video", infoLabels={ "Title": title, "Plot" : description, "Rating" : rating, "Year" : year, 
                    "Genre" : genre, "Director" : director, "Actors" : actors})
    if mode == MODE_LIST:
        cm = []
        cm_mode = MODE_DOWNLOAD
        cm_label = "Download"
        if (__settings__.getSetting("auto_play").lower() == "true"):
            folder = False
        cm_url_download = NZBS_URL + '?mode=' + cm_mode + url
        cm.append((cm_label , "XBMC.RunPlugin(%s)" % (cm_url_download)))
        listitem.addContextMenuItems(cm, replaceItems=False)
        xurl = "%s?mode=%s" % (NZBS_URL,mode)
    elif mode == MODE_INCOMPLETE:
        xurl = "%s?mode=%s" % (NZBS_URL,mode)
    else:
        xurl = "%s?mode=%s" % (sys.argv[0],mode)
    xurl = xurl + url
    listitem.setPath(xurl)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=xurl, listitem=listitem, isFolder=folder)
 
# FROM plugin.video.youtube.beta  -- converts the request url passed on by xbmc to our plugin into a dict  
def getParameters(parameterString):
    commands = {}
    splitCommands = parameterString[parameterString.find('?')+1:].split('&')
    
    for command in splitCommands: 
        if (len(command) > 0):
            splitCommand = command.split('=')
            name = splitCommand[0]
            value = splitCommand[1]
            commands[name] = value
    
    return commands

def get_node_value(parent, name, ns=""):
    if ns:
        return parent.getElementsByTagNameNS(ns, name)[0].childNodes[0].data
    else:
        return parent.getElementsByTagName(name)[0].childNodes[0].data

def load_xml(url):
    try:
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
    except:
        xbmc.log("unable to load url: " + url)

    xml = response.read()
    response.close()
    return parseString(xml)

def search(dialog_name):
    searchString = unikeyboard('', '' )
    if searchString == "":
        xbmcgui.Dialog().ok('Missing text')
    elif searchString:
        # latestSearch = __settings__.setSetting( "latestSearch", searchString )
        dialogProgress = xbmcgui.DialogProgress()
        dialogProgress.create(dialog_name, 'Searching for: ' , searchString)
        #The XBMC onscreen keyboard outputs utf-8 and this need to be encoded to unicode
    encodedSearchString = urllib.quote_plus(searchString.decode("utf_8").encode("raw_unicode_escape"))
    return encodedSearchString

#From old undertexter.se plugin    
def unikeyboard(default, message):
    keyboard = xbmc.Keyboard(default, message)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        return keyboard.getText()
    else:
        return None

if (__name__ == "__main__" ):
    if not (__settings__.getSetting("firstrun") and __settings__.getSetting("nzb_su_id")
        and __settings__.getSetting("nzb_su_key")):
        # Try import from nzbs
        try:
            __nzbs_settings__ = xbmcaddon.Addon(id='plugin.video.nzbs')
            __settings__.setSetting("nzb_su_id", __nzbs_settings__.getSetting("nzb_su_id"))
            __settings__.setSetting("nzb_su_key", __nzbs_settings__.getSetting("nzb_su_key"))
        except:
            # DEBUG
            print "plugin.video.nzbsu - nothing to import from plugin.video.nzbs"
        __settings__.openSettings()
        __settings__.setSetting("firstrun", '1')
    if (not sys.argv[2]):
        nzb_su(None)
        addPosts('Incomplete', '', MODE_INCOMPLETE)
    else:
        params = getParameters(sys.argv[2])
        get = params.get
        if get("mode")== MODE_LIST:
            listVideo(params)
        if get("mode")== MODE_NZB_SU:
            nzb_su(params)

xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=True, cacheToDisc=True)