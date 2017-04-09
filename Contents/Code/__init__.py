NAME = 'Arconai TV'
BASE_URL = 'https://ssl-proxy.my-addr.org/myaddrproxy.php/https/www.arconaitv.me/'
HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36'}
ICON = 'icon-default.jpg'
ART = 'art-default.jpg'

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME

####################################################################################################
@handler('/video/arconaitv', NAME, art=ART, thumb=ICON)
def MainMenu():

	oc = ObjectContainer()
	html = HTML.ElementFromURL(BASE_URL, cacheTime=CACHE_1HOUR, headers=HTTP_HEADERS)
	nav = html.xpath('//ul[@class="mega_dropdown"]')[0]

	for channel in nav.xpath('.//a'):

		id = channel.get('href').split('/')[-2]

		if 'arconaitv.me' in id:
			continue

		title = channel.xpath('./span/span/text()')[0].strip()

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
					PartObject(key=HTTPLiveStreamURL(Callback(PlayVideo, id=id)))
				],
				video_resolution = 'sd',
				optimized_for_streaming = True
			)
		]
	)

	if include_container:
		return ObjectContainer(objects=[videoclip_obj])
	else:
		return videoclip_obj

####################################################################################################
@route('/video/arconaitv/playvideo.m3u8')
@indirect
def PlayVideo(id, **kwargs):

	html = HTML.ElementFromURL('%s%s/' % (BASE_URL, id), cacheTime=60, headers=HTTP_HEADERS)
	video_url = html.xpath('//video/source/@src')[0].split('/http/')[-1]
	video_url = 'http://%s' % (video_url)

	return IndirectResponse(VideoClipObject, key=video_url)
