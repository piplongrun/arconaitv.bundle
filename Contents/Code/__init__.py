import base64, os, ssl, urllib2

NAME = 'Arconai TV'
BASE_URL = 'https://www.arconaitv.us'
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
		thumb = 'https://piplong.run/t/%s.jpg?_%s' % (String.Quote(title.replace(' ', '-').lower()), ts[:-4]),
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
		html = HTML.ElementFromString(HTTPGet(url))
		js = html.xpath('//script[contains(., "document.getElementsByTagName(\'video\')")]/text()')

		if len(js) < 1:
			raise Ex.MediaNotAvailable

		data = HTTP.Request('https://piplong.run/api/jsunpack/', headers={"X-Api-Key": "5e3e6f60bd1fa12f26a64a776a8ae463", "X-Base64-Encoded": "true"}, data=base64.b64encode(js[0].split(';', 1)[-1])).content
		file = Regex("'src','(.+?)'").search(data)

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
