# -*- coding: utf-8 -*-
# default.py
import urllib,urllib2,re,xbmcplugin,xbmcgui,subprocess,sys,os,os.path,sys,xbmcaddon,xbmcvfs,random,hashlib,threading
import json,cookielib,gzip,time
import xbmc

from bt import TorrentFile
from xbmcswift2 import Plugin, CLI_MODE, xbmcaddon,ListItem
from StringIO import StringIO
from zhcnkbd import Keyboard

reload(sys)
sys.setdefaultencoding('utf-8')

__addonid__ = "plugin.video.115"
__addon__ = xbmcaddon.Addon(id=__addonid__)
__cwd__ = __addon__.getAddonInfo('path')
__resource__  = xbmc.translatePath( os.path.join( __cwd__, 'lib' ) )
__subpath__       = xbmc.translatePath( os.path.join( __cwd__, 'subtitles') ).decode("utf-8")
if not os.path.exists(__subpath__):
    os.makedirs(__subpath__)
sys.path.append (__resource__)
colors = {'back': '7FFF00','dir': '8B4513','video': 'FF0000','next': 'CCCCFF','bt': '660066', 'audio': '0000FF', 'subtitle':'505050', 'image': '00FFFF', '-1':'FF0000','0':'8B4513','1':'CCCCFF','2':'7FFF00', 'menu':'FFFF00'}

ALL_VIEW_CODES = {
    'list': {
        'skin.confluence': 50, # List
        'skin.aeon.nox': 50, # List
        'skin.droid': 50, # List
        'skin.quartz': 50, # List
        'skin.re-touched': 50, # List
    },
    'thumbnail': {
        'skin.confluence': 500, # Thumbnail
        'skin.aeon.nox': 500, # Wall
        'skin.droid': 51, # Big icons
        'skin.quartz': 51, # Big icons
        'skin.re-touched': 500, #Thumbnail
        'skin.confluence-vertical': 500,
        'skin.jx720': 52,
        'skin.pm3-hd': 53,
        'skin.rapier': 50,
        'skin.simplicity': 500,
        'skin.slik': 53,
        'skin.touched': 500,
        'skin.transparency': 53,
        'skin.xeebo': 55,
    },
}
		
plugin = Plugin()
ppath = plugin.addon.getAddonInfo('path')
videoexts=plugin.get_setting('videoext').lower().split(',')
musicexts=plugin.get_setting('musicext').lower().split(',')
cookiefile = os.path.join(ppath, 'cookie.dat')

subcache = plugin.get_storage('subcache')
filters = plugin.get_storage('ftcache', TTL=1440)
#urlcache = plugin.get_storage('urlcache', TTL=5)
setthumbnail=plugin.get_storage('setthumbnail')
setthumbnail['set']=False

class QRShower(xbmcgui.WindowDialog):
    def __init__(self):
        self.imgControl = xbmcgui.ControlImage((1280-250)/2, (720-250)/2,250, 250, filename = '')
        self.addControl(self.imgControl)
        self.labelControl = xbmcgui.ControlLabel((1280-300)/2, (720+250)/2 + 10, 300, 10, '请用115手机客户端扫描二维码', alignment = 0x00000002)
        self.addControl(self.labelControl)		

    def showQR(self, url):
        self.imgControl.setImage(url)
        self.doModal()
        #self.setFocus(self.imgControl)

    def changeLabel(self, label):
        self.labelControl.setLabel(label)
        
    def onAction(self,action):
        self.close()
	def onClick(self, controlId):
		self.close()
		
class api_115(object):
	
	bad_servers = ['fscdnuni-vip.115.com', 'fscdntel-vip.115.com']
	def __init__(self, cookiefile):
		
		servers = {'0':'vipcdntel.115.com', '1':'vipcdnuni.115.com', '2':'vipcdnctt.115.com', '3':'vipcdngwbn.115.com'}		
		self.prefer_server = servers.get(plugin.get_setting('prefer115server'))
		self.cookiejar = cookielib.LWPCookieJar()
		if os.path.exists(cookiefile):
			self.cookiejar.load(
				cookiefile, ignore_discard=True, ignore_expires=True)
		self.opener = urllib2.build_opener(
			urllib2.HTTPCookieProcessor(self.cookiejar))

		self.headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
			'Accept-encoding': 'gzip,deflate',
		}

	def login(self):		
		login_page = self.urlopen('http://passport.115.com/?ct=login&ac=qrcode_token&is_ssl=1')
		msgs=json.loads(self.fetch(login_page))
		uid,_t,sign=msgs['uid'],msgs['time'],msgs['sign']
		
		sessionid_page=self.urlopen('http://msg.115.com/proapi/anonymous.php?ac=signin&user_id='+str(uid)+'&sign='+str(sign)+'&time='+str(_t))
		sessionmsgs=json.loads(self.fetch(sessionid_page))
		sessionid=sessionmsgs['session_id']
		imserver = sessionmsgs['server']
		
		qrcode_url='http://www.115.com/scan/?ct=scan&ac=qrcode&uid='+str(uid)+'&_t='+str(time.time())
		
		qrShower = QRShower()
		#qrShower.showQR(qrcode_url)
		qthread = threading.Thread(target=qrShower.showQR, args=(qrcode_url,))
		qthread.start()
		
		for i in range(2):
			try:
				data = self.urlopen('http://'+imserver+'/chat/r?VER=2&c=b0&s='+str(sessionid)+'&_='+str(long(time.time())))
			except Exception, e:
				qrShower.close()
				qthread.join()
				return {'state':False, 'message':'Login Error'}
			ll = json.loads(self.fetch(data))
			#ll = eval(data)
			#ll = json.loads(data[data.index('[{'):])
			for l in ll:
				for p in l['p']:
					if p.has_key('key') == False:
						qrShower.changeLabel('请在手机客户端点击登录确认')
						continue
					key = p['key']
					v = p['v']
					break;
		if key is None:
			return {'state':False, 'message':'Login Error'}
		#data = self.urlopen('http://www.115.com/?ct=login&ac=qrcode&key=' + key + '&v=' + v + '&goto=https%3A%2F%2Fpassport.115.com%2F%3Fct%3Dlogin%26ac%3Dempty_page%26is_ssl%3D1')
		data = self.urlopen('http://www.115.com/?ct=login&ac=qrcode&key=' + key + '&v=' + v)
		data = self.fetch(data)

		data = self.urlopen('http://www.115.com/?ct=login&ac=is_login&_=' + str(time.time()))
		data = self.fetch(data)
		data = json.loads(data[data.index('{'):])
		qrShower.close()
		qthread.join()

		if data['state'] != True:
			return {'state':False, 'message':data['msg']}
		if data['data'].has_key('USER_NAME'):
			self.user_name = data['data']['USER_NAME']
		else:
			self.user_name = data['data']['USER_ID']
		self.is_vip='0'
		if data['data'].has_key('IS_VIP'):
			self.is_vip=data['data']['IS_VIP']
		self.cookiejar.save(cookiefile, ignore_discard=True)
		return {'state':True, 'user_name':self.user_name,'is_vip':self.is_vip}
			
	def urlopen(self, url, **args): 
		#plugin.log.error(url)
		if 'data' in args and type(args['data']) == dict:
			args['data'] = json.dumps(args['data'])
			self.headers['Content-Type'] = 'application/json'
		else:
			self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
		rs = self.opener.open(
			urllib2.Request(url, headers=self.headers, **args), timeout=60)
		#urlcache[url] = rs
		return rs		
		
	def fetch(self,wstream):
		if wstream.headers.get('content-encoding', '') == 'gzip':
			content = gzip.GzipFile(fileobj=StringIO(wstream.read())).read()
		else:
			content = wstream.read()
		return content

	def getcookieatt(self, domain, attr):
		if domain in self.cookiejar._cookies and attr in \
		   self.cookiejar._cookies[domain]['/']:
			return self.cookiejar._cookies[domain]['/'][attr].value
	def depass(self,ac,ps,co):
		eac=hashlib.sha1(ac).hexdigest()
		eps=hashlib.sha1(ps).hexdigest()
		return hashlib.sha1(hashlib.sha1(eps+eac).hexdigest()+co.upper()).hexdigest()
	def encodes(self):
		prefix = ""
		phpjs=int(random.random() * 0x75bcd15)
		retId = prefix
		retId += self.encodess(int(time.time()),8)
		retId += self.encodess(phpjs, 5)
		return retId
	def encodess(self,seed, reqWidth):
		seed = hex(int(seed))[2:]
		if (reqWidth < len(seed)):
			return seed[len(seed) - reqWidth:]
		if (reqWidth >  len(seed)):
			return (1 + (reqWidth - seed.length)).join('0') + seed
		return seed	
		
		
