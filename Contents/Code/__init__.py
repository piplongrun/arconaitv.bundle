import base64, certifi, os, requests
requests.packages.urllib3.disable_warnings()

NAME = 'Arconai TV'
BASE_URL = 'https://www.arconaitv.us'
HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:65.0) Gecko/20100101 Firefox/65.0', 'Referer': BASE_URL}
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
	oc.add(DirectoryObject(key = Callback(MediaType, title='TV', type_id='shows'), title='TV', thumb=R(THUMB)))
	oc.add(DirectoryObject(key = Callback(MediaType, title='Movies', type_id='movies'), title='Movies', thumb=R(THUMB)))
	oc.add(DirectoryObject(key = Callback(MediaType, title='Cable', type_id='cable'), title='Cable', thumb=R(THUMB)))

	return oc

####################################################################################################
@route('/video/arconaitv/type/{type_id}')
def MediaType(title, type_id):

	oc = ObjectContainer()
	html = HTML.ElementFromString(requests.get(BASE_URL, headers=HTTP_HEADERS, verify=certifi.where()).text)
	nav = html.xpath('//div[@id="{}"]'.format(type_id))[0]

	for channel in nav.xpath('.//a'):

		title = channel.get('title')

		if not title:
			continue

		if title.endswith(' Movies'):
			title = title.split(' Movies')[0]

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
		rating_key = 'arconaitv:{}'.format(id),
		title = title,
		thumb = 'https://api.piplong.run/assets/images/{}.jpg?_{}'.format(String.Quote(title.replace(' ', '-').lower()), ts[:-4]),
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
		url = '{}/stream.php?id={}'.format(BASE_URL, id)
		html = HTML.ElementFromString(requests.get(url, headers=HTTP_HEADERS, verify=certifi.where()).text)
		js = html.xpath('//script[contains(., "document.getElementsByTagName(\'video\')")]/text()')

		if len(js) < 1:
			raise Ex.MediaNotAvailable

		data = Regex("(eval\(function\(p,a,c,k,e,.+\.split\('\|'\).+\)\))", Regex.DOTALL).search(js[0])

		if not data:
			raise Ex.MediaNotAvailable

		data = requests.post('https://api.piplong.run/jsunpack/', headers={"X-Base64-Encoded": "true"}, data=base64.b64encode(data.group(1)), verify=certifi.where()).text
		file = Regex("'(https:\/\/.+\.m3u8)'").search(data)

		if not file:
			raise Ex.MediaNotAvailable

		video_url = file.group(1)
		Dict['ts'][ts] = video_url
		Log(" *** Video URL stored for session!")

	original_playlist = requests.get(video_url, headers=HTTP_HEADERS, verify=False).text
	new_playlist = ''

	for line in original_playlist.splitlines():

		if line.startswith('http') or '.ts' in line:
			new_playlist += '/video/arconaitv/segment/{}.ts?X-Plex-Token={}\n'.format(String.Encode(line), PLEX_TOKEN)
		elif 'EXT-X-DISCONTINUITY' in line:
			continue
		else:
			new_playlist += line + '\n'

	return new_playlist

####################################################################################################
@route('/video/arconaitv/segment/{url}.ts')
def DownloadSegment(url):

	try:
		return requests.get(String.Decode(url), headers=HTTP_HEADERS, verify=False).content
	except:
		return requests.get('https://api.piplong.run/assets/kitten.ts', headers=HTTP_HEADERS, verify=certifi.where()).content
