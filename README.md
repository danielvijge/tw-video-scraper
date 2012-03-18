# tw-video-scraper

`tw-video-scraper` is a Python script that can retrieve fan art
thumbnail for a video file. It is designed to run with TwonkyMedia server,
but can possibly be of use to others as well. It was designed for (Debian) Linux,
but can run on Windows as well. See the instruction below for Windows users.

## Background

[TwonkyMedia server](http://www.twonky.com) is a DLNA server that runs on a lot
of different devices. Using `ffmpeg` Twonky can generate thumbnails for video
files. A guide to setting up Twonky can be found
[here](http://server.vijge.net/archive/twonky-dlna-with-video-thumbnails/)

One of the problems of using `ffmpeg` is that it takes a snapshot of the video
file at a fixed time, for example at 30 seconds. For both movies and series
this can be a problem. If there are opening credits, the thumbnail will display
that. This might not be a very meaningful thumbnail for the video file.

For a lot of movies and series there is fan art on the internet. This is a
thumbnail that is more meaningful, such as a screenshot from a specific scene
in a serie's episode, or the poster for a movie.
`tw-video-scraper` tries to get the fan art thumbnail for a video file. If no
thumbnail can be found, `ffmpeg` is used to generate a thumbnail.

## How to use

`tw-video-scraper` is a Python script that takes two arguments. The first is
the name of the video file, the second is the output image file.

	python tw-video-scraper.py /path/to/cool.serie.s01e04.htdv.avi /images/abc.jpg

To use it with Twonky, save `tw-video-scraper.py`, `python-tw-video-scraper.desc` 
and `python.location` in Twonky's cgi-bin directory. Make all files executable

	chmod 700 tw-video-scraper.py python-python-tw-video-scraper.desc python.location

If needed, change the values in `python.location`, `tw-video-scraper.py`, and
`python-tw-video-scraper.desc`.
The file `ffmpeg-video-thumb.desc` is no longer needed. Either comment out all
lines are delete the file.
If you want to regenerate all thumbnail, delete everything from the cache folder
in the twonky directory (i.e. `/var/twonkymedia/twonkymedia/db/cache`)
Now restart Twonky, and the script is used.

At least `jpeg-scale.desc` and `cgi-jpegscale` plugin must also be enabled.

## How it works

Thumbnail for series are retrieved from TheTVDB.com. For movies, TheMovieDB.org is
used. For each file, the script tries to guess the name and year of the movie, or
the name of the series, the season, and the episode number. This is done by
regular expression patterns.

### Series

First, it tries to determine if the file is a series. It is a series if the file name
matches one of the following conditions:

- The file name containing S01E01 (or any one of two digit number)
- The file name containing 1x01 (or any one of two digit number)
- The file name containing 'season 1 - episode 01' (or any one of two digit number, hyphen can be omitted)

Anything immediately before the S01E01 or 1x01 is treated as the serie's name. If the
last character is a hyphen (-), this is removed first. Periods (.) and underscores (_)
are replaced by space ( ) first. With this name, the script used the TheTVDB.com API to
find the correct serie. A serie is only found if the name matches the serie name exactly.
A semicolon (:) in the serie's name is removed. Names are compared case insensitive. 

For each serie, the script downloads a zip file from TheTVDB.com and extracts it. This
file contains information about each episode. The script will try to match the
season number and the season episode retrieved from the file name to the information
in the file downloaded from TheTVDB.com. When the correct episode has been found, the
thumbnail image is saved in the path used as the input argument when starting the
script.

For each serie, the script has to contact TheTVDB.com to get the serie ID. Once found,
the ID is stored in a database. First, the database is checked for the serie ID,
before TheTVDB.com is contacted. This improves speed, and reduced the number of API call.

The files downloaded from TheTVDB.com are saved. If the file already exists, the file is
not downloaded again. This also improves speed and reduces the load on the TheTVDB.com
server. If the file is more that 6 days old, it will always be retrieved again
from TheTVDB.com, to make sure new episodes are included.

### Movies

If the script determines that a file is not a series, it tries to download the movie
poster from TheMovieDB.org. Movies are also matched using regular expression. The following
patterns are recognised:

- The file name has a year in in, surrounded by (), [], or {}, or not surrounded
- The file file name

First, the name of the parent directory is tried. If no movie can be found, the file name
itself is used. Both the directory and the file name use the same patterns.

## Configuration settings

A number of settings can be configured. Open the file `tw-video-scraper.py`, and
change the settings on top of the page. Documentation is included above each
setting.

## Serie/Movie cannot be found OR Wrong serie/movie is retrieved

If the serie/movie cannot be found, or the wrong serie/movie information is retrieved, there
are some ways to deal with this. The starting point is the name of each video
file. The script must be able to guess the name of the serie or movie from just the file name.
This is done by regular expression. New regular expression patterns can be added by adjusting
the settings.

Sometimes the file name is in a different format, e.g. foo.bar.2011.s01e01.aaa.avi.
This includes the year of the series. The script sees the name as 'foo bar 2011'
and will try to match that. If this cannot be found, no thumbnail will be retrieved. The same
goes for movies. A folder name or file name like 'foo.bar.hdtv.avi' cannot be matched.
One option is to change the name of all the files. Another option is to make (mis)use
of the database. Add a new line to the database with the serie name and the correct
ID, and the script will then always use this ID.

	$ sqlite3 tw-video-scraper.db
	>> insert into video (id,type,name) values (TVDB_ID,'serie','foo bar 2011');
or

	>> insert into video (id,type,name) values (MOVIEDB_ID,'movie','foo bar');
	>> .exit

## Windows users

This script was originally written for Linux operating systems, but it can work on Windows too. You have to make some modifications to the files and install some extra software.

1. Install [Python](http://www.python.org/download/). It is tested with the 2.7.x and 3.2.x releases.
1. If you also want to generate thumbnails if no thumbnail could be found, install [ffmpeg](http://ffmpeg.zeranoe.com/builds/) too.
1. Download the script files via the ZIP package, and extract the files `python-tw-video-scraper.desc`, `python.location`, and `tw-video-scraper.py` to a temporary location, e.g. your desktop.
1. Open the file `python.location` and change it to the path where Python is installed. In the default case `C:\Python27` or `C:\Python32` This should just be the directory, NOT the whole path name including `python.exe`.
1. Open the file `python-tw-video-scraper.desc` and change `/usr/local/twonkymedia/cgi-bin/tw-video-scraper.py` to `"C:\Program Files (x86)\TwonkyMedia\cgi-bin\tw-video-scraper.py"` (with quotes around it, because the path contains a space; replace the path if Twonky is installed somewhere else).
1. Open the file `tw-video-scraper.py` and make some changes there:
	- Change the location of the database to `c:\tmp\tw-video-scraper\tw-video-scraper.db`. You can choose any directory you want, just make sure the script has write access.
	- Change the location of the tmpdir to `c:\tmp\tw-video-scraper`. **Make sure NOT to end this path with \\** Again, you can choose any directory.
	- Change the location of the generatecommand. Replace `ffmpeg` with the full path to ffmpeg, e.g. `"C:\Program Files (x86)\ffmpeg\ffmpeg.exe"` (add quotes around it if the path contains spaces).
1. Make sure Twonky is stopped.
1. Copy the three files to `C:\Program Files (x86)\TwonkyMedia\cgi-bin`.
1. Restart Twonky.
1. Browse using the Flash browser, or using a television that supports thumbnails.

## Future developments

If you can, please contribute by submitting bug/fixes/new code through GitHub.

## Licence & legal stuff

This code may be distributed and adapted under a BSD licence. See the file LICENSE for more
information.

This product is not associated with TwonkyMedia or PacketVideo in any way.
TwonkyMedia server (c)2011 PacketVideo Corporation

This product uses the TheTVDB.com API. You can help support TheTVDB.com
by contributing information and artwork.

This product uses the TMDb API but is not endorsed or certified by TMDb.
