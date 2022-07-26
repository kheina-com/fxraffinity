from kh_common.server import ServerApp
from kh_common.logging import getLogger
from kh_common.caching import ArgsCache
from fastapi.responses import HTMLResponse
from fa_crawler import FurAffinityCrawler
from html import escape

logger = getLogger()
app = ServerApp(auth=False)
crawler = FurAffinityCrawler()


@ArgsCache(TTL_days=1)
async def _fetch_fa_post(id: int) :
	return await crawler.crawl(id)


@app.get('/view/{post_id}')
@app.get('/full/{post_id}')
@app.get('/{post_id}')
async def v1Post(post_id: int) :
	data = await _fetch_fa_post(post_id)
	return HTMLResponse(
		(
			'<html><head>'
			'<meta property="og:title" content="{title}"><meta property="twitter:title" content="{title}">'
			'<meta property="og:image" content="{image}"><meta property="twitter:image" content="{image}">'
			'<meta name="description" property="og:description" content="{description}"><meta property="twitter:description" content="{description}">'
			'<meta property="twitter:site" content="@kheinacom"><meta property="twitter:card" content="summary_large_image">'
			'<meta property="twitter:site" content="@kheinacom"><meta property="twitter:card" content="summary">'
			'<meta property="og:site_name" content="fxraffinity.net">'
			'</head></html>'
		).format(
			**{ k: escape(str(v)) for k, v in data.items() },
		)
	)


if __name__ == '__main__' :
	from uvicorn.main import run
	run(app, host='127.0.0.1', port=8000)