xl = api_115(cookiefile)

		
@plugin.route('/login')
def login():
	r=xl.login()
	if r['state']:
		plugin.notify(msg='登录成功')
	else:
		plugin.notify('登录失败：' + r['message'])
	return	

@plugin.route('/setting')
def setting():
	ret= plugin.open_settings()
	return


@plugin.route('/')
def index():
	data=xl.urlopen('http://web.api.115.com/files?aid=0&cid=0&o=user_ptime&asc=0&offset=0&show_dir=1&limit=115&code=&scid=&snap=0&natsort=1&source=&format=json')
	data= xl.fetch(data).replace('\n','').replace('\r','')
	data=json.loads(data[data.index('{'):])
	if not data['state']:
		login()
	item = [
		{'label': '网盘', 'path': plugin.url_for('getfile',cid='0',offset=0,star='0')},
		{'label': '星标列表', 'path': plugin.url_for('getfile',cid='0',offset=0,star='1')},
		#{'label': '记事本', 'path': plugin.url_for('note',cid='0',offset=0)},
		{'label': '离线任务列表', 'path': plugin.url_for('offline_list')},
		{'label': '搜索', 'path': plugin.url_for('search',mstr='0',offset=0)},
		{'label': '磁力搜索', 'path': plugin.url_for('btsearch',website='0',sstr='0',sorttype='-1',page='1')},
		{'label': '豆瓣电影', 'path': plugin.url_for('dbmovie')},
        {'label': '豆瓣影人搜索', 'path': plugin.url_for('dbactor', sstr='none', page=0)},
        {'label': '豆瓣电影新片榜TOP10', 'path': plugin.url_for('dbntop')},
        {'label': '豆瓣电影TOP250', 'path': plugin.url_for('dbtop', page=0)},
		{'label': '扫码登入', 'path': plugin.url_for('login')},
		{'label': '设置', 'path': plugin.url_for('setting')},
		#{'label': '清空缓存','path': plugin.url_for('clear_cache'),'is_playable': True,'properties': {'isPlayable': ''}}
	]
	return item
	
@plugin.route('/search/<mstr>/<offset>')
def search(mstr,offset):
	if not mstr or mstr=='0':
		kb = Keyboard('',u'请输入搜索关键字')
		kb.doModal()
		if not kb.isConfirmed():
			return
		mstr = kb.getText()
		if not mstr:
			return
	sorttypes = {'0': 'user_ptime','1': 'file_size','2': 'file_name'}
	sorttype=sorttypes[plugin.get_setting('sorttype')]	
	sortasc=str(plugin.get_setting('sortasc'))
	pageitems = {'0': '25','1': '50','2': '100'}
	pageitem=pageitems[plugin.get_setting('pageitem')]	
	url='http://web.api.115.com/files/search?search_value=' + urllib.quote_plus(mstr) + '&type=&star=0&o='+sorttype+'&asc='+sortasc+'&offset='+str(offset)+'&show_dir=1&natsort=1&limit='+str(pageitem)+'&format=json'
	
	data=xl.urlopen(url)
	data= xl.fetch(data).replace('\n','').replace('\r','')
	data=json.loads(data[data.index('{'):])
	
	videoexts=plugin.get_setting('videoext').lower().split(',')
	musicexts=plugin.get_setting('musicext').lower().split(',')
	
	if data['state']:
		imagecount=0
		items=[]
		for item in data['data']:			
			listitem=getListItem(item)
			if listitem!=None:
				items.append(listitem)
				if item.has_key('ms'):
					imagecount+=1
		if data['count']>int(offset)+int(pageitem):
			items.append({'label': colorize_label('下一页', 'next'), 'path': plugin.url_for('search',mstr=mstr,offset=str(int(offset)+int(pageitem)))})
		#skindir=xbmc.getSkinDir()
		if imagecount >= 10 and imagecount * 2 > len(items):       
			setthumbnail['set']=True
			#if ALL_VIEW_CODES['thumbnail'].has_key(skindir):
			#	plugin.set_view_mode(ALL_VIEW_CODES['thumbnail'][skindir])
		return items
	else:
		plugin.notify(msg='数据获取失败,错误信息:'+str(data['error']))
		return
		
