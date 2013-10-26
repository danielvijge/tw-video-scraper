settings = {
	# path and name of the sqlite3 database to use
	# use only a file name to use the database in
	# the current working directory
	# Leave empty to disable the database
	'database': r'/var/twonky/TwonkyServer/tw-video-scraper.db',
	
	# Path where to download and extract the files
	# downloaded from TVDB. The script will check
	# if a file already exists, so it will not be
	# downloaded again.
	'tmpdir': r'/tmp/tw-video-scraper/',

	# Log level
	# 1: ERROR only
	# 2: ERROR and WARNING
	# 3: ERROR, WARNING, and INFO
	# 4: ERROR, WARNING, INFO, and DEBUG
	'loglevel': 3,
	# Different kind of messages are coloured
	'colouredoutput': True,

	# List of name of the parent directories
	# Used for matching the directory name of the name
	# of a movie/serie. By knowing the parent dir,the
	# script knows if it should analyse the name
	# E.g. ~/download/my.movie.2011.avi vs. ~/download/My.Movie.2011/part1.avi
	'parentdir': ['download','series','movies','sample'],
	
	# Regular expression patterns to determine if
	# a file is a series. First match should product
	# the title, second match the season, third match
	# the episode number
	'seriepatterns': ['(.*?)S(\d{1,2})E(\d{2})(.*)',
					  '(.*?)\[?(\d{1,2})x(\d{2})\]?(.*)',
					  '(.*?)Season.?(\d{1,2}).*?Episode.?(\d{1,2})(.*)'],
	
	# TVDB api settings
	'tvdbapikey': '6262A88CCAB7E724',
	'tvdblang': 'en',
	
	# Regular expression patterns for movies
	# First try to get the year from the title
	# If that fails, try to match the whole name
	'moviepatterns': ['(.*?)\((\d{4})\)(.*)',
					  '(.*?)\[(\d{4})\](.*)',
					  '(.*?)\{(\d{4})\}(.*)',
					  '(.*?)(\d{4})(.*)',
					  '(.*?)\.(avi|mkv|mpg|mgep|mp4)',
					  '(.*)'],
	# MovieDB api settings
	'moviedbapikey': 'a8b9f96dde091408a03cb4c78477bd14',

	# Preferred size for movie posters, in order of preferability
	'preferred_poster_size': ['w342', 'original', 'w500', 'w185', 'w154', 'w92'],
	# Base URL will be retrieved automatically. Fill this in if you run it without a database
	# and want to limit the API calls to retrieve the configuration
	'moviedb_base_url': '',

	# Files downloaded from TVDB are stored in the tmpdir,
	# and not downloaded if already present. If the file
	# is too old, it will be deleted and downloaded again
	# This is the number of days after which to delete files
	# and download it again
	'cacherenew': 6,

	# Instead of a still from the episode, download the series poster for the first
	# episode (pilot). This allows you to quickly identify the series as a whole
	'posterforpilot': False,

	# By default, images are stored in the cache folder under
	# a subdirectory for the scale. E.g is a media renderer asks
	# for a thumnail, it can request the scale, such as ?scale=100x100
	# Images from this script are stored in that folder, but are saved
	# in the original size.
	# If you have multiple media renderers, they can request thumbnails
	# in different sizes, leading to duplication of images.
	# Valid option for this setting are:
	# none : (Default option) Store images in a scale subdirectory, in the
	#     original size
	# resize : (Requires PIL Image) Store images in a scale subdirectory, resize
	#     the image to the correct scale. If 'keepaspectratio' is set to 
	#     false, the exact scale will be used, otherwise, the aspect ratio 
	#     is preserved, adding black borders
	# symlink : (Linux only) Store images in an 'Original' folder, and make
	#     symbolic links for each entry in 'symbolicfolders'
	'scaleoption': 'symlink',
	'keepaspectratio': 'true',
	'symbolicfolders': ['0x0','100x100','160x160', '1920x1080'],
	
	# Sometimes the downloaded JPEG cannot be in the correct format to display on
	# certain deviced, e.g. the XBOX360 cannot display JPEG not of time JFIF standard
	# Set this to true to this for all images (requires PIL Image)
	'fixjpeg': 'true',
	
	# Save a copy of the image file in the same folder as the movie
	# if 'savelocal' is true, a copy will be saved
	# 'savelocalfilename' controls the name of the local copy. If set to
	# Folder.jpg, the name will be Folder.jpg. If left empty, the name of the
	# local file is the same as the name of the input movie, with the extension
	# replace by .jpg. Thus, movie.2012.avi will be saved as movie.2012.jpg
	# 'savelocalwaysoverwrite' controls if a local file should be overwritten if
	# if already exists
	'savelocal': 'false',
	'savelocalfilename': '',
	'savelocalalwaysoverwrite': 'false',
	
	# If no thumbnail can be found, a thumbnail can be generated
	# using the following command. Leave empty to disable generating
	# thumbnails
	'generatecommand': r'ffmpeg -itsoffset -30 -i "$infile" -y -vcodec mjpeg -vframes 1 -an -f rawvideo -s 624x352 "$outfile"',
}

