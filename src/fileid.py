# MusicPlayer, https://github.com/albertz/music-player
# Copyright (c) 2013, Albert Zeyer, www.az2000.de
# All rights reserved.
# This code is under the 2-clause BSD license, see License.txt in the root directory of this project.

# Get some native file-id handle which is persistent from file-moves.

import os, sys
import utils

if sys.platform == "darwin" and utils.isPymoduleAvailable("AppKit"):

	import AppKit
	from utils import NSAutoreleasePoolDecorator, WarnMustNotBeInForkDecorator
	
	@WarnMustNotBeInForkDecorator
	@NSAutoreleasePoolDecorator
	def getFileNativeId(filepath):
		if not os.path.isfile(filepath): return None
		filepath = os.path.abspath(filepath)
		filepath = unicode(filepath)
		
		url = AppKit.NSURL.alloc().initFileURLWithPath_(filepath)
		bookmark = url.bookmarkDataWithOptions_includingResourceValuesForKeys_relativeToURL_error_(0,None,None,None)
		if isinstance(bookmark, tuple):
			# I have no idea why this is a tuple on Python 2.7.
			# It is not a tuple on Python 2.6.
			# According to the MacOSX SDK doc, it should directly return NSData.
			bookmark = bookmark[0]

		if not bookmark: return None
		bytes = bookmark.bytes()
		if isinstance(bytes, buffer): # Python 2.6 has buffer here - otherwise (>=2.7) we have memory
			bytes = str(bytes)
		else:
			bytes = bytes.tobytes()
		return bytes
	
	@WarnMustNotBeInForkDecorator
	@NSAutoreleasePoolDecorator
	def getPathByNativeId(fileid):
		nsdata = AppKit.NSData.alloc().initWithBytes_length_(fileid, len(fileid))
		url, _, _ = AppKit.NSURL.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_(
			nsdata,
			# mounting can take long. i don't know about the timeout but it is more than 30 seconds.
			# this is not acceptable here.
			AppKit.NSURLBookmarkResolutionWithoutUI | AppKit.NSURLBookmarkResolutionWithoutMounting,
			None,None,None)
		
		if not url: return None
		
		return unicode(url.path())

else:

	print "fileid: implementation not available"
	def getFileNativeId(filepath): return None
	def getPathByNativeId(fileid): return None