@plugin.route('/btsearch/<website>/<sstr>/<sorttype>/<page>')
def btsearch(website,sstr,sorttype,page):	
	if not sstr or sstr=='0':
		kb = Keyboard('',u'请输入搜索关键字')
		kb.doModal()
		if not kb.isConfirmed():
			return
		sstr = kb.getText()
		if not sstr:
			return
	if website=='0':
		website=plugin.get_setting('magnetsearch')	
		
	if website=='0':
		dialog = xbmcgui.Dialog()
		websites = ['icili主站','icili2备站','btbook','bt2mag']
		website = dialog.select('磁力网站', websites)
		if website is -1: return
		website=str(website+1)


	sorttype=int(sorttype)		
	items=[]
	
	if website=='1':
		searchbase='http://icili.net'
		searchurl=searchbase+'/list/'+urllib.quote(sstr)+'/'+str(page)
		rmain=r'"title" href="(?P<href>.*?)">(?P<title>.*?)</a>.*?收录时间.*?>(?P<createtime>.*?)<.*?活跃热度.*?>(?P<heatlevel>.*?)<.*?最后活跃.*?>(?P<lastdown>.*?)<.*?文件大小.*?>(?P<filesize>.*?)<'
	if website=='2':
		searchbase='http://icili.net'
		searchurl=searchbase+'/a/list/'+urllib.quote(sstr)+'/'+str(page)
		rmain=r'"title" href="(?P<href>.*?)">.*?"item-list">(?P<title>.*?)</div>.*?大小:<span>(?P<filesize>.*?)</span>.*?文件数:<span>(?P<filecount>.*?)</span>.*?创建日期:<span>(?P<createtime>.*?)</span>.*?热度:<span>(?P<heatlevel>.*?)</span>'
	elif website=='3':
		searchbase='http://www.btbook.net/search/'		
		rmain=r'target="_blank">(?P<title>.*?)</a>.*?<ul>(?P<filelist>.*?)</ul>.*?fileType[0-9]*?">(?P<filetype>.*?)</span>.*?创建时间.*?<b.*?>(?P<createtime>.*?)</b>.*?文件大小.*?<b.*?>(?P<filesize>.*?)</b>.*?下载热度.*?<b.*?>(?P<heatlevel>.*?)</b>.*?最近下载.*?<b.*?>(?P<lastdown>.*?)</b>.*?href="(?P<magnet>.*?)"'
		if sorttype<0:
			dialog = xbmcgui.Dialog()
			sorttype=dialog.select('btbook搜索-选择排序类型',['创建时间','文件大小','下载热度','相关度'])
			if sorttype==-1:
				return
		searchurl=searchbase+urllib.quote(sstr)+'/'+str(page)+'-'+str(sorttype+1)+'.html'
	elif website=='4':
		searchbase='http://www.bt2mag.com/search/'
		searchurl=searchbase+urllib.quote(sstr)+'/currentPage/'+str(page)
		rmain=r'<div\x20class="row">.*?<a\x20href="(?P<href>.*?)"\x20title="(?P<title>.*?)">.*?Size:(?P<filesize>.*?)\x20/\x20Convert\x20Date:(?P<createtime>.*?)</div>'
	#data=xl.urlopen(searchurl)
	#data=xl.fetch(data)
	data=_http(searchurl)	
	reobj = re.compile(rmain, re.DOTALL)
	
	for match in reobj.finditer(data):
		title=match.group('title')
		filesize=match.group('filesize')
		createtime=match.group('createtime')
		
		if website=='1':
			title=title.replace('<span class="highlight">','').replace('</span>','')
			filemsg='大小：'+filesize+'  创建时间：'+createtime		
			detialdata=_http(searchbase+match.group('href'))		
			detailreobj = re.compile(r'磁力链接：.*?href="(?P<magnet>.*?)">', re.DOTALL)		
			detailmatch = detailreobj.search(detialdata)
			if detailmatch:
				magnet = detailmatch.group('magnet')			
			else:
				magnet = ''	
		if website=='2':			
			filemsg='大小：'+filesize+'  创建时间：'+createtime		
			magnet=match.group('href')[match.group('href').rfind('/')+1:]			
			magnet='magnet:?xt=urn:btih:'+magnet
		elif website=='3':
			title=title.replace('<b>','').replace('</b>','')
			lireobj=re.compile(r'<li>(?P<filename>.*?)<span', re.DOTALL)
			filelist=lireobj.finditer(match.group('filelist'))			
			filemsg='大小：'+filesize+'  创建时间：'+createtime+'\r\n文件列表：'
			for f in filelist:
				filemsg=filemsg+'\r\n'+f.group('filename')
			magnet=match.group('magnet')
		
		elif website=='4':
			filemsg='大小：'+filesize+'  创建时间：'+createtime
			magnet=match.group('href')[match.group('href').rfind('/')+1:]			
			magnet='magnet:?xt=urn:btih:'+magnet
			
		if magnet:
			listitem=ListItem(label=colorize_label(title, 'bt'), label2=filesize, icon=None, thumbnail=None, path=plugin.url_for('offlinedown',url=magnet.encode('UTF-8'),title=title,msg=filemsg))
			items.append(listitem)
	
	if website=='1':		
		nextpage=str(int(page)+1)
		if data.find('/'+nextpage+'">'+nextpage+'</a></li>')>=0:		
			items.append({'label': colorize_label('下一页', 'next'), 'path': plugin.url_for('btsearch',website=website,sstr=sstr,sorttype=str(sorttype),page=str(int(page)+1))})
	elif website=='3':
		if data.find('html"> &gt; </a>')>=0:		
			items.append({'label': colorize_label('下一页', 'next'), 'path': plugin.url_for('btsearch',website=website,sstr=sstr,sorttype=str(sorttype),page=str(int(page)+1))})
	elif website=='4':
		if data.find('>Next\x20<span')>=0:
			items.append({'label': colorize_label('下一页', 'next'), 'path': plugin.url_for('btsearch',website=website,sstr=sstr,sorttype=str(sorttype),page=str(int(page)+1))})
	return items

