# -*- coding: utf-8 -*-
# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2012, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

import utils
from utils import UserAttrib, Event, initBy
import Traits
import gui

# Note: I'm not too happy with all the complicated update handling here...
# In general, the design is ok. But it needs some more specification
# and then some drastic simplification. Most of it should be one-liners.

class SongEdit:
	# This is used by the GUI update system.
	@initBy
	def _updateEvent(self): return Event()

	def _updateHandler(self):
		self._updateEvent.push()

	def __init__(self, ctx=None):
		if not ctx:
			import gui
			ctx = gui.ctx()
			assert ctx, "no gui context"
		self.ctx = ctx
		ctx.curSelectedSong_updateEvent.register(self._updateHandler)
		
	@UserAttrib(type=Traits.Object)
	@property
	def song(self):
		return self.ctx.curSelectedSong	

	@UserAttrib(type=Traits.EditableText)
	def artist(self, updateText=None):
		if self.song:
			if updateText:
				self.song.artist = updateText
			return self.song.artist
		return ""
	
	@UserAttrib(type=Traits.EditableText)
	def title(self, updateText=None):
		if self.song:
			if updateText:
				self.song.title = updateText
			return self.song.title
		return ""

	@staticmethod
	def _convertTagsToText(tags):
		def txtForTag(tag):
			value = tags[tag]
			if value >= 1: return tag
			return tag + ":" + str(value) 
		return " ".join(map(txtForTag, sorted(tags.keys())))

	@staticmethod
	def _convertTextToTags(txt):
		pass
	
	# todo...
	#@UserAttrib(type=Traits.EditableText)
	def tags(self, updateText=None):
		if self.song:
			return self._convertTagsToText(self.song.tags)
		return ""

	@staticmethod
	def _formatGain(gain):
		factor = 10.0 ** (gain / 20.0)
		return "%f dB (factor %f)" % (gain, factor)

	@UserAttrib(type=Traits.Table(keys=("key", "value")), variableHeight=True)
	@property
	def metadata(self):
		d = dict(self.song.metadata)
		for (key,func) in (
			("artist",None),
			("title",None),
			("album",None),
			("duration",utils.formatTime),
			("url",None),
			("rating",None),
			("tags",self._convertTagsToText),
			("gain",self._formatGain),
			("completedCount",None),
			("skipCount",None),
			("lastPlayedDate",utils.formatDate),
			("id",repr),
		):
			try: value = getattr(self.song, key)
			except AttributeError: pass
			else:
				if func: value = func(value)
				if not isinstance(value, (str,unicode)):
					value = str(value)
				d[key] = utils.convertToUnicode(value)
		l = []
		for key,value in sorted(d.items()):
			l += [{"key": key, "value": value}]
		return l

	def _queryAcoustId(self):
		fingerprint = self.song.get("fingerprint_AcoustId", timeout=None)[0]
		duration = self.song.get("duration", timeout=None, accuracy=0.5)[0]
		
		import base64
		fingerprint = base64.urlsafe_b64encode(fingerprint)
		
		api_url = "http://api.acoustid.org/v2/lookup"
		# "8XaBELgH" is the one from the web example from AcoustID.
		# "cSpUJKpD" is from the example from pyacoustid
		# get an own one here: http://acoustid.org/api-key
		client_api_key = "cSpUJKpD"
		
		params = {
			'format': 'json',
			'client': client_api_key,
			'duration': int(duration),
			'fingerprint': fingerprint,
			'meta': 'recordings recordingids releasegroups releases tracks compress',
		}
		
		import urllib
		body = urllib.urlencode(params)
		
		import urllib2
		req = urllib2.Request(api_url, body)
		
		import contextlib
		with contextlib.closing(urllib2.urlopen(req)) as f:
			data = f.read()
			headers = f.info()
		
		import json
		data = json.loads(data)
		return data

	def queryAcoustIdResults_selectionChangeHandler(self, selection):
		self._queryAcoustId_selection = selection
		
	@UserAttrib(type=Traits.Table(keys=("artist", "title", "album", "track", "score")),
		selectionChangeHandler=queryAcoustIdResults_selectionChangeHandler,
		addUpdateEvent=True)
	@property
	def queryAcoustIdResults(self):
		if getattr(self, "_queryAcoustIdResults_songId", "") != getattr(self.song, "id", ""):
			return []
		return list(getattr(self, "_queryAcoustIdResults", []))

	@UserAttrib(type=Traits.Action, variableWidth=False)
	def queryAcoustId(self):
		data = self._queryAcoustId()
		
		self._queryAcoustIdResults_songId = self.song.id
		self._queryAcoustIdResults = []
		for result in data.get("results", []):
			for recording in result.get("recordings", []):
				for resGroup in recording.get("releasegroups", []):
					artist = resGroup["artists"][0]
					release = resGroup["releases"][0]
					medium = release["mediums"][0]
					track = medium["tracks"][0]
					if artist["name"] == "Various Artists":
						artist = track["artists"][0]
					entry = {
						"id": result["id"],
						"score": result["score"],
						"recording-id": recording["id"],
						"releasegroup-id": resGroup["id"],
						"artist-id": artist["id"],
						"artist": artist["name"],
						"title": track["title"],
						"album": resGroup["title"],
						"track": "%i/%i" % (track["position"], medium["track_count"])
					}
					self._queryAcoustIdResults += [entry]
		if not self._queryAcoustIdResults:
			self._queryAcoustIdResults += [{"artist":"- None found -","title":"","album":"","track":""}]
		self.__class__.queryAcoustIdResults.updateEvent(self).push()
		
	@UserAttrib(type=Traits.Action, variableWidth=False, alignRight=True)
	def apply(self):
		if getattr(self, "_queryAcoustIdResults_songId", "") != getattr(self.song, "id", ""):
			return
		sel = getattr(self, "_queryAcoustId_selection", [])
		if not sel: return
		sel = sel[0]
		for key in ("artist","title"):
			if not sel[key]: return
		for key in ("artist","title","album","track"):
			setattr(self.song, key, sel[key])
		self._updateEvent.push() # the song is updating itself - but the edit fields aren't atm...


gui.registerCtxRootObj(clazz=SongEdit, name="Song edit", priority=-2, keyShortcut='i')
