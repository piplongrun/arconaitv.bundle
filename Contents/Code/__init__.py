import os, ssl, urllib2

NAME = 'Arconai TV'
BASE_URL = 'https://www.arconai.tv'
HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0', 'Referer': BASE_URL}
ICON = 'icon-default.jpg'
THUMB = 'thumb-default.jpg'
ART = 'art-default.jpg'

if 'PLEXTOKEN' in os.environ:
	PLEX_TOKEN = os.environ['PLEXTOKEN']
else:
	PLEX_TOKEN = None

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME

	Dict['ts'] = {}

####################################################################################################
@handler('/video/arconaitv', NAME, art=ART, thumb=ICON)
def MainMenu():

	if not PLEX_TOKEN:
		return ObjectContainer(header="Token error", message="Cannot find Plex Media Server token")

	oc = ObjectContainer()
	html = HTML.ElementFromString(HTTPGet(BASE_URL))
	nav = html.xpath('//div[@id="shows"]')[0]

	for channel in nav.xpath('.//a'):

		title = channel.get('title')

		if not title:
			continue

		id = channel.get('href').split('?id=')[-1]

		oc.add(CreateVideoClipObject(
			id = id,
			title = title.strip()
		))

	oc.objects.sort(key=lambda obj: obj.title)
	return oc

####################################################################################################
@route('/video/arconaitv/createvideoclipobject', include_container=bool)
def CreateVideoClipObject(id, title, include_container=False, **kwargs):

	ts = str(Datetime.TimestampFromDatetime(Datetime.Now())).split('.')[0]

	videoclip_obj = VideoClipObject(
		key = Callback(CreateVideoClipObject, id=id, title=title, include_container=True),
		rating_key = id,
		title = title,
		thumb = Resource.ContentsOfURLWithFallback(url='https://piplong.run/t/%s.jpg' % (String.Quote(title.replace(' ', '-').lower())), fallback=THUMB),
		items = [
			MediaObject(
				parts = [
					PartObject(key=HTTPLiveStreamURL(Callback(Playlist, id=id, ts=ts)))
				],
				video_resolution = 'sd',
				audio_channels = 2,
				optimized_for_streaming = True
			)
		]
	)

	if include_container:
		return ObjectContainer(objects=[videoclip_obj])
	else:
		return videoclip_obj

####################################################################################################
@route('/video/arconaitv/playlist.m3u8')
def Playlist(id, ts, **kwargs):

	if ts in Dict['ts']:
		video_url = Dict['ts'][ts]
	else:
		url = '%s/stream.php?id=%s' % (BASE_URL, id)
		page = HTTPGet(url)
		data = Regex("<script>.+(eval\(function\(p,a,c,k,e,.+\.split\('\|'\).+\)\))", Regex.DOTALL).search(page)

		if not data:
			raise Ex.MediaNotAvailable

		data = unpack(data.group(1))
		file = Regex(r"\\'src\\',\\'(.+?)\\'").search(data)

		if not file:
			raise Ex.MediaNotAvailable

		video_url = file.group(1)
		Dict['ts'][ts] = video_url
		Log(" *** Video URL stored for session!")

	original_playlist = HTTPGet(video_url)
	new_playlist = ''

	for line in original_playlist.splitlines():

		if line.startswith('http') or '.ts' in line:
			new_playlist += '/video/arconaitv/segment/%s.ts?X-Plex-Token=%s\n' % (String.Encode(line), PLEX_TOKEN)
		else:
			new_playlist += line + '\n'

	return new_playlist

####################################################################################################
@route('/video/arconaitv/segment/{url}.ts')
def DownloadSegment(url):

	try:
		return HTTPGet(String.Decode(url))
	except:
		return HTTPGet('https://piplong.run/kitten.ts')

####################################################################################################
@route('/video/arconaitv/httpget')
def HTTPGet(url):

	req = urllib2.Request(url, headers=HTTP_HEADERS)
	ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
	data = urllib2.urlopen(req, context=ssl_context).read()

	return data

####################################################################################################
####################################################################################################
"""
    urlresolver XBMC Addon
    Copyright (C) 2013 Bstrdsmkr

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Adapted for use in xbmc from:
    https://github.com/einars/js-beautify/blob/master/python/jsbeautifier/unpackers/packer.py

Unpacker for Dean Edward's p.a.c.k.e.r
"""

def unpack(source):
    """Unpacks P.A.C.K.E.R. packed js code."""
    payload, symtab, radix, count = filterargs(source)

    if count != len(symtab):
        raise UnpackingError('Malformed p.a.c.k.e.r. symtab.')

    try:
        unbase = Unbaser(radix)
    except TypeError:
        raise UnpackingError('Unknown p.a.c.k.e.r. encoding.')

    def lookup(match):
        """Look up symbols in the synthetic symtab."""
        word  = match.group(0)
        return symtab[unbase(word)] or word

    source = Regex(r'\b\w+\b').sub(lookup, payload)
    return replacestrings(source)

def filterargs(source):
    """Juice from a source file the four args needed by decoder."""
    argsregex = (r"}\('(.*)', *(\d+), *(\d+), *'(.*?)'\.split\('\|'\)")
    args = Regex(argsregex).search(source, Regex.DOTALL).groups()

    try:
        return args[0], args[3].split('|'), int(args[1]), int(args[2])
    except ValueError:
        raise UnpackingError('Corrupted p.a.c.k.e.r. data.')

def replacestrings(source):
    """Strip string lookup table (list) and replace values in source."""
    match = Regex(r'var *(_\w+)\=\["(.*?)"\];').search(source, Regex.DOTALL)

    if match:
        varname, strings = match.groups()
        startpoint = len(match.group(0))
        lookup = strings.split('","')
        variable = '%s[%%d]' % varname
        for index, value in enumerate(lookup):
            source = source.replace(variable % index, '"%s"' % value)
        return source[startpoint:]
    return source

class Unbaser(object):
    """Functor for a given base. Will efficiently convert
    strings to natural numbers."""
    ALPHABET  = {
        64 : '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/',
        95 : (' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ'
              '[\]^_`abcdefghijklmnopqrstuvwxyz{|}~')
    }

    def __init__(self, base):
        self.base = base

        # If base can be handled by int() builtin, let it do it for us
        if 2 <= base <= 36:
            self.unbase = lambda string: int(string, base)
        else:
            # Build conversion dictionary cache
            try:
                self.dictionary = dict((cipher, index) for
                    index, cipher in enumerate(self.ALPHABET[base]))
            except KeyError:
                try:
                    self.dictionary = dict((cipher, index) for
                        index, cipher in enumerate(self.ALPHABET[64][:base]))
                except KeyError:
                    raise TypeError('Unsupported base encoding.')

            self.unbase = self.dictunbaser

    def __call__(self, string):
        return self.unbase(string)

    def dictunbaser(self, string):
        """Decodes a  value to an integer."""
        ret = 0
        for index, cipher in enumerate(string[::-1]):
            ret += (self.base ** index) * self.dictionary[cipher]
        return ret

class UnpackingError(Exception):
    """Badly packed source or general error. Argument is a
    meaningful description."""
    pass