def getListItem(item):
	if item.has_key('sha'):
		if item.has_key('iv'):			
			listitem=ListItem(label=colorize_label(item['n'], 'video'), label2=None, icon=None, thumbnail=None, path=plugin.url_for('play',pc=item['pc'],name=item['n'].encode('UTF-8'),iso='0'))
			listitem.set_info('video', {'size': item['s']})
			listitem.set_is_playable('true')
			listitem.set_property('PlayableInList', 'true')	
		elif item.has_key('ms'):			
			listitem=ListItem(label=colorize_label(item['n'], 'image'), label2=None, icon=None, thumbnail=None, path=plugin.url_for('playimg',pc=item['pc'],name=item['n'].encode('UTF-8')))
			listitem.set_info('image', {'size': item['s']})
			listitem.set_is_playable('true')
			listitem.set_property('PlayableInList', 'true')	
		elif item['ico'] in videoexts:
			listitem=ListItem(label=colorize_label(item['n'], 'video'), label2=None, icon=None, thumbnail=None, path=plugin.url_for('play',pc=item['pc'],name=item['n'].encode('UTF-8'),iso='1'))
			listitem.set_info('video', {'size': item['s']})
			listitem.set_is_playable('true')
			listitem.set_property('PlayableInList', 'true')
		elif  item['ico'] in musicexts:
			listitem=ListItem(label=colorize_label(item['n'], 'audio'), label2=None, icon=None, thumbnail=None, path=plugin.url_for('play',pc=item['pc'],name=item['n'].encode('UTF-8'),iso='1'))
			listitem.set_info('audio', {'size': item['s']})
			listitem.set_is_playable('true')
			listitem.set_property('PlayableInList', 'true')	
		elif item['ico']=='torrent':
			listitem=ListItem(label=colorize_label(item['n'], 'bt'), label2=None, icon=None, thumbnail=None, path=plugin.url_for('offline_bt',sha1=item['sha']))
			listitem.set_is_playable('true')
		else:
			listitem=None
			
		if is_subtitle(item['ico']):
			subcache[item['n'].encode('UTF-8')]=item['pc']
		
		if item.has_key('u') and  listitem!=None:
			listitem.set_thumbnail(item['u'])
	else:
		listitem=ListItem(label=colorize_label(item['n'], 'dir'), label2=None, icon=None, thumbnail=None, path=plugin.url_for('getfile',cid=item['cid'],offset=0,star='0'))
	return listitem
	
@plugin.route('/getfile/<cid>/<offset>/<star>')
def getfile(cid,offset,star):	
	subcache.clear()	
	
	sorttypes = {'0': 'user_ptime','1': 'file_size','2': 'file_name'}
	sorttype=sorttypes[plugin.get_setting('sorttype')]	
	sortasc=str(plugin.get_setting('sortasc'))
	pageitems = {'0': '25','1': '50','2': '100'}
	pageitem=pageitems[plugin.get_setting('pageitem')]	
	#if cid+"/"+offset+"/"+str(star) in urlcache:
		#plugin.log.error("缓存输出:"+cid+"/"+offset)
		#return urlcache[cid+"/"+offset+"/"+str(star)]
	#else:
		#plugin.log.error("数据更新:"+cid+"/"+offset)
	
	if sorttype=='file_name':
		data=xl.urlopen('http://aps.115.com/natsort/files.php?aid=1&cid='+str(cid)+'&type=&star='+star+'&o='+sorttype+'&asc='+sortasc+'&offset='+str(offset)+'&show_dir=1&limit='+pageitem+'&format=json')
	else:
		data=xl.urlopen('http://web.api.115.com/files?aid=1&cid='+str(cid)+'&type=&star='+star+'&o='+sorttype+'&asc='+sortasc+'&offset='+str(offset)+'&show_dir=1&limit='+pageitem+'&format=json')
	data= xl.fetch(data).replace('\n','').replace('\r','')
	data=json.loads(data[data.index('{'):])
	if data['state']:
		imagecount=0
		items=[]
		for item in data['path']:
			if item['cid']!=0 and item['cid']!=cid:
				items.append({'label': colorize_label('返回到【'+item['name']+"】", 'back'), 'path': plugin.url_for('getfile',cid=item['cid'],offset=0,star='0')})		
		for item in data['data']:			
			listitem=getListItem(item)
			if listitem!=None:
				items.append(listitem)					
				if item.has_key('ms'):
					imagecount+=1
		if data['count']>int(offset)+int(pageitem):
			items.append({'label': colorize_label('下一页', 'next'), 'path': plugin.url_for('getfile',cid=cid,offset=str(int(offset)+int(pageitem)),star=star)})
			#urlcache[cid+"/"+offset+"/"+str(star)] = items
		#xbmc.executebuiltin('Container.SetViewMode(8)')
		#skindir=xbmc.getSkinDir()
		if imagecount >= 10 and imagecount * 2 > len(items):
			setthumbnail['set']=True
			#plugin.notify('setthumbnail')
			#if ALL_VIEW_CODES['thumbnail'].has_key(skindir):
			#	plugin.set_view_mode(ALL_VIEW_CODES['thumbnail'][skindir])
		return items
	else:
		plugin.notify(msg='数据获取失败,错误信息:'+str(data['error']))
		return

	
@plugin.route('/playiso/<pc>/<name>')
def playiso(pc,name):
	videourl=get_file_download_url(pc)
	xbmc.executebuiltin("PlayMedia(%s)" % (videourl))
	return
	
@plugin.route('/playimg/<pc>/<name>')
def playimg(pc,name):
	data=xl.urlopen('http://web.api.115.com/files/image?pickcode='+pc+'&_='+str(long(time.time())))		
	data=json.loads(xl.fetch(data))
	imageurl=''
	if data['state']:
		imageurl=data['data']['source_url']
	xbmc.executebuiltin("ShowPicture(%s)" % (imageurl))
	return
	
def rmtree(path):
    if isinstance(path, unicode):
        path = path.encode('utf-8')
    dirs, files = xbmcvfs.listdir(path)
    for dir in dirs:
        rmtree(os.path.join(path, dir))
    for file in files:
        xbmcvfs.delete(os.path.join(path, file))
    xbmcvfs.rmdir(path)
	
