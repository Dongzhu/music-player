
from UserAttrib import UserAttrib
from utils import safe_property
import Traits


class Preferences(object):
	def __init__(self):
		self._sampleRateStr = None
		self.lastFm_update(self.__class__.lastFm)

	@UserAttrib(type=Traits.OneLineText, autosizeWidth=True)
	@property
	def soundDeviceLabel(self):
		return "Preferred sound device:"

	@UserAttrib(type=Traits.EditableText, autosizeWidth=True, alignRight=True)
	def preferredSoundDevice(self, updateText=None):
		from State import state
		player = state.player
		if updateText is not None:
			player.preferredSoundDevice = updateText
			from appinfo import config
			config.preferredSoundDevice = updateText
			config.save()
		return player.preferredSoundDevice

	@UserAttrib(type=Traits.OneLineText, variableWidth=True)
	@property
	def soundDeviceDescr(self):
		return "(Playback needs to be stopped to set this into effect.)"


	@UserAttrib(type=Traits.OneLineText, autosizeWidth=True)
	@property
	def actualSoundDeviceLabel(self):
		return "Current sound device:"

	@UserAttrib(type=Traits.OneLineText, autosizeWidth=True, withBorder=True, alignRight=True)
	@safe_property
	@property
	def actualSoundDevice(self):
		from State import state
		return state.player.actualSoundDevice


	@UserAttrib(type=Traits.OneLineText, autosizeWidth=True)
	@property
	def availableSoundDevicesLabel(self):
		return "Available sound devices:"

	@UserAttrib(type=Traits.Table(keys=("Name",)), autosizeWidth=True, alignRight=True)
	@safe_property
	@property
	def availableSoundDevices(self):
		import musicplayer
		l = musicplayer.getSoundDevices()
		return [{"Name": dev} for dev in l]


	@UserAttrib(type=Traits.OneLineText, autosizeWidth=True)
	@property
	def sampleRateLabel(self):
		return "Sample rate in Hz:"

	@property
	def _sampleRate(self):
		from State import state
		return state.player.outSamplerate

	@UserAttrib(type=Traits.EditableText,
		alignRight=True, variableWidth=True,
		width=200, # this forces a min-width
		addUpdateEvent=True
		)
	def sampleRate(self, updateText=None):
		if updateText is not None and self._sampleRateStr != updateText:
			self._sampleRateStr = updateText
		if self._sampleRateStr is not None:
			return self._sampleRateStr
		rate = str(self._sampleRate / 1000)
		return rate + "k"

	@UserAttrib(type=Traits.Action, name="apply", alignRight=True, variableWidth=False)
	def applySampleRate(self):
		self.__class__.sampleRate.updateEvent(self).push()

		self._sampleRateStr, rate = None, self._sampleRateStr
		if rate is None: return
		rate = rate.strip()
		if rate[-1:] == "k":
			factor = 1000
			rate = rate[:-1]
		else:
			factor = 1
		try: rate = int(rate) * factor
		except Exception: return # no valid integer

		# do some very basic check on the number.
		# later, our musicplayer module should allow us to check this.
		if rate in (44100,48000,88200,96000,176400,192000): pass
		else: return

		from State import state
		state.player.playing = False # can only change that when not playing
		state.player.outSamplerate = rate

		from appinfo import config
		config.sampleRate = rate
		config.save()

	def lastFm_update(self, attrib):
		from appinfo import config
		if config.lastFm:
			attrib.name = "Last.fm is enabled. Disable it."
		else:
			attrib.name = "Last.fm is disabled. Enable it."

	@UserAttrib(type=Traits.Action, updateHandler=lastFm_update, variableWidth=False, addUpdateEvent=True)
	def lastFm(self):
		self.__class__.lastFm.updateEvent(self).push()

		from appinfo import config
		config.lastFm = not config.lastFm
		config.save()

		from ModuleSystem import getModule
		getModule("tracker_lastfm").reload()

	@UserAttrib(type=Traits.Action, alignRight=True, name="reset Last.fm login", variableWidth=False)
	def resetLastFm(self):
		import lastfm, os, sys
		try:
			os.remove(lastfm.StoredSession.TOKEN_FILE)
		except Exception:
			sys.excepthook(*sys.exc_info())

prefs = Preferences()

import gui
gui.registerRootObj(obj=prefs, name="Preferences", priority=-5)
