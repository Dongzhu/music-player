What is a music player?
=======================

Sometimes I get asked questions like:

> What does a music player do?
> Isn't it trivial to just play some mp3s?
> What makes a music player better at playing music than some media player like [VLC](http://www.videolan.org/vlc/) ([*](#vlc))?
> Can the audio playback quality really differ between different players?

So, I'll try to answer these questions here now.


## [Resampling](http://en.wikipedia.org/wiki/Resampling_%28audio%29)

The [soundcard](http://en.wikipedia.org/wiki/Sound_card) or the [operating system (OS)](http://en.wikipedia.org/wiki/Operating_system) usually gets [raw PCM data](http://en.wikipedia.org/wiki/Pulse-code_modulation) from an application. It usually internally works with PCM data at 48 kHz or 96 kHz. If you feed it the PCM data at another frequency, it is often able to resample the data automatically.

Audio [CDs](http://en.wikipedia.org/wiki/Compact_Disc) and most MP3s are encoded with 44.1 kHz and thus there is some resampling needed at some point.

Resampling isn't trivial and there is not really a straight-forward way to do it. Thus, different algorithms can result in much different quality.

A simple media player usually doesn't cares about that and leaves the resampling to the OS or has only some simple resampling algorithm.

A music player usually has its own high-quality resampling algorithm.

This project uses [libswresample of FFmpeg](http://ffmpeg.org/doxygen/trunk/libswresample_2resample_8c-source.html).


## [Loudness normalization](http://en.wikipedia.org/wiki/Audio_normalization#Loudness_normalization)

Different songs from different sources often have different volume / loudness.

A media player usually just plays the song as-is.

In a music player, you usually want that all songs are played with about the same loudness so that you don't have to  frequently change the volume manually to adapt to the current song.

Many existing music players don't have their own loudness analyzing algorithm. They depend on external software which analyzes your music and saves the volume-change-information in the metatags of your songs. The music player checks for that metadata information and applies the volume change. However, if it stumbles upon a song which misses this metadata information, it will not be able to do the loudness normalization.

Some professional music players such as iTunes have their own analyzing algorithm.

This project also has its own analyzing algorithm which calculates the loudness of a song based on the [ReplayGain specification](http://wiki.hydrogenaudio.org/index.php?title=ReplayGain_1.0_specification).


## Avoid [clipping](http://en.wikipedia.org/wiki/Clipping_%28audio%29) issues when incrementing the volume

When you set the volume to more than 100% (which could also theoretically, though rarely happen from the loudness normalization), you might get the case that you get PCM samples which exceeds the maximum value. E.g. assume that a PCM sample value must be between -1 and 1. If you apply the volume change and you get a value `v > 1`, you must make it fit somehow. The simplest variant would be to just use `1` as the value in that case. This is called clipping.

You want to avoid clipping because it results in bad distorted sound.

Via [dynamic range compression](http://en.wikipedia.org/wiki/Dynamic_range_compression), you can get rid of this effect while at the same time have other quality losses and you have the audio data altered.

This project uses a smooth compression variant which is only applied for values above some high threshold. Thus, in most cases, the audio data is not altered at all which is what [audiophiles](http://en.wikipedia.org/wiki/Audiophile) usually want. The compression itself has some nice properties such as that it is always smooth and will never need clipping.


## Equalizer

In some cases, you might want to have an equalizer to alter the sound a bit.


## Switching songs

The switch to the next song when some song is finished can be done in various ways.

The straight-forward way would be to just start the playback of the next song once the old song has hit the end. This is what most simple media players would do (if they have some playlist support at all).

A music player could do some fading, i.e. fading the old song out and at the same time fading the new song in.

Some players support [beatmatching](http://en.wikipedia.org/wiki/Beatmatching) so that the tempo or pitch of a song gets slightly changed so that it can seamlessly mixed with the next song. For that (and other things), it is useful to know the [beats per minute](http://en.wikipedia.org/wiki/Tempo#Beats_per_minute) of a song. Some music players and most DJ mixing software can analyze the song to determine the BPM. This is far from trivial and the BPM is not always well defined for all songs.

A music player could also try to avoid cracking if the song starts/ends abruptly.

Many music players also have support for [gapless playback](http://en.wikipedia.org/wiki/Gapless_playback). Some songs, e.g. coming from an album might have extra information how much pause there should be between them when playing the songs of the album consecutively. To have perfect control over how much pause there is, you usually need to preload the next song and mix them together in memory -- doing that on-the-fly would most certainly add some short pause.


## Skip silence sections of songs

Some songs have some longer silence sections in between them. In some cases, you might want to automatically skip these sections.


## Different sound formats

There is a wide range of sound formats, like MP3, Flac, WMA, Ogg, etc. It is very non-trivial to have support for them all.

This project uses the great [FFmpeg](http://ffmpeg.org/) library which has support for most formats and codecs.


## Intelligent automatic queue

In a music player when you have a big music library, you sometimes just want to play some random music, maybe listen to some songs you haven't heard in a while, randomly listening through your music. Sometimes you want to play some specific songs and when they are finished, it should randomly play further songs which are similar. Maybe you have some songs on your computer you don't like that much and you prefer to listen to music you like more.

Media players as well as many simple music players usually don't have any functionality where you can achieve this.

Some better music players have such things with some limited functionality. For example iTunes has this and calls it iTunes DJ mode. Some other players call this PartyShuffle.

In this project, this is central element - the main queue.

A music player could also try to choose similar songs to the current song. Analyzing the similarity of songs is again a wide area. There is for example the [MusicBox project / master thesis](http://thesis.flyingpudding.com/) which introduces in that area.


## Caching and realtime

Depending on where you are reading the song files from, e.g. local disc, network share, some Internet stream, CD, USB drive or so, reading takes some noticeable time and also might be delayed. Even worse, that might be very varying - there could be sudden drastic slow-downs or delays.

You want to be sure that while playing, the music doesn't stop suddenly. So you must make an estimation about how much data you must have read in advance into a local cache in memory so that you always have enough data left.

Also, encoding takes time. It is usually possible in realtime, meaning that encoding the full song takes less time than playing the full song, which makes it simpler in this regards. However, it still takes time and when you got the callback from the sound driver which requests for new data, you should provide data as fast as possible -- otherwise, the internal sound driver cache runs out of data and there will be a sudden drop of playback. Thus, you should do the encoding in parallel and do also some caching there so that there is always enough data present for delivery to the sound driver.

There might be situations where your operating system or the user is doing some heavy tasks which takes many system resources. This could slow down the IO access and the CPU time for the music player drastically. This would invalidate previous calculations about how much cache you need. Also, in extreme cases, encoding or even reading is not possible in realtime anymore -- which would always lead to drops in the playback.

Many operating systems provide ways to ensure your application that it got a certain amount of CPU time and also the needed amount of IO bandwidth. This is often called [real-time computing](http://en.wikipedia.org/wiki/Real-time_computing). Modern operating systems like Linux, MacOSX or Windows aren't true [real-time operating systems](http://en.wikipedia.org/wiki/Real-time_operating_system) -- however, their scheduler still can ensure certain real-time constraints with high probability.

This project, on MacOSX, uses [real-time threads](https://developer.apple.com/library/mac/#documentation/Darwin/Conceptual/KernelProgramming/scheduler/scheduler.html).


## [Last.fm](http://last.fm)

You might want to track the songs you listened with [Last.fm](http://last.fm) or some similar service (Last.fm calls this scrobbling). Last.fm can generate some interesting statistics about your music taste and make you new suggestions based on this.

This project supports Last.fm scrobbling.


## Song database

Most users have a huge amount of music. It makes sense for a music player to provide a simple and fast way to search in that music library. Also, the music player sometimes wants to save extra information about songs, such as when you lastly played it and how often you played it, etc. Also, you might want to give the user the ability to add some extra information about a song, such as further tags, some notes or some rating.

For all this, you need a database. Media players as well as simple music players usually don't have.

Most more complex music players as well as this project have that.


## Audio fingerprint

An audio fingerprint represents the song. Depending on the properties of the fingerprint, you can compare a song for similarity (based on the similarity of the fingerprint) and search for duplicate songs. Also, there are services like [MusicBrainz](http://musicbrainz.org) where you can query for metadata information such as artist name and title for any given song fingerprint. This makes sense if these information is missing.

This project can calculate the [AcoustId](http://acoustid.org/) fingerprint which is also used by MusicBrainz.


## Visual representation of audio data

You might want to see some visual representation of a song. This project supports that and calculates visual representations which look like this:

![song thumbnail](https://github.com/albertz/music-player/raw/master/song-thumbnail.png)

The color represents the spectral centroid of the sound frequency. This is calculated via a [fast Fourier transformation](http://en.wikipedia.org/wiki/Fast_Fourier_transform).


---

If you want to know some more about the internals of this project, read the [development notes](DevelopmentNotes.md).

---

## VLC

VLC is actually a bad example. It was more what you would probably expect what VLC is and does (as I did). But VLC nowadays has quite advanced in many respects and has basic volume normalizaton, dynamic range compression, an equalizer along other things. It is still missing gapless playback and a music library (although both is planned) and more advanced queue handling (such as an intelligent automatic queue).
