NAME = 'Arconai TV'
BASE_URL = 'http://arconaitv.me'
HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1 Safari/603.1.30'}
ICON = 'icon-default.jpg'
ART = 'art-default.jpg'

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME

####################################################################################################
@handler('/video/arconaitv', NAME, art=ART, thumb=ICON)
def MainMenu():

	oc = ObjectContainer()
	html = HTML.ElementFromURL(BASE_URL)
	nav = html.xpath('//div[@id="shows"]')[0]

	for channel in nav.xpath('.//a'):

		id = channel.get('href').split('?id=')[-1]
		title = channel.get('title')

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
@route('/video/arconaitv/playvideo.m3u8')
@indirect
def PlayVideo(id, **kwargs):

	html = HTML.ElementFromURL('%s/stream.php?id=%s' % (BASE_URL, id))
	video_url = html.xpath('//source[contains(@src, ".m3u8")]/@src')[0]

	return IndirectResponse(VideoClipObject, key=video_url)