@plugin.route('/play/<pc>/<name>/<iso>')
def play(pc,name,iso):	
	stm=str(plugin.get_setting('select'))
	if iso=='1':
		stm='5'	
	if stm=='0':
		dialog = xbmcgui.Dialog()
		qtyps = [('标清', '1'),('高清', '2'), ('蓝光', '3'),('1080p', '4'),('原码', '5')]
		sel = dialog.select('清晰度', [q[0] for q in qtyps])
		if sel is -1: return 'cancel'
		stm=str(sel+1)		
	
	if stm=='5':
		videourl=get_file_download_url(pc)
		if videourl=='':
			plugin.notify(msg='无视频文件.')
			return
	else:
		data=xl.urlopen('http://115.com/api/video/m3u8/'+pc+'.m3u8')
		data=xl.fetch(data)
		url= re.compile(r'http:(.*?)\r', re.DOTALL).findall(data)
		if len(url)<1:
			plugin.notify(msg='无视频文件.')
			return
		if len(url)<int(stm):
			stm=str(len(url))
		videourl='http:'+url[int(stm)-1]
	
	subpath=''
	if iso=='0':
		name=name[:name.rfind('.')]		
		sub_pcs={}
		for k,v in subcache.items():
			if k.find(name)!= -1:
				sub_pcs['_同目录_'+k]=get_file_download_url(v)
				
		if plugin.get_setting('subtitle')=='true':
			data=xl.urlopen('http://web.api.115.com/movies/subtitle?pickcode='+pc)
			data=json.loads(xl.fetch(data))		
			if data['state']:
				for s in data['data']:
					sub_pcs[(s['language']+'_'+s['filename']).decode('utf-8')]=s['url']
				
		if len(sub_pcs)==1:
			subpath = os.path.join( __subpath__,sub_pcs.keys()[0].decode('utf-8'))
			suburl=sub_pcs[sub_pcs.keys()[0]]
			plugin.notify('加载了1个字幕')
			
		elif len(sub_pcs)>1:
			dialog = xbmcgui.Dialog()
			sel = dialog.select('字幕选择', [subname for subname in sub_pcs.keys()])
			if sel>-1: 
				subpath = os.path.join( __subpath__,sub_pcs.keys()[sel])
				suburl = sub_pcs[sub_pcs.keys()[sel]]
				
		if subpath!='':
			if suburl!='':				
				socket = urllib.urlopen( suburl )
				subdata = socket.read()
				with open(subpath, "wb") as subFile:
					subFile.write(subdata)
				subFile.close()
	plugin.set_resolved_url(videourl,subpath)
	return
	
@plugin.route('/offline_bt/<sha1>')
def offline_bt(sha1):
	dialog = xbmcgui.Dialog()
	ret = dialog.yesno('115网盘提示', '是否离线文件?')
	if ret:
		uid = xl.getcookieatt('.115.com', 'UID')
		uid = uid[:uid.index('_')]
		data=xl.urlopen('http://115.com/?ct=offline&ac=space&_='+str(long(time.time())))
		data=json.loads(xl.fetch(data))
		sign=data['sign']
		_time=data['time']
		data = urllib.urlencode({'sha1': sha1,'uid':uid,'sign':sign,'time':_time})
		data=xl.urlopen('http://115.com/lixian/?ct=lixian&ac=torrent',data=data)		
		data=json.loads(xl.fetch(data))
		if data['state']:			
			wanted='0'
			for i in range(1,len(data['torrent_filelist_web'])):
				wanted+='%02C'
				wanted+=str(i)			
			torrent_name=data['torrent_name']			
			info_hash=data['info_hash']			
			data = urllib.urlencode({'info_hash': info_hash,'wanted': wanted,'savepath': torrent_name,'uid':uid,'sign':sign,'time':_time})
			
			data=xl.urlopen('http://115.com/lixian/?ct=lixian&ac=add_task_bt',data=data)
			data=json.loads(xl.fetch(data))
			if data['state']:
				plugin.notify('离线任务添加成功！', delay=2000)
			else:
				plugin.notify(data['error_msg'], delay=2000)
				return
		else:
			plugin.notify(data['error_msg'], delay=2000)
			return			
	else:
		return
def get_file_download_url(pc):
	bad_server = ''
	result = ''
	data=xl.urlopen("http://web.api.115.com/files/download?pickcode="+pc+"&_="+str(long(time.time())))		
	data=json.loads(xl.fetch(data))
	if data['state']:
		result=data['file_url']
	else:
		data=xl.urlopen("http://proapi.115.com/app/chrome/down?method=get_file_url&pickcode="+pc)
		data=json.loads(xl.fetch(data))
		if data['state']:			
			for value in data['data'].values():				
				if value.has_key('url'):
					result = value['url']['url']
					break
		else:
			return ''      
			
	for bs in xl.bad_servers:
		if result.find(bs) != -1:
			bad_server = bs
			break
	if bad_server != '':
		result = result.replace(bad_server, xl.prefer_server)
	return result

@plugin.route('/offline_list')
def offline_list():
	msg_st={'-1': '任务失败','0': '任务停止','1': '下载中','2': '下载完成'}
	data=xl.urlopen("http://115.com/?ct=offline&ac=space&_="+str(time.time()))
	data=xl.fetch(data)
	data=json.loads(data[data.index('{'):])
	sign=data['sign']
	time1=data['time']
	uid = xl.getcookieatt('.115.com', 'UID')
	uid = uid[:uid.index('_')]
	page=1
	task=[]
	items=[]
	while True:
		data = urllib.urlencode({'page': str(page),'uid':uid,'sign':sign,'time':time1})
		data=xl.urlopen("http://115.com/lixian/?ct=lixian&ac=task_lists",data=data)
		data=xl.fetch(data)
		data=json.loads(data[data.index('{'):])
		if data['state']:
			for item in data['tasks']:
				task.append(item)
			if data['page_count']>page:
				page=page+1
			else:
				break
		else:
			break
	for item in task:
		items.append({'label': item['name']+colorize_label("["+msg_st[str(item['status'])]+"]", str(item['status'])), 
					'path': plugin.url_for('getfile',cid=item['file_id'],offset='0',star='0')})
	return items
	
