settings = {
	# path and name of the sqlite3 database to use
	# use only a file name to use the database in
	# the current working directory
	# Leave empty to disable the database
	'database': '/var/twonkymedia/twonkymedia/tw-video-scraper.db',
	
	# Path where to download and extract the files
	# downloaded from TVDB. The script will check
	# if a file already exists, so it will not be
	# downloaded again.
	'tmpdir': '/tmp/tw-video-scraper/',

	# List of name of the parent directories
	# Used for matching the directory name of the name
	# of a movie/serie. By knowing the parent dir,the
	# script knows if it should analyse the name
	# E.g. ~/download/my.movie.2011.avi vs. ~/download/My.Movie.2011/part1.avi
	'parentdir': ['download','series','movies'],
	
	# Regular expression patterns to determine if
	# a file is a series. First match should product
	# the title, second match the season, third match
	# the episode number
	'seriepatterns': ['(.*?)S(\d{1,2})E(\d{2})(.*)',
					  '(.*?)\[?(\d{1,2})x?(\d{2})\]?(.*)',
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
					  '(.*)'],
	# MovieDB api settings
	'moviedbapikey': 'a8b9f96dde091408a03cb4c78477bd14',

	# Files downloaded from TVDB are stored in the tmpdir,
	# and not downloaded if already present. If the file
	# is too old, it will be deleted and downloaded again
	# This is the number of days after which to delete files
	# and download it again
	'cacherenew': 6,
	
	# If no thumbnail can be found, a thumbnail can be generated
	# using the following command. Leave empty to disable generating
	# thumbnails
	'generatecommand': 'ffmpeg -itsoffset -30 -i "$infile" -y -vcodec mjpeg -vframes 1 -an -f rawvideo -s 624x352 "$outfile"',
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
		print "Usage: tw-video-scraper.py inputmovie outputimage"
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
		print 'Downloading file '+thumbnail+'...'
		URL(thumbnail).download(sys.argv[2])
	else:
		file = sys.argv[1]
		if file.find('/') >= 0:
			file = file[file.rindex('/')+1:]
			
		print 'Could not get enough information from file name \''+file+'\''
		if Config['generatecommand'] != '':
			print 'Generating thumbnail...'
			try:
				#import subprocess as sub
				import os
				Config['generatecommand'] = Config['generatecommand'].replace('$infile',sys.argv[1]).replace('$outfile',sys.argv[2])
				os.system(Config['generatecommand'])
				#p = sub.Popen(Config['generatecommand'],stdout=sub.PIPE,stderr=sub.PIPE,shell=True)
				#output, errors = p.communicate()
			except:
				print 'Failed to execute generate thumbnail command'
				
	
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

		self.name = match.group(1).replace('.',' ').replace('_',' ').lower().strip()
		self.season = int(match.group(2))
		self.episode = int(match.group(3))
		
		if self.name.endswith('-'):
			self.name = self.name[0:len(self.name)-1].strip()
		
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
			apicall = URL('http://www.thetvdb.com/api/GetSeries.php?language=en&seriesname='+self.name).open()
			if apicall:
				from xml.dom import minidom
				dom = minidom.parse(apicall)
				for node in dom.getElementsByTagName('Series'):
					if node.getElementsByTagName('SeriesName')[0].firstChild.nodeValue.lower().replace(':','').replace('/','') == self.name:
						self.id = node.getElementsByTagName('seriesid')[0].firstChild.nodeValue
				
				if self.id and db.isEnabled():
					db.execute('INSERT INTO video (id,type,name) VALUES ('+str(db.escape(self.id))+',\'serie\',\''+db.escape(self.name)+'\')')
			else:
				print 'Could not connect to theTVDB.com server.'
		
		return self.id
	
	
	def _getTVDBzipfile(self):
		import os, time
		if not os.path.isdir(Config['tmpdir']+self.id):
			os.makedirs(Config['tmpdir']+self.id)
		if os.path.isfile(Config['tmpdir']+self.id+'/'+Config['tvdblang']+'.xml'):
			if os.path.getctime(Config['tmpdir']+self.id+'/'+Config['tvdblang']+'.xml') < time.time()-(Config['cacherenew']*86400):
				os.remove(Config['tmpdir']+self.id+'/'+Config['tvdblang']+'.xml')
				os.remove(Config['tmpdir']+self.id+'/banners.xml')
				os.remove(Config['tmpdir']+self.id+'/actors.xml')
				os.remove(Config['tmpdir']+self.id+'.zip')
		if not os.path.isfile(Config['tmpdir']+self.id+'/'+Config['tvdblang']+'.xml'):
			if URL('http://www.thetvdb.com/api/'+Config['tvdbapikey']+'/series/'+self.id+'/all/'+Config['tvdblang']+'.zip').download(Config['tmpdir']+self.id+'.zip'):
				Zip(Config['tmpdir']+self.id+'.zip').extract(Config['tmpdir']+self.id)			
				return True
		else:
			# zip and xml file are already downloaded, no need to download again	
			return True

		print 'Error retrieving/processing files from theTVDB.com'
		return False
	
	def _getTVDBThumbnail(self):
		from xml.dom import minidom
		
		if self.id:
			if self._getTVDBzipfile():
				dom = minidom.parse(Config['tmpdir']+self.id+'/'+Config['tvdblang']+'.xml')
				for node in dom.getElementsByTagName('Episode'):
					if int(node.getElementsByTagName('SeasonNumber')[0].firstChild.nodeValue) == self.season and int(node.getElementsByTagName('EpisodeNumber')[0].firstChild.nodeValue) == self.episode:			
						if node.getElementsByTagName('filename')[0].firstChild:		
							self.thumbnail =  'http://www.thetvdb.com/banners/'+node.getElementsByTagName('filename')[0].firstChild.nodeValue
							return True
		return False

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
		from xml.dom import minidom
		
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
			dom = minidom.parse(apicall)
			if int(dom.getElementsByTagName('opensearch:totalResults')[0].firstChild.nodeValue) == 1:
				# If the search has only 1 result, presume that's the correct movie
				match = True
			
			for node in dom.getElementsByTagName('movie'):
				# try to match the name, and -if exist- the original name or alternative name
				if self._cleanupName(node.getElementsByTagName('name')[0].firstChild.nodeValue) == name:
					match = True
				if node.getElementsByTagName('original_name') and node.getElementsByTagName('original_name')[0].firstChild:
					if self._cleanupName(node.getElementsByTagName('original_name')[0].firstChild.nodeValue) == name:
						match = True
				if node.getElementsByTagName('alternative_name') and node.getElementsByTagName('alternative_name')[0].firstChild:
					if self._cleanupName(node.getElementsByTagName('alternative_name')[0].firstChild.nodeValue) == name:
						match = True
				
				if match:
					
					if db.isEnabled():
						self.id = node.getElementsByTagName('id')[0].firstChild.nodeValue
						if year:
							db.execute('INSERT INTO video (id,type,name,year) VALUES ('+str(db.escape(self.id))+',\'movie\',\''+db.escape(name)+'\','+db.escape(year)+')')
						else:
							db.execute('INSERT INTO video (id,type,name,year) VALUES ('+str(db.escape(self.id))+',\'movie\',\''+db.escape(name)+'\')')	

					if node.getElementsByTagName('images')[0]:
						for node2 in node.getElementsByTagName('image'):
							if node2.attributes['type'].nodeValue == 'poster' and node2.attributes['size'].nodeValue == 'cover':
								self.thumbnail = node2.attributes['url'].nodeValue
								return True
				# Set to False, for the next run of the loop
				match = False
		
		return False
		
	def _cleanupName(self, name):
		name = name.lower()
		name = name.replace(':','')
		name = name.replace('/','')
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

		self.name = match.group(1).replace('.',' ').replace('_',' ').lower().strip()
		if len(match.groups()) > 1:
			self.year = match.group(2).strip()
	
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
				import sqlite3
			
				self._sql = sqlite3.connect(database)
			
				self._result = self._sql.execute('create table if not exists video (id int, type text, name text, year int)')
				self._sql.commit()
				self._enabled = True
			except:
				print "Could not open/create database. Running without database..."
		else:
			print "Database disabled. Running without database..."

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
	
	def __init__(self, url):
		self.url = url
	
	def open(self):
		import urllib
		try:
			return urllib.urlopen(self.url)
		except:
			return None
	
	def download(self, location):
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
