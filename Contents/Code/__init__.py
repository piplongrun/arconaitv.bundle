import os

NAME = 'Arconai TV'
BASE_URL = 'http://arconaitv.me'
HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:54.0) Gecko/20100101 Firefox/54.0', 'Referer': BASE_URL}
ICON = 'icon-default.jpg'
ART = 'art-default.jpg'

if 'PLEXTOKEN' in os.environ:
	PLEX_TOKEN = os.environ['PLEXTOKEN']
else:
	PLEX_TOKEN = None

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME

####################################################################################################
@handler('/video/arconaitv', NAME, art=ART, thumb=ICON)
def MainMenu():

	if not PLEX_TOKEN:
		return ObjectContainer(header="Token error", message="Cannot find Plex Media Server token")

	oc = ObjectContainer()
	html = HTML.ElementFromURL(BASE_URL, headers=HTTP_HEADERS, cacheTime=CACHE_1DAY)
	nav = html.xpath('//div[@id="shows"]')[0]

	for channel in nav.xpath('.//a'):

		title = channel.get('title')

		if not title:
			continue

		id = channel.get('href').split('?id=')[-1]

		oc.add(CreateVideoClipObject(
			id = id,
			title = title
		))

	oc.objects.sort(key=lambda obj: obj.title)
	return oc

####################################################################################################
@route('/video/arconaitv/createvideoclipobject', include_container=bool)
def CreateVideoClipObject(id, title, include_container=False, **kwargs):

	videoclip_obj = VideoClipObject(
		key = Callback(CreateVideoClipObject, id=id, title=title, include_container=True),
		rating_key = id,
		title = title,
		thumb = R(ICON),
		items = [
			MediaObject(
				parts = [
					PartObject(key=HTTPLiveStreamURL(Callback(Playlist, id=id)))
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
def Playlist(id, **kwargs):

	url = '%s/stream.php?id=%s' % (BASE_URL, id)

	html = HTML.ElementFromURL(url, headers=HTTP_HEADERS, cacheTime=300)
	video_url = html.xpath('//source[contains(@src, ".m3u8")]/@src')[0]

	try:
		original_playlist = HTTP.Request(video_url, headers=HTTP_HEADERS, cacheTime=0).content
	except:
		try:
			original_playlist = HTTP.Request(video_url, headers=HTTP_HEADERS, cacheTime=0).content
		except:
			raise Ex.MediaNotAvailable

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
		return HTTP.Request(String.Decode(url), headers=HTTP_HEADERS, cacheTime=0, timeout=1.0).content
	except:
		return HTTP.Request('http://localhost:32400/:/plugins/com.plexapp.plugins.arconaitv/resources/kitten.ts?X-Plex-Token=%s' % (PLEX_TOKEN)).content
