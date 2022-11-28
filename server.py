from fastapi.responses import FileResponse, HTMLResponse
from kh_common.caching import ArgsCache, SimpleCache
from kh_common.server import Request, ServerApp
from fa_crawler import FurAffinityCrawler
from kh_common.logging import getLogger
from html import escape


logger = getLogger()
app = ServerApp(
	auth=False,
	allowed_hosts=[
		'fxraffinity.net',
		'fxfuraffinity.net',
		'vxfuraffinity.net',
		'*.fxraffinity.net',
		'*.fxfuraffinity.net',
		'*.vxfuraffinity.net',
		'localhost',
	],
)
crawler = FurAffinityCrawler()
generate_embed_user_agents = {
	"facebookexternalhit/1.1",
	"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36",
	"Mozilla/5.0 (Windows; U; Windows NT 10.0; en-US; Valve Steam Client/default/1596241936; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36",
	"Mozilla/5.0 (Windows; U; Windows NT 10.0; en-US; Valve Steam Client/default/0; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36", 
	"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.4 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.4 facebookexternalhit/1.1 Facebot Twitterbot/1.0", 
	"facebookexternalhit/1.1",
	"Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; Valve Steam FriendsUI Tenfoot/0; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36", 
	"Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)", 
	"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0", 
	"Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)", 
	"TelegramBot (like TwitterBot)", 
	"Mozilla/5.0 (compatible; January/1.0; +https://gitlab.insrt.uk/revolt/january)", 
	"test",
}
thumbnail_cutoff: int = 1280 ** 2


@SimpleCache(float('inf'))
def index() :
	with open('index.html') as file :
		return file.read()


@app.get('/')
async def v1Home(req: Request) :
	return HTMLResponse(index().replace('{hostname}', req.url.hostname))


@app.get('/favicon.ico')
async def favicon() :
	return FileResponse('favicon.ico')


@ArgsCache(TTL_days=1)
async def _fetch_fa_post(id: int) :
	return await crawler.crawl(id)


@app.get('/view/{post_id}')
@app.get('/full/{post_id}')
@app.get('/{post_id}')
async def v1Post(req: Request, post_id: int, full: str = None) :
	data = await _fetch_fa_post(post_id)
	image = data['image']

	if data['resolution'] and full is None :
		if data['resolution'][0] * data['resolution'][1] > thumbnail_cutoff :
			image = data['thumbnails'][-1]

	return HTMLResponse(
		(
			'<html><head>'
			'<meta property="og:title" content="{title}"><meta property="twitter:title" content="{title}">'
			'<meta property="og:image" content="{image}"><meta property="twitter:image" content="{image}">'
			'<meta name="description" property="og:description" content="{description}"><meta property="twitter:description" content="{description}">'
			'<meta property="twitter:site" content="@kheinacom"><meta property="twitter:card" content="summary_large_image">'
			'<meta property="og:site_name" content="fxraffinity.net">'
			'</head></html>'
		).format(
			title=escape(str(data['title'])),
			image=escape(str(image)),
			description=escape(str(data['description'])),
		),
		status_code=200 if req.headers.get('user-agent') in generate_embed_user_agents else 302,
		headers={
			'location': f'https://www.furaffinity.net/view/{post_id}',
		},
	)


if __name__ == '__main__' :
	from uvicorn.main import run
	run(app, host='0.0.0.0', port=5000)