@plugin.route('/lxlist/<cid>/<name>')
def lxlist(cid,name):
	dialog = xbmcgui.Dialog()
	ret = dialog.yesno('115网盘提示', '是否包含子文件夹?')
	lists=getlxlist(cid,ret)
	x=0
	#plugin.log.error(lists)
	if len(lists)>0:
		strs=name+'\n'
		for item in lists:
			strs += item['n']+"|115:"+item['pc']+"|"+item['u']+'\n'
			if len(strs)>40000:
				data = urllib.urlencode({'nid': '', 'content': strs, 'cid': '0'})		
				data=xl.urlopen("http://115.com/note/?ct=note&ac=save",data=data)
				x=x+1
				strs=name+"-"+str(x)+'\n'
		data = urllib.urlencode({'nid': '', 'content': strs, 'cid': '0'})		
		data=xl.urlopen("http://115.com/note/?ct=note&ac=save",data=data)
		data= xl.fetch(data).replace('\n','').replace('\r','')
		data=json.loads(data[data.index('{'):])
		#plugin.log.error(data)
		if data['state']:
			plugin.notify(msg='制作成功！')
		else:
			plugin.notify(msg='制作失败！'+str(data['msg']))

def getlxlist(cid,alls):
	sorttypes = {'0': 'user_ptime','1': 'file_size','2': 'file_name'}
	sorttype=sorttypes[plugin.get_setting('sorttype')]	
	sortasc=str(plugin.get_setting('sortasc'))
	lists=[]
	offsets=0
	if alls:
		while True:
			data=xl.urlopen("http://web.api.115.com/files?aid=1&cid="+cid+"&type=4&star=0&o="+sorttype+"&asc="+sortasc+"&offset="+str(offsets)+"&show_dir=1&limit=80&format=json")
			data= xl.fetch(data).replace('\n','').replace('\r','')
			data=json.loads(data[data.index('{'):])
			if data['state']:
				for item in data['data']:
					if item.has_key('sha'):
						if item.has_key('iv'):
							lists.append({'n':item['n'],'pc':item['pc'],'u':item['u']})
				if data['count']>data['offset']+80:
					offsets=data['offset']+80
				else:
					break;
			else:
				break;
		return lists
	else:
		while True:
			data=xl.urlopen("http://web.api.115.com/files?aid=1&cid="+cid+"&type=&star=0&o="+sorttype+"&asc="+sortasc+"&offset="+str(offsets)+"&show_dir=1&limit=80&format=json")
			data= xl.fetch(data).replace('\n','').replace('\r','')
			data=json.loads(data[data.index('{'):])
			if data['state']:
				for item in data['data']:
					if item.has_key('sha'):
						if item.has_key('iv'):
							lists.append({'n':item['n'],'pc':item['pc'],'u':item['u']})
				if data['count']>data['offset']+80:
					offsets=data['offset']+80
				else:
					break;
			else:
				break;
		return lists

@plugin.route('/note/<cid>/<offset>')
def note(cid,offset):
	# if cid+"/note/"+offset in urlcache:
		# #plugin.log.error("缓存输出:"+cid+"/note/"+offset)
		# return urlcache[cid+"/note/"+offset]
	# else:
		#plugin.log.error("数据更新:"+cid+"/note/"+offset)
	data=xl.urlopen('http://115.com/note/?ct=note&page_size=9999&cid='+str(cid)+'&start='+str(offset))
	data= xl.fetch(data).replace('\n','').replace('\r','')
	data=json.loads(data[data.index('{'):])
	if data['state']:
		items=[]
		for item in data['data']:
			items.append({'label': colorize_label(item['title'], 'dir'),'path': plugin.url_for('getnote',nid=item['nid'])})
		#urlcache[cid+"/note/"+offset] = items
		return items
	else:
		plugin.notify(msg='数据获取失败,错误信息:'+str(data['error']))
		return
@plugin.route('/getnote/<nid>')
def getnote(nid):
	# if nid+"/note" in urlcache:
		# #plugin.log.error("缓存输出:"+nid+"/note")
		# return urlcache[nid+"/note"]
	# else:
		#plugin.log.error("数据更新:"+nid+"/note")
	data=xl.urlopen('http://115.com/note/?ct=note&ac=detail&nid='+nid)
	data= xl.fetch(data).replace('\n','').replace('\r','')
	data=json.loads(data[data.index('{'):])
	if data['state']:
		items=[]
		content=data['data']['content'].split('\n')
		for item in content:
			if item != data['data']['title']:
				temp=item.split('|')
				if len(temp)==2:
					items.append({'label': colorize_label(temp[0], 'video'),'path': plugin.url_for('playnote',url=temp[1].encode('UTF-8'))})
				elif len(temp)==3:
					items.append({'label': colorize_label(temp[0], 'video'),'thumbnail':temp[2],'path': plugin.url_for('playnote',url=temp[1].encode('UTF-8'))})
				else:
					items.append({'label': colorize_label(item, 'video'),'path': plugin.url_for('playnote',url=item.encode('UTF-8'))})

		#plugin.log.error(content)
		#urlcache[nid+"/note"] = items
		return items
	else:
		plugin.notify(msg='数据获取失败,错误信息:'+str(data['error']))


@plugin.route('/offline/<url>')
def offline(url):
	xbmc.executebuiltin( "ActivateWindow(busydialog)" )
	xbmc.sleep(1000)
	data=xl.urlopen("http://115.com/?ct=offline&ac=space&_="+str(time.time()))
	data=xl.fetch(data)
	data=json.loads(data[data.index('{'):])
	sign=data['sign']
	#plugin.notify(sign)
	time1=data['time']
	uid = xl.getcookieatt('.115.com', 'UID')
	uid = uid[:uid.index('_')]
	data = urllib.urlencode({'url': url,'uid':uid,'sign':sign,'time':time1})
	data=xl.urlopen("http://115.com/lixian/?ct=lixian&ac=add_task_url",data=data)
	data=xl.fetch(data)
	#plugin.log.error(data)
	data=json.loads(data[data.index('{'):])
	if data['state']:
		plugin.notify(u' 添加离线成功'.encode('utf-8'),delay=1000)
	else:
		plugin.notify(u' 添加离线失败,错误代码:'.encode('utf-8')+data['error_msg'],delay=1000)
	xbmc.executebuiltin( "Dialog.Close(busydialog)" )
	if data['state']:
		return data['info_hash']
	else:
		return ''
	
	