def main():
	import sys
	
	if not Config['tmpdir'].endswith('/'):
		Config['tmpdir'] = Config['tmpdir']+'/'
	
	inputfile = None
	inputdirectory = None
	outputimage = None
	
	# Validate input arguments
	if len(sys.argv) < 3:
		Console.text("Usage: tw-video-scraper.py inputmovie outputimage")
		exit()

	if Config['scaleoption'] == 'symlink':
		# make symlinks
		try:
			import os, re
			pattern = re.compile('(.*)/(\d{1,4})x(\d{1,4})/(.*)', re.IGNORECASE)
			match = pattern.match(sys.argv[2])
			cachedir = match.group(1)
			if not os.path.isdir(cachedir + '/Original'):
				os.makedirs(cachedir + '/Original')
				os.rmdir(cachedir + '/' + match.group(2) + 'x' + match.group(3))

			for symlink in Config['symbolicfolders']:
				if not os.path.isdir(cachedir + '/' + symlink):
					os.symlink(cachedir + '/Original', cachedir + '/' + symlink)
		except:
			Console.error("Error in making symbolic link folders")
	
	# for windows path names
	if sys.argv[1].find('\\') >= 0:
		sys.argv[1] = sys.argv[1].replace('\\','/')

	serie = Serie(sys.argv[1])
	
	if serie.isSerie():
		thumbnail = serie.getThumbnail()
	else:
		movie = Movie(sys.argv[1])
		thumbnail = movie.getThumbnail()

	if thumbnail:
		Console.info("Downloading file "+thumbnail+"...")
		URL(thumbnail).download(sys.argv[2])
	else:
		file = sys.argv[1]
		if file.find('/') >= 0:
			file = file[file.rindex('/')+1:]
			
		Console.warning("Could not get enough information from file name '"+file+"'")
		if Config['generatecommand'] != '':
			Console.info("Generating thumbnail...")
			try:
				import os
				Config['generatecommand'] = Config['generatecommand'].replace('$infile',sys.argv[1]).replace('$outfile',sys.argv[2])
				os.system(Config['generatecommand'])
			except:
				Console.error("Failed to execute generate thumbnail command")
				
	if Config['fixjpeg'] == 'true':
		try:
			import Image
			image = Image.open(sys.argv[2])
			image.save(sys.argv[2])
		except:
			pass
			
	if Config['savelocal'] == 'true':
		try:
			if Config['savelocalfilename'] == '':
				# if name is empty, take filename
				file = sys.argv[1]
				if file.find('/') >= 0:
					file = file[file.rindex('/')+1:]
				if file.find('.') >= 0:
					file = file[0:file.rindex('.')] + '.jpg'
			else:
				file = Config['savelocalfilename']
			
			if file == '':
				# something went wrong with the file name, exit 'savelocal'
				pass
				
			folder = sys.argv[1]
			if folder.find('/') >= 0:
				folder = folder[0:folder.rindex('/')+1]
			else:
				folder = ''	
									
			import Image, os
			
			if not os.path.isfile(folder + file) or Config['savelocalalwaysoverwrite'] == 'true':
				image = Image.open(sys.argv[2])
				image.save(folder + file)
		except:
			pass

	if Config['scaleoption'] == 'resize':
		# resize the image
		try:
			import Image, re
			# try to get the scale option using regular expression
			pattern = re.compile('(.*)/(\d{1,4})x(\d{1,4})/(.*)', re.IGNORECASE)
			match = pattern.match(sys.argv[2])
			scalewidth = int(match.group(2))
			scaleheight = int(match.group(3))
			
			image = Image.open(sys.argv[2])
			
			if Config['keepaspectratio'] == 'true':
				imagenew = Image.new('RGB', (scaleheight, scalewidth))
				imagewidth = image.size[0]
				imageheight = image.size[1]
				
				# landscape or portait?
				if imageheight > imagewidth:
					imagewidth = int(imagewidth * (float(scaleheight)/float(imageheight)))
					centreoffset = (scalewidth-imagewidth)/2
					image = image.resize((imagewidth, scaleheight), Image.ANTIALIAS)
					imagenew.paste(image, (centreoffset, 0))
				else:
					imageheight = int(imageheight * (float(scalewidth)/float(imagewidth)))
					centreoffset = (scaleheight-imageheight)/2
					image = image.resize((scalewidth, imageheight), Image.ANTIALIAS)
					imagenew.paste(image, (0, centreoffset))
				image = imagenew
			else:
				image = image.resize((scalewidth, scaleheight), Image.ANTIALIAS)
			
			image.save(sys.argv[2])
		except:
			return

	
	
