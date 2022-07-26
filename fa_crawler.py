from kh_common.gateway import ClientResponse, Gateway
from kh_common.hashing import Hashable
from lxml.html import fromstring
from kh_common.config.credentials import furaffinity


class First :
	def __init__(self, method=None) :
		self.method = method

	def __call__(self, it) :
		try :
			return next(filter(self.method, it))
		except (TypeError, StopIteration) :
			return None

first = First()


class SiteNotCrawled(Exception) :
	pass


def isint(s) :
	try : return int(s)
	except : return None


FurAffinityGateway: Gateway = Gateway('https://www.furaffinity.net/view/{id}', decoder=ClientResponse.text)


class FurAffinityCrawler(Hashable) :

	submissionTypes = { 'story', 'music' }
	xpathargs = { 'regexp': False, 'smart_strings': False }

	async def crawl(self: 'FurAffinityCrawler', post_id: int) :
		html = await FurAffinityGateway(id=post_id, headers=furaffinity['headers'])
		document = fromstring(html)
		return self.parse(document)


	def parse(self: 'FurAffinityCrawler', document) :
		# check that the website isn't down and etc etc
		if first(document.xpath('//body//div[@class="attribution"]/a/text()', **self.xpathargs)) == 'DDoS protection by Cloudflare' :
			raise SiteNotCrawled('furaffinity is currently behind cloudflare.')

		if first(document.xpath('//body/@id', **self.xpathargs)) == 'pageid-matureimage-error' :
			raise SiteNotCrawled('furaffinity login error.')

		elif document.xpath('//head/title[contains(text(), "System Error")]', **self.xpathargs) and document.xpath('//body/section/div[@class="section-body" and contains(text(), "The submission you are trying to find is not in our database")]', **self.xpathargs) :
			raise SiteNotCrawled('url does not have a submission.')

		elif document.xpath('//img[@src="/fa_offline.jpg"]', **self.xpathargs) :
			raise SiteNotCrawled('furaffinity is currently offline.')

		# now we can actually crawl

		image_url = first(document.xpath('//img[@id="submissionImg"]/@src', **self.xpathargs))
		if not image_url :
			raise SiteNotCrawled('submission does not contain an image.')

		filetype = document.xpath('//div[@class="submission-content"]//center[contains(@class, "p20")]/div[contains(strong/text(), "File type")]', **self.xpathargs)
		if filetype :
			raise SiteNotCrawled('submission is not an image.')

		timestamp = image_url.split('/')[5]  # this will ALWAYS be [5]

		if isint(timestamp) is not None :
			timestamp = int(timestamp)
			uploadTimestamp = image_url.split('/')[6]
			uploadTimestamp = int(uploadTimestamp[:uploadTimestamp.find('.')])

		elif timestamp in FurAffinityCrawler.submissionTypes :
			raise SiteNotCrawled (f'submission is not an image. type: {timestamp}.')

		else :
			raise SiteNotCrawled(f'could not find image id (timestamp) from image url. image_url: {image_url}, timestamp: {timestamp}.')

		if image_url.startswith('//') :
			image_url = 'https:' + image_url

		artist = first(document.xpath('//div[@class="submission-id-container"]//a[contains(@href, "/user/") and strong]', **self.xpathargs))
		artist_url = None

		if artist :
			artist_url = first(artist.xpath('@href', **self.xpathargs))

			if artist_url :
				artist_url = 'https://www.furaffinity.net' + artist_url

			else :
				raise SiteNotCrawled('could not find artist url in html.')

			artist = first(artist.xpath('strong/text()', **self.xpathargs))

		if not artist :
			raise SiteNotCrawled('could not find artist in html.')

		description = ''.join(document.xpath('//div[@class="submission-content"]/section/div[@class="section-body"]/div[contains(@class, "submission-description")]//text()', **self.xpathargs)).strip()

		title = first(document.xpath('//div[@class="submission-id-container"]//div[@class="submission-title"]//p/text()', **self.xpathargs))
		if not title :
			self.logger.warning(f'could not find submission title in html. url: {self.url}')

		return {
			'image': image_url,
			'title': title,
			'timestamp': uploadTimestamp,
			'description': description,
			'artist': artist,
			'artist_url': artist_url,
		}