@plugin.route('/offlinedown/<url>/<title>/<msg>')
def offlinedown(url,title='',msg=''):	
	dialog = xbmcgui.Dialog()
	ret = dialog.yesno('是否离线 '+title+'?', msg)
	if ret:
		info_hash=offline(url)
		if  info_hash:
			data=xl.urlopen("http://115.com/?ct=offline&ac=space&_="+str(time.time()))
			data=xl.fetch(data)
			data=json.loads(data[data.index('{'):])
			sign=data['sign']
			time1=data['time']
			uid = xl.getcookieatt('.115.com', 'UID')
			uid = uid[:uid.index('_')]
			page=1			
			file_id=''
			for i in range(0,10):
				time.sleep(1)
				data = urllib.urlencode({'page': str(page),'uid':uid,'sign':sign,'time':time1})
				data=xl.urlopen("http://115.com/lixian/?ct=lixian&ac=task_lists",data=data)
				data=xl.fetch(data)
				data=json.loads(data[data.index('{'):])
				if data['state']:
					curitem=None
					for item in data['tasks']:
						if item['info_hash']==info_hash:
							curitem=item
							break
					if curitem:
						if curitem['status']==2 and curitem['move']==1:
							if curitem.has_key('file_id'):
								file_id	=curitem['file_id']
					if file_id:
						break;
			if file_id:	
				return getfile(cid=file_id,offset=0,star='0')
			else:
				plugin.notify('离线任务未完成,请稍候从离线列表进入查看任务状态')


def _http(url, data=None):
    """
    open url
    """
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) {0}{1}'.
                   format('AppleWebKit/537.36 (KHTML, like Gecko) ',
                          'Chrome/28.0.1500.71 Safari/537.36'))
    req.add_header('Accept-encoding', 'gzip,deflate')
    if data:
        rsp = urllib2.urlopen(req, data=data, timeout=30)
    else:
        rsp = urllib2.urlopen(req, timeout=30)
    if rsp.info().get('Content-Encoding') == 'gzip':
        buf = StringIO(rsp.read())
        f = gzip.GzipFile(fileobj=buf)
        data = f.read()
    else:
        data = rsp.read()
    rsp.close()
    return data
	
@plugin.route('/dbmovie')
def dbmovie():
	
	if '类型' not in filters:
		rsp = _http('http://movie.douban.com/category/')
		fts = re.findall(
			r'class="label">([^>]+?)</h4>\s+<ul>(.*?)</ul>', rsp, re.S)
		typpatt = re.compile(r'<a href="#">([^>]+?)</a>')
		for ft in fts:
			typs = typpatt.findall(ft[1])
			if '类型' not in ft[0]:
				typs.insert(0, '不限')
			filters[ft[0]] =  tuple(typs)
	typs = filters['类型']
	menus = [{'label': t,
			  'path': plugin.url_for(
				  'dbcate', typ=str({'types[]':t,}), page=1),
			  } for t in typs]
	return menus

@plugin.route('/dbcate/<typ>/<page>')
def dbcate(typ, page):	
	params  = {'district': '', 'era': '', 'category': 'all',
			   'unwatched': 'false', 'available': 'false', 'sortBy': 'score',
			   'page': page, 'ck': 'null', 'types[]': ''}
	typ = eval(typ)	
	dialog = xbmcgui.Dialog()
	if 'district' in typ and not typ['district']:
		#plugin.notify(filters['地区'])
		sel = dialog.select('地区', filters['地区'])
		if sel is -1: return
		typ['district'] = filters['地区'][sel]
	if 'era' in typ and not typ['era']:
		sel = dialog.select('年代', filters['年代'])
		if sel is -1: return
		typ['era'] = filters['年代'][sel]
	params.update(typ)	
	data = urllib.urlencode(params)		
	rsp = _http('http://movie.douban.com/category/q',data.replace(urllib2.quote('不限'), ''))
	
	minfo = json.loads(rsp)
	menus = [{'label': '[%s].%s[%s][%s]' % (m['release_year'], m['title'],
										   m['rate'], m['abstract']),
			  'path': plugin.url_for('btsearch', website='0',sstr=m['title'].split(' ')[0].encode('utf-8'),sorttype='-1',page='1' ),
			  'thumbnail': m['poster'].replace('ipst','spst').replace('img3.douban.com','img4.douban.com'),
			  } for m in minfo['subjects']]	
	
	if not menus: return
	# if int(page) > 1:
		# menus.append({'label': '上一页', 'path': plugin.url_for(
			# 'dbcate', typ=str(typ), page=int(page)-1)})
	menus.append({'label': '下一页', 'path': plugin.url_for(
		'dbcate', typ=str(typ), page=int(page)+1)})
		
	ntyp = typ.copy()
	ntyp.update({'district': '', 'era': ''})
	menus.insert(0, {'label': '【按照条件过滤】【地区】【年代】选择',
		'path': plugin.url_for('dbcate',typ=str(ntyp), page=1)})
	setthumbnail['set']=True
	#skindir=xbmc.getSkinDir()
	#if ALL_VIEW_CODES['thumbnail'].has_key(skindir):		
		#plugin.set_view_mode(ALL_VIEW_CODES['thumbnail'][skindir])
	return menus