class Serie:
	fileName = None
	file = None
	path = None
	name = None
	id = None
	season = None
	episode = None
	thumbnail = None
	inDB = False
	
	def __init__(self, fileName):
		self.fileName = fileName
		self._parseFileName()
	
	def isSerie(self):
		if self.name and self.season and self.episode and self.id:
			return True
		else:
			return False
		
	def getThumbnail(self):
		if not self.thumbnail:
			self._getTVDBThumbnail()
		return self.thumbnail

	def _parseFileName(self):
		import re

		match = None
		i = 0	
		patterns = Config['seriepatterns']
		
		# Separate the path name and the file name
		if self.fileName.find('/') >= 0:
			self.file = self.fileName[self.fileName.rindex('/')+1:]
			self.path = self.fileName[0:self.fileName.rindex('/')+1]
		else:
			self.file = self.fileName
			self.path = ''
		
		while not match:		
			if i > len(patterns)-1:
				return False
			pattern = re.compile(patterns[i], re.IGNORECASE)
			match = pattern.match(self.file)
			i = i+1

		self.name = self._cleanupFileName(match.group(1))
		self.season = int(match.group(2))
		self.episode = int(match.group(3))
		
		if self._retrieveID():
			return True
		else:
			return False
	
	def _retrieveID(self):
		if db.isEnabled():
			db.execute('SELECT id FROM video WHERE type=\'serie\' and name=\''+db.escape(self.name)+'\'')		
			if db.rowcount() > 0:
				self.id = str(db.fetchrow()[0])
				self.inDB = True
		
		if not self.id:
			import json, re
			
			apicall = URL('http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q='+self.name+' Series Info site:thetvdb.com').json(True)
			if apicall:
				data = json.loads(apicall)

				# Try to match the name from the file with the name from the search results
				# After each result, increase the searchresult counter by 1
				# If no exact match is found, assume that the first search result was the correct one
				searchresult = 0
				for serie in data['responseData']['results']:
					pattern = re.compile('(.*?): Series Info - TheTVDB', re.IGNORECASE)
					match = pattern.match(serie['titleNoFormatting'])
					if match:
						if self._cleanupName(match.group(1)) == self._cleanupName(self.name):
							break
					searchresult = searchresult+1
				else:
					searchresult = 0

				pattern = re.compile('.*?id%3D(\d+).*', re.IGNORECASE)
				match = pattern.match(data['responseData']['results'][searchresult]['url'])
				if match:
					self.id = match.group(1)

				if self.id and db.isEnabled() and self.inDB == False:
					db.execute('INSERT INTO video (id,type,name) VALUES ('+str(db.escape(self.id))+',\'serie\',\''+db.escape(self.name)+'\')')
		return self.id
	
	def _getTVDBThumbnail(self):
		import os, time
		if self.id:
			# check if the file already exists
			if os.path.isfile(Config['tmpdir']+self.id+'-'+Config['tvdblang']+'.xml'):
				# if it is older than config['cacherenew'] days, delete the files and download again
				if os.path.getctime(Config['tmpdir']+self.id+'-'+Config['tvdblang']+'.xml') < time.time()-(Config['cacherenew']*86400):
					os.remove(Config['tmpdir']+self.id+'-'+Config['tvdblang']+'.xml')
			if not os.path.isfile(Config['tmpdir']+self.id+'-'+Config['tvdblang']+'.xml'):
				URL('http://www.thetvdb.com/api/'+Config['tvdbapikey']+'/series/'+self.id+'/all/'+Config['tvdblang']+'.xml').download(Config['tmpdir']+self.id+'-'+Config['tvdblang']+'.xml')
			from xml.etree.ElementTree import ElementTree
			tree = ElementTree()
			try:
				tree.parse(Config['tmpdir']+self.id+'-'+Config['tvdblang']+'.xml')
				if Config['posterforpilot'] == True and self.season == 1 and self.episode == 1:
					series = tree.find('Series')
					if series.find('poster').text:
						self.thumbnail =  'http://www.thetvdb.com/banners/'+series.find('poster').text
						return True
				for episode in tree.findall('Episode'):
					if int(episode.find('SeasonNumber').text) == self.season and int(episode.find('EpisodeNumber').text) == self.episode:			
						if episode.find('filename').text:		
							self.thumbnail =  'http://www.thetvdb.com/banners/'+episode.find('filename').text
							return True
			except:
				pass
		return False
	
	def _cleanupFileName(self, name):
		name = name.lower()
		name = name.replace('.',' ')
		name = name.replace('_',' ')
		name = name.replace('\'',' ')
		name = name.strip()
		if name.endswith('-'):
			name = name[0:len(name)-1]
			name = name.strip()
		return name
	
	def _cleanupName(self, name):
		name = name.lower()
		name = name.replace(':','')
		name = name.replace('/','')
		name = name.replace('\'',' ')
		name = name.strip()
		return name

