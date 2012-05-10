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

	# Files downloaded from TVDB are stored in the tmpdir,
	# and not downloaded if already present. If the file
	# is too old, it will be deleted and downloaded again
	# This is the number of days after which to delete files
	# and download it again
	'cacherenew': 6,

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
		print("Usage: tw-video-scraper.py inputmovie outputimage")
		exit()
	
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
		print("Downloading file "+thumbnail+"...")
		URL(thumbnail).download(sys.argv[2])
	else:
		file = sys.argv[1]
		if file.find('/') >= 0:
			file = file[file.rindex('/')+1:]
			
		print("Could not get enough information from file name '"+file+"'")
		if Config['generatecommand'] != '':
			print("Generating thumbnail...")
			try:
				import os
				Config['generatecommand'] = Config['generatecommand'].replace('$infile',sys.argv[1]).replace('$outfile',sys.argv[2])
				os.system(Config['generatecommand'])
			except:
				print("Failed to execute generate thumbnail command")
				
	if Config['fixjpeg'] == 'true':
		try:
			import Image
			image = Image.open(sys.argv[2])
			image.save(sys.argv[2])
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

	if Config['scaleoption'] == 'symlink':
		# make symlinks
		try:
			import os, shutil, re
			pattern = re.compile('(.*)/(\d{1,4})x(\d{1,4})/(.*)', re.IGNORECASE)
			match = pattern.match(sys.argv[2])
			cachedir = match.group(1)
			if not os.path.isdir(cachedir + '/Original'):
				os.makedirs(cachedir + '/Original')
				shutil.move(sys.argv[2], cachedir + '/Original/' + match.group(4))
				os.rmdir(cachedir + '/' + match.group(2) + 'x' + match.group(3))
			for symlink in Config['symbolicfolders']:
				if not os.path.isdir(cachedir + '/' + symlink):
					os.symlink(cachedir + '/Original', cachedir + '/' + symlink)
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
		
		if not self.id:
			apicall = URL('http://www.thetvdb.com/api/GetSeries.php?language='+Config['tvdblang']+'&seriesname='+self.name).open()
			if apicall:
				from xml.etree.ElementTree import ElementTree
				tree = ElementTree()
				tree.parse(apicall)
				for series in tree.findall('Series'):
					if self._cleanupName(series.find('SeriesName').text) == self.name:
						self.id = series.find('seriesid').text
				
				if self.id and db.isEnabled():
					db.execute('INSERT INTO video (id,type,name) VALUES ('+str(db.escape(self.id))+',\'serie\',\''+db.escape(self.name)+'\')')
			else:
				print("Could not connect to theTVDB.com server.")
		return self.id
	
	
	def _getTVDBzipfile(self):
		import os, time
		# make a temp dir if it does not exist
		if not os.path.isdir(Config['tmpdir']+self.id):
			os.makedirs(Config['tmpdir']+self.id)
		# check if the file already exists
		if os.path.isfile(Config['tmpdir']+self.id+'/'+Config['tvdblang']+'.xml'):
			# if it is older than config['cacherenew'] days, delete the files and download again
			if os.path.getctime(Config['tmpdir']+self.id+'/'+Config['tvdblang']+'.xml') < time.time()-(Config['cacherenew']*86400):
				os.remove(Config['tmpdir']+self.id+'/'+Config['tvdblang']+'.xml')
				os.remove(Config['tmpdir']+self.id+'/banners.xml')
				os.remove(Config['tmpdir']+self.id+'/actors.xml')
				os.remove(Config['tmpdir']+self.id+'.zip')
		# if the file does not exists, download it
		if not os.path.isfile(Config['tmpdir']+self.id+'/'+Config['tvdblang']+'.xml'):
			if URL('http://www.thetvdb.com/api/'+Config['tvdbapikey']+'/series/'+self.id+'/all/'+Config['tvdblang']+'.zip').download(Config['tmpdir']+self.id+'.zip'):
				Zip(Config['tmpdir']+self.id+'.zip').extract(Config['tmpdir']+self.id)			
				return True
		else:
			# zip and xml file are already downloaded, no need to download again	
			return True

		print("Error retrieving/processing files from theTVDB.com")
		return False
	
	def _getTVDBThumbnail(self):
		if self.id:
			if self._getTVDBzipfile():
				from xml.etree.ElementTree import ElementTree
				tree = ElementTree()
				tree.parse(Config['tmpdir']+self.id+'/'+Config['tvdblang']+'.xml')
				for episode in tree.findall('Episode'):
					if int(episode.find('SeasonNumber').text) == self.season and int(episode.find('EpisodeNumber').text) == self.episode:			
						if episode.find('filename').text:		
							self.thumbnail =  'http://www.thetvdb.com/banners/'+episode.find('filename').text
							return True
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
	
	def __init__(self, fileName):
		self.fileName = fileName
		self._parseFileName()
	
	def isMovie(self):
		if self.name and self.id:
			return True
		else:
			return False
			
	def getThumbnail(self):
		return self.thumbnail
		
	def _getMovieDBThumbnail(self, name, year = None):
		from xml.etree.ElementTree import ElementTree
		tree = ElementTree()
		
		match = False
		
		if db.isEnabled():			
			if year:
				db.execute('SELECT id FROM video WHERE type=\'movie\' and name=\''+db.escape(name)+'\' and year='+db.escape(year))
			else:
				db.execute('SELECT id FROM video WHERE type=\'movie\' and name=\''+db.escape(name)+'\'')	
			if db.rowcount() > 0:
				self.id = str(db.fetchrow()[0])
				apicall = URL('http://api.themoviedb.org/2.1/Movie.getInfo/en/xml/'+Config['moviedbapikey']+'/'+self.id).open()

		if not self.id:
			if year:
				apicall = URL('http://api.themoviedb.org/2.1/Movie.search/en/xml/'+Config['moviedbapikey']+'/'+name+' '+year).open()
			else:
				apicall = URL('http://api.themoviedb.org/2.1/Movie.search/en/xml/'+Config['moviedbapikey']+'/'+name).open()
		
		if apicall:
			tree.parse(apicall)
			if int(tree.find('{%s}totalResults' % 'http://a9.com/-/spec/opensearch/1.1/').text) == 0:
				# No results found, no need to parse everything
				return False
			if int(tree.find('{%s}totalResults' % 'http://a9.com/-/spec/opensearch/1.1/').text) == 1:
				# If the search has only 1 result, assume that's the correct movie
				match = True
			
			for movie in tree.findall('movies/movie'):
				# try to match the name, and -if exist- the original name or alternative name
				if self._cleanupName(movie.find('name').text) == name:
					match = True
				if movie.find('original_name').text:
					if self._cleanupName(movie.find('original_name').text) == name:
						match = True
				if movie.find('alternative_name').text:
					if self._cleanupName(movie.find('alternative_name').text) == name:
						match = True
				
				if match:
					
					if db.isEnabled():
						self.id = movie.find('id').text
						if year:
							db.execute('INSERT INTO video (id,type,name,year) VALUES ('+str(db.escape(self.id))+',\'movie\',\''+db.escape(name)+'\','+db.escape(year)+')')
						else:
							db.execute('INSERT INTO video (id,type,name,year) VALUES ('+str(db.escape(self.id))+',\'movie\',\''+db.escape(name)+'\')')	

					if movie.findall('images/image'):
						for image in movie.findall('images/image'):
							if image.attrib['type'] == 'poster' and image.attrib['size'] == 'cover':
								self.thumbnail = image.attrib['url']
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
			self.parentfolder = self.parentfolder[self.parentfolder.rindex('/')+1:]
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
			
				self._result = self._sql.execute('create table if not exists video (id int, type text, name text, year int)')
				self._sql.commit()
				self._enabled = True
			except:
				print("Could not open/create database. Running without database...")
		else:
			print("Database disabled. Running without database...")

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

class Zip:
	zipfile = None
	
	def __init__(self, zipfile):
		self.zipfile = zipfile
	
	def extract(self, location):
		import zipfile, os
		try:
			if not location.endswith('/'):
				location = location+'/'
			fh = open(self.zipfile, 'rb')
			z = zipfile.ZipFile(fh)
			for name in z.namelist():
				if name.endswith('/'):
					os.makedirs(location+name)
				else:
					outfile = open(location+name, 'wb')
					outfile.write(z.read(name))
					outfile.close()
			fh.close()
		except:
			return

Config = dict(settings)
db = Database(Config['database'])
main()
db.close()