@plugin.route('/dbactor/<sstr>/<page>')
def dbactor(sstr, page):
	urlpre = 'http://movie.douban.com/subject_search'
	if 'none' in sstr:
		kb = Keyboard('',u'请输入搜索关键字')
		kb.doModal()
		if not kb.isConfirmed(): return
		sstr = kb.getText()
	url = '%s/?search_text=%s&start=%s' % (urlpre ,sstr, str(int(page)*15))
	rsp = _http(url)
	rtxt = r'%s%s' % ('tr class="item".*?nbg".*?src="(.*?)" alt="(.*?)"',
					  '.*?class="pl">(.*?)</p>.*?rating_nums">(.*?)<')
	patt = re.compile(rtxt, re.S)
	mitems = patt.findall(rsp)
	if not mitems: return
	menus = [{'label': '{0}. {1}[{2}][{3}]'.format(s, i[1], i[3], i[2]),
			 'path': plugin.url_for('btsearch',  website='0',sstr=i[1],sorttype='-1',page='1' ),
			 'thumbnail': i[0].replace('ipst','spst').replace('img3.douban.com','img4.douban.com'),
		 } for s, i in enumerate(mitems)]

	count = re.findall(r'class="count">.*?(\d+).*?</span>', rsp)
	count = int(count[0])
	page = int(page)
	if page>0:
		menus.append({
			'label': '上一页',
			'path': plugin.url_for('dbactor', sstr=sstr, page=page-1)})
	if (page+1)*15 < count:
		menus.append({
			'label': '下一页',
			'path': plugin.url_for('dbactor', sstr=sstr, page=page+1)})

	menus.insert(0, {
		'label': '【当前页%s/总共页%s】【放回上级菜单】' % (page+1, (count+14)//15),
		'path': plugin.url_for('index')})
	setthumbnail['set']=True
	#skindir=xbmc.getSkinDir()
	#if ALL_VIEW_CODES['thumbnail'].has_key(skindir):		
		#plugin.set_view_mode(ALL_VIEW_CODES['thumbnail'][skindir])
	return menus

@plugin.route('/dbntop')
def dbntop():
	'''
	img, title, info, rate
	'''
	rsp = _http('http://movie.douban.com/chart')
	mstr = r'%s%s' % ('nbg".*?src="(.*?)" alt="(.*?)"',
					  '.*?class="pl">(.*?)</p>.*?rating_nums">(.*?)<')
	mpatt = re.compile(mstr, re.S)
	mitems = mpatt.findall(rsp)
	menus = [{'label': '{0}. {1}[{2}][{3}]'.format(s, i[1], i[3], i[2]),
			 'path': plugin.url_for('btsearch', website='0', sstr=i[1],sorttype='-1',page='1' ),
			 'thumbnail': i[0].replace('ipst','spst').replace('img3.douban.com','img4.douban.com'),
		 } for s, i in enumerate(mitems)]
	setthumbnail['set']=True
	#skindir=xbmc.getSkinDir()
	#if ALL_VIEW_CODES['thumbnail'].has_key(skindir):		
		#plugin.set_view_mode(ALL_VIEW_CODES['thumbnail'][skindir])
	return menus

@plugin.route('/dbtop/<page>')
def dbtop(page):
	'''
	title, img, info
	'''
	page = int(page)
	pc = page * 25
	rsp = _http('http://movie.douban.com/top250?start={0}'.format(pc))
	mstr = r'class="item".*?alt="(.*?)" src="(.*?)".*?<p class="">\s+(.*?)</p>'
	mpatt = re.compile(mstr, re.S)
	mitems = mpatt.findall(rsp)
	menus = [{'label': '{0}. {1}[{2}]'.format(s+pc+1, i[0], ''.join(
		i[2].replace('&nbsp;', ' ').replace('<br>', ' ').replace(
			'\n', ' ').split(' '))),
			  'path': plugin.url_for('btsearch',  website='0', sstr=i[0],sorttype='-1',page='1' ),
			  'thumbnail': i[1].replace('ipst','spst').replace('img3.douban.com','img4.douban.com'),
		 } for s, i in enumerate(mitems)]
	# if  page != 0:
		# menus.append({'label': '上一页',
					  # 'path': plugin.url_for('dbtop', page=page-1)})
	if page <9 :
		menus.append({'label': '下一页',
					  'path': plugin.url_for('dbtop', page=page+1)})
	setthumbnail['set']=True
	#skindir=xbmc.getSkinDir()
	#if ALL_VIEW_CODES['thumbnail'].has_key(skindir):		
		#plugin.set_view_mode(ALL_VIEW_CODES['thumbnail'][skindir])
	return menus

@plugin.route('/clear_cache/')
def clear_cache():
    #urlcache.clear()
    plugin.notify(u'缓存清除完毕！'.encode('utf-8'))

   
def is_video(ext):
    return ext.lower() in ['mkv', 'mp4', 'm4v', 'mov', 'flv', 'wmv', 'asf', 'avi', 'm2ts', 'mts', 'm2t', 'ts', 'mpg', 'mpeg', '3gp', 'rmvb', 'rm', 'iso']

def is_ext_video(ext):
    return ext.lower() in ['iso', 'm2ts', 'mts', 'm2t']

def is_subtitle(ext):
    return ext.lower() in ['srt', 'sub', 'ssa', 'smi', 'ass']

def is_audio(ext):
    return ext.lower() in ['wav', 'flac', 'mp3', 'ogg', 'm4a', 'ape', 'dff', 'dsf', 'wma', 'ra']

def is_image(ext):
    return ext.lower() in ['jpg', 'jpeg', 'bmp', 'tif', 'tiff', 'png', 'gif']

class Player(xbmc.Player):

    def play(self, item='', listitem=None, windowed=False, sublist=None):
        self._sublist = sublist

        super(Player, self).play(item, listitem, windowed)

        self._start_time = time.time()
        while True:
            # print self._start_time, time.time()
            if self._stopped or time.time() - self._start_time > 300:
                if self._totalTime == 999999:
                    raise PlaybackFailed(
                        'XBMC silently failed to start playback')
                break

            xbmc.sleep(500)
        # print 'play end'

    def __init__(self):
        self._stopped = False
        self._totalTime = 999999

        xbmc.Player.__init__(self, xbmc.PLAYER_CORE_AUTO)

    def onPlayBackStarted(self):
        self._totalTime = self.getTotalTime()
        self._start_time = time.time()

        sublist = self._sublist
        if sublist:
            if isinstance(sublist, basestring):
                sublist = [sublist]

            for surl in sublist:
                # print '$'*50, surl
                self.setSubtitles(surl)
            self.setSubtitleStream(0)
            # self.showSubtitles(False)

    def onPlayBackStopped(self):
        self._stopped = True

    def onPlayBackEnded(self):
        self.onPlayBackStopped()


class PlaybackFailed(Exception):

    '''Raised to indicate that xbmc silently failed to play the stream'''


def colorize_label(label, _class=None, color=None):
	color = color or colors.get(_class)

	if not color:
		return label

	if len(color) == 6:
		color = 'FF' + color

	return '[COLOR %s]%s[/COLOR]' % (color, label)


if __name__ == '__main__':
	plugin.run()	
	skindir=xbmc.getSkinDir()
	if setthumbnail['set']:
		if ALL_VIEW_CODES['thumbnail'].has_key(skindir):		
			plugin.set_view_mode(ALL_VIEW_CODES['thumbnail'][skindir])	