class Movie:
	fileName = None
	file = None
	path = None
	parentfolder = None
	name = None
	year = None
	id = None
	thumbnail = None
	base_url = None
	poster_size = None
	inDB = False
	
	def __init__(self, fileName):
		self.fileName = fileName
		self._checkMovieDBConfiguration()
		self._parseFileName()

	def _checkMovieDBConfiguration(self):
		import time

		if db.isEnabled():
			for row in db.execute('SELECT key,value,last_updated FROM config WHERE provider=\'themoviedb\''):
				if row[0] == 'base_url' and row[2] > time.time() - 3600*24:
					self.base_url = row[1]
				if row[0] == 'poster_size' and row[2] > time.time() - 3600*24:	
					self.poster_size = row[1]
		elif Config['moviedb_base_url']:
			self.base_url = Config['moviedb_base_url']
			self.poster_size = Config['preferred_poster_size'][0]

		# if the info is not set, retrieve it via API
		if not self.base_url or not self.poster_size:
			self._getMovieDBConfiguration()

	def _getMovieDBConfiguration(self):
		import json
		apicall = URL('https://api.themoviedb.org/3/configuration?api_key='+Config['moviedbapikey']).json(True)
		if apicall:
			data = json.loads(apicall)
			
			self.base_url = data['images']['base_url']
			for poster_size in Config['preferred_poster_size']:
				if poster_size in data['images']['poster_sizes']:
					self.poster_size = poster_size
					break
			else:
				# No preferred poster size could be found. Take the first one to prevent breaking
				self.poster_size = data['images']['poster_sizes'][0]

			if db.isEnabled():
				db.execute('DELETE FROM config WHERE provider=\'themoviedb\'')
				db.execute('INSERT INTO config (provider,key,value,last_updated) VALUES (\'themoviedb\',\'base_url\',\''+db.escape(self.base_url)+'\',strftime(\'%s\',\'now\'))')
				db.execute('INSERT INTO config (provider,key,value,last_updated) VALUES (\'themoviedb\',\'poster_size\',\''+db.escape(self.poster_size)+'\',strftime(\'%s\',\'now\'))')
		else:
			Console.error("Could not connect to TheMovieDB server to retrieve configuration")

	def isMovie(self):
		if self.name and self.id:
			return True
		else:
			return False
			
	def getThumbnail(self):
		return self.thumbnail
		
	def _getMovieDBThumbnail(self, name, year = None):
		import json
		
		match = False
		
		if db.isEnabled():			
			if year:
				db.execute('SELECT id FROM video WHERE type=\'movie\' and name=\''+db.escape(name)+'\' and year='+db.escape(year))
			else:
				db.execute('SELECT id FROM video WHERE type=\'movie\' and name=\''+db.escape(name)+'\'')	
			if db.rowcount() > 0:
				self.id = str(db.fetchrow()[0])
				self.inDB = True
				apicall = URL('http://api.themoviedb.org/3/movie/'+self.id+'?api_key='+Config['moviedbapikey']).json(True)
				if apicall:
					movie = data = json.loads(apicall)
					match = True

		if not self.id:
			if year:
				apicall = URL('http://api.themoviedb.org/3/search/movie?api_key='+Config['moviedbapikey']+'&query='+name+'&year='+year).json(True)
			else:
				apicall = URL('http://api.themoviedb.org/3/search/movie?api_key='+Config['moviedbapikey']+'&query='+name).json(True)

			if apicall:
				data = json.loads(apicall)
				
				if int(data['total_results']) == 0:
					# No results found, no need to parse everything
					return False
				if int(data['total_results']) == 1:
					# If the search has only 1 result, assume that it's the correct movie
					movie = data['results'][0]
					match = True
				
				if match == False:
					for movie in data['results']:
						# try to match the name, and -if exist- the original name
						if self._cleanupName(movie['title']) == name:
							match = True
							break
						if movie['original_title']:
							if self._cleanupName(movie['original_title']) == name:
								match = True
								break
				
		if match:
			if db.isEnabled() and self.inDB == False:
				self.id = movie['id']
				if year:
					db.execute('INSERT INTO video (id,type,name,year) VALUES ('+db.escape(str(self.id))+',\'movie\',\''+db.escape(name)+'\','+db.escape(str(year))+')')
				else:
					db.execute('INSERT INTO video (id,type,name,year) VALUES ('+db.escape(str(self.id))+',\'movie\',\''+db.escape(name)+'\')')	

			if movie['poster_path']:
				self.thumbnail = self.base_url + self.poster_size + movie['poster_path']
				return True
		
		return False
		
	def _cleanupFileName(self, name):
		name = name.lower()
		name = name.replace('.',' ')
		name = name.replace('_',' ')
		name = name.replace('\'',' ')
		name = name.strip()
		return name
		
	def _cleanupName(self, name):
		name = name.lower()
		name = name.replace(':','')
		name = name.replace('/','')
		name = name.replace('\'',' ')
		name = name.strip()
		return name

	def _parseFileName(self):

		match = None
		i = 0	
		patterns = Config['moviepatterns']
		# Separate the path name and the file name
		if self.fileName.find('/') >= 0:
			self.file = self.fileName[self.fileName.rindex('/')+1:]
			self.path = self.fileName[0:self.fileName.rindex('/')+1]
			# remove the last /
			self.parentfolder = self.path[0:len(self.path)-1]
			# this can fail for files in the format ./movie.avi
			try:
				self.parentfolder = self.parentfolder[self.parentfolder.rindex('/')+1:]
			except:
				pass
		else:
			self.file = self.fileName
		
		# If there is a parent folder, first try that match that
		if self.parentfolder and Config['parentdir'].count(self.parentfolder) == 0:
			if self._matchPattern(self.parentfolder):
				if self._getMovieDBThumbnail(self.name, self.year):
					return True	
				
		# If the script comes here, no thumbnail could be found based on the parent directory's name
		# Next, try the file name
		if self._matchPattern(self.file):
			if self._getMovieDBThumbnail(self.name, self.year):
				return True
		
		return False
		
	def _matchPattern(self, matchPattern):
		import re
		
		match = None
		i = 0	
		patterns = Config['moviepatterns']
		
		while not match:		
			if i > len(patterns)-1:
				return False
			pattern = re.compile(patterns[i], re.IGNORECASE)
			match = pattern.match(matchPattern)
			i = i+1

		self.name = self._cleanupFileName(match.group(1))
		if len(match.groups()) > 1:
			# second match could also be avi,mkv,..., so check if it's an integer
			try:
				if int(match.group(2).strip()):
					self.year = match.group(2).strip()
			except:
				self.year = None
	
		if self.name:
			return True
			
		return False
		
