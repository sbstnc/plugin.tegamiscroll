#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#    This script is based on service.skin.widgets
#    Thanks to the original authors

import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs
import xbmcaddon
import xml.etree.ElementTree as ET
import re

if sys.version_info < (2, 7):
    import simplejson
else:
    import json as simplejson

ADDON = xbmcaddon.Addon()
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_LANGUAGE = ADDON.getLocalizedString

def log(txt):
    message = '%s: %s' % (ADDON_NAME, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=xbmc.LOGDEBUG)

class Main:
    def __init__(self):
        self._parse_argv()

        self.tokens = {}
        sortLetterList = list()
        # 0 if false, 1 if true
        hasParentItem = xbmc.getCondVisibility('System.GetBool(filelists.showparentdiritems)')
        ignoreArticles = xbmc.getCondVisibility('System.GetBool(filelists.ignorethewhensorting)')
        wid = xbmcgui.getCurrentWindowId()
        currentWindow = xbmcgui.Window(wid)

        # get sort tokens from advancedsettings.xml
        f = xbmcvfs.File(xbmc.translatePath('special://userdata/advancedsettings.xml'))
        advancedsettings = f.read()
        f.close()

        if advancedsettings:
            root = ET.fromstring(advancedsettings)
            sorttokens = root.find('sorttokens')
            # user specified tokens, proceed to create dictionary
            if sorttokens is not None:
                self.tokens = { token.text.encode('utf-8') : u'' for token in sorttokens.findall('token') }

        if self.TYPE == "scroll":
            xbmcplugin.setResolvedUrl(handle=self.handle, succeeded=False, listitem=xbmcgui.ListItem())
            containerId = self._get_view_mode()
            targetList = currentWindow.getControl(containerId)
            targetList.selectItem(int(self.pos))
            currentWindow.setFocus(targetList)
        elif self.path:
            xbmcplugin.setContent(self.handle, 'files')
            self._parse_files(sortLetterList, hasParentItem, ignoreArticles)
            xbmcplugin.addDirectoryItems(self.handle, sortLetterList)
            xbmcplugin.endOfDirectory(handle=self.handle)
        return

    def _get_view_mode(self):
        view_mode = 0
        for view in self.views:
            try:
                if xbmc.getCondVisibility( "Control.IsVisible(%i)" % int(view) ):
                    view_mode = int(view)
                    return view_mode
                    break
            except:
                pass
        return view_mode

    def _remove_articles(self, text, keep=[]):
        text = text.encode('utf-8')
        # if no sort tokens have been specified by the user xbmc uses 'the' by default
        articles_default = {u'the':u''}
        articles = self.tokens if self.tokens else articles_default
        for k in keep:
            articles.pop(k, None)
        rest = []
        for word in text.split(' '):
            # decode utf to avoid lowercase issues with foreign character sets
            if word.lower() not in articles:
                rest.append(word)
        return ' '.join(rest)

    def _is_number_string(self, text):
        p = re.compile('^[0-9\\(\\)\\[\\]]+')
        return p.match(text)

    def _parse_files(self, sortLetterList, hasParentItem, ignoreArticles):
        if self.path:
            isSeason = re.search('videodb://tvshows/titles/\d+/',self.path)
            if self.path == "videodb://movies/years/" or self.path == "videodb://tvshows/years/" or isSeason:
                return
            json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media": "files", "sort": {"order": "ascending", "method": "label", "ignorearticle": true}}, "id": 1}' % (self.path))
            json_query = unicode(json_query, 'utf-8', errors='ignore')
            count = hasParentItem
            lastSortLetterLabel = ''
            if json_query:
                json_query = simplejson.loads(json_query)
                if 'result' in json_query and 'files' in json_query['result']:
                    for item in json_query['result']['files']:
                        # if user ignores articles remove them
                        if ignoreArticles:
                            # music db doesn't remove all articles. keep some.
                            if self.path == "musicdb://artists/":
                                title = self._remove_articles(item['label'], [u'a', u'an'])
                            else:
                                title = self._remove_articles(item['label'])
                        else:
                            title = item['label']
                        # item title starts with a number, or something close enough... "50/50", "(500)", "30 Days", ...
                        if self._is_number_string(title):
                            sortLetterLabel = '#'
                        else:
                            sortLetterLabel = title[0].upper()
                        # new sort key found
                        if sortLetterLabel != lastSortLetterLabel:
                            # create a list item
                            sortLetter = xbmcgui.ListItem(sortLetterLabel)
                            url = 'plugin://plugin.tegamiscroll?views=%s&pos=%s&type=scroll' % (','.join(self.views), str(count))
                            sortLetterList.append((url, sortLetter, False))
                        # store old sort letter to ensure uniqueness in next iteration
                        lastSortLetterLabel = sortLetterLabel
                        count += 1
                del json_query

    def _parse_argv(self):
        self.handle = int(sys.argv[1])
        try:
            params = dict(arg.split("=") for arg in sys.argv[2].split("&"))
        except:
            params = {}
        self.views = params.get("?views", "")
        self.views = self.views.split(',')
        self.pos = params.get("pos", "")
        self.TYPE = params.get("type", "")
        self.path = params.get("path", "")

log('script version %s started' % ADDON_VERSION)
Main()
log('script version %s stopped' % ADDON_VERSION)