class Database:
	_sql = None
	_result = None
	_enabled = False
	_row = 0
	
	def __init__(self, database = None):
		if database:
			try:
				import sqlite3, os
				
				dbdir = Config['database'].replace('\\','/')
				if dbdir.find('/') >= 0:
					dbdir = dbdir[0:dbdir.rindex('/')+1]
				if not os.path.isdir(dbdir):
					os.makedirs(dbdir)
			
				self._sql = sqlite3.connect(database)
			
				self.execute('create table if not exists video (id int, type text, name text, year int)')
				self.execute('create table if not exists config (provider text, key text, value text, last_updated int)')
				
				self._enabled = True
			except:
				Console.warning("Could not open/create database. Running without database...")
		else:
			Console.info("Database disabled. Running without database...")

	def isEnabled(self):
		return self._enabled

	def execute(self, query):
		if not self._sql:
			return False
		try:
			self._result = self._sql.execute(query)
			self._sql.commit()
			self._result = self._result.fetchall()
			self._row = 0
			return self._result
		except:
			return False
	
	def close(self):
		if not self._sql:
			return False
		self._sql.close()
		
	def rowcount(self):
		if not self._sql:
			return False
		try:
			return len(self._result)
		except:
			return False
	
	def fetchrow(self):
		if not self._sql:
			return False
		if len(self._result) == 0:
			return []
		if len(self._result) <= self._row:
			return None
		t = self._result[self._row]
		self._row = self._row+1
		return t
	
	def fetchall(self):
		if not self._sql:
			return False
		return self._result

	def escape(self, str):
		return str.replace("'",'').replace('"','')

class URL:
	url = None
	ver = 2
	
	def __init__(self, url):
		import sys
		if sys.version_info[0] > 2:
			self.ver = 3
		self.url = url.replace(' ','%20')
		
	def open(self):
		if self.ver == 3:
			import urllib.request
			try:
				return urllib.request.urlopen(self.url)
			except:
				return None
		else:
			import urllib
			try:
				return urllib.urlopen(self.url)
			except:
				return None

	def json(self, asString = False):
		Console.debug('Retrieving JSON for ' + self.url)
		if self.ver == 3:
			import urllib.request
			try:
				response = urllib.request.urlopen(urllib.request.Request(self.url, None, {'accept': 'application/json'}))
				if asString:
					return response.read().decode('utf-8')
				else:
					return response
			except:
				return None
		else:
			import urllib2
			try:
				response = urllib2.urlopen(urllib2.Request(self.url, None, {'accept': 'application/json'}))
				if asString:
					return response.read()
				else:
					return response
			except:
				return None
	
	def download(self, location):
		if self.ver == 3:
			import urllib.request
			try:
				if urllib.request.urlretrieve(self.url, location):
					return True
				else:
					return False
			except:
				return False
		else:
			import urllib
			try:
				if urllib.urlretrieve(self.url, location):
					return True
				else:
					return False
			except:
				return False

class PrintLog:
	_YELLOW = '\033[33m'
	_BLUE = '\033[94m'
	_GREEN = '\033[32m'
	_RED = '\033[31m'
	_ENDC = '\033[0m'

	_loglevel = 0

	def __init__(self, loglevel = 3, colour = True):
		self._loglevel = loglevel

		if colour == False:
			self._YELLOW = ''
			self._BLUE = ''
			self._GREEN = ''
			self._RED = ''
			self._ENDC = ''

	def _print(self, text, texttype):
		STARTCOLOUR = ''
		ENDSEQ = ''
		if texttype == 'error':
			STARTCOLOUR = self._RED
			ENDSEQ = self._ENDC
		elif texttype == 'warning':
			STARTCOLOUR = self._YELLOW
			ENDSEQ = self._ENDC
		elif texttype == 'info':
			STARTCOLOUR = ''
			ENDSEQ = ''
		elif texttype == 'debug':
			STARTCOLOUR = self._BLUE
			ENDSEQ = self._ENDC

		print(STARTCOLOUR + text + ENDSEQ)

	def text(self, text):
		if self._loglevel >= 0:
			self._print(text, 'text')

	def error(self, text):
		if self._loglevel >= 1:
			self._print(text, 'error')

	def warning(self, text):
		if self._loglevel >= 2:
			self._print(text, 'warning')

	def info(self, text):
		if self._loglevel >= 3:
			self._print(text, 'info')

	def debug(self, text):
		if self._loglevel >= 4:
			self._print(text, 'debug')
		
Config = dict(settings)
Console = PrintLog(Config['loglevel'], Config['colouredoutput'])
db = Database(Config['database'])
main()
db.close()
