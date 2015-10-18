# -*- coding: utf-8 -*-
# default.py
import urllib,urllib2,re,xbmcplugin,xbmcgui,subprocess,sys,os,os.path,sys,xbmcaddon,xbmcvfs,random,hashlib
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
sys.path.append (__resource__)


colors = {'back': '7FFF00','dir': '8B4513','video': 'FF0000','next': 'CCCCFF','bt': 'FF0066', 'audio': '0000FF', 'subtitle':'505050', 'image': '00FFFF', '-1':'FF0000','0':'8B4513','1':'CCCCFF','2':'7FFF00', 'menu':'FFFF00'}

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
cookiefile = os.path.join(ppath, 'cookie.dat')

subcache = plugin.get_storage('subcache')
#urlcache = plugin.get_storage('urlcache', TTL=5)
		
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
	login_page = xl.urlopen('http://passport.115.com/?ct=login&ac=qrcode_token&is_ssl=1')
	msgs=json.loads(xl.fetch(login_page))
	uid,_t,sign=msgs['uid'],msgs['time'],msgs['sign']
	
	sessionid_page=xl.urlopen('http://msg.115.com/proapi/anonymous.php?ac=signin&user_id='+str(uid)+'&sign='+str(sign)+'&time='+str(_t))
	sessionmsgs=json.loads(xl.fetch(sessionid_page))
	sessionid=sessionmsgs['session_id']
	
	qrcode_url='http://www.115.com/scan/?ct=scan&ac=qrcode&uid='+str(uid)+'&_t='+str(_t)
	
	window = xbmcgui.Window()
	window.setCoordinateResolution(0)
	qr_code = xbmcgui.ControlImage(0, 0, 450, 450, qrcode_url)
	qr_code.setPosition((1920 - qr_code.getWidth()) / 2, (1080 - qr_code.getHeight()) / 2)
	window.addControl(qr_code)
	window.show()
	start_time = time.time()
	while time.time() - start_time < 90:
		time.sleep(1)
		try:		
			key_page=xl.urlopen('http://im16.115.com/chat/r?VER=2&c=b0&s='+str(sessionid)+'&_='+str(long(time.time())))
			keymsgs=json.loads(xl.fetch(key_page))
			status=keymsgs[0]['p'][0]['status']
			if status==1002:
				xl.cookiejar.clear()
				key=keymsgs[0]['p'][0]['key']
				key_page=xl.urlopen('http://passport.115.com/?ct=login&ac=qrcode&is_ssl=1&key='+key+'&v=android&goto=https%3A%2F%2Fpassport.115.com%2F%3Fct%3Dlogin%26ac%3Dempty_page%26is_ssl%3D1')
				xl.cookiejar.save(cookiefile, ignore_discard=True)
				plugin.notify(msg='登录成功')
				break
		except:			
			continue
	else:
		plugin.notify(msg='登录超时')	
		xl.cookiejar.save(cookiefile, ignore_discard=True)
	window.close()
	return

@plugin.route('/setting')
def setting():
	ret= plugin.open_settings()
	return


@plugin.route('/')
def index():
	item = [
		{'label': '网盘', 'path': plugin.url_for('getfile',cid='0',offset=0,star='0')},
		{'label': '星标列表', 'path': plugin.url_for('getfile',cid='0',offset=0,star='1')},
		#{'label': '记事本', 'path': plugin.url_for('note',cid='0',offset=0)},
		{'label': '离线任务列表', 'path': plugin.url_for('offline_list')},
		{'label': '搜索', 'path': plugin.url_for('search',mstr='0',offset=0)},
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
	
	if data['state']:
		imagecount=0
		items=[]
		for item in data['data']:
			if item.has_key('sha'):
				if item.has_key('iv'):
					items.append({'label': colorize_label(item['n'], 'video'),'thumbnail':item['u'], 'path': plugin.url_for('play',pc=item['pc'],name=item['n'].encode('UTF-8'),iso='0'),'is_playable': True,'properties': {'isPlayable': ''}})
				elif item.has_key('ms'):
					items.append({'label': colorize_label(item['n'], 'video'),'thumbnail':item['u'], 'path': plugin.url_for('playimg',pc=item['pc'],name=item['n'].encode('UTF-8')),'is_playable': True,'properties': {'isPlayable': ''}})
					imagecount+=1
				elif  is_subtitle(item['ico']):					
					subcache[item['n'].encode('UTF-8')]=item['pc']
					#items.append({'label': colorize_label(item['n'], 'video'),'path': plugin.url_for('play',pc=item['pc'],name=item['n'].encode('UTF-8'),iso='1'),'is_playable': True,'properties': {'isPlayable': ''}})
				elif  is_video(item['ico']) or is_ext_video(item['ico']):
					#items.append({'label': colorize_label(item['n'], 'video'),'path': plugin.url_for('playiso',pc=item['pc'],name=item['n'].encode('UTF-8')),'is_playable': True,'properties': {'isPlayable': ''}})
					items.append({'label': colorize_label(item['n'], 'video'),'path': plugin.url_for('play',pc=item['pc'],name=item['n'].encode('UTF-8'),iso='1'),'is_playable': True,'properties': {'isPlayable': ''}})
				#elif  is_audio(item['ico']):
				#	items.append({'label': colorize_label(item['n'], 'video'),'path': plugin.url_for('play',pc=item['pc'],name=item['n'].encode('UTF-8'),iso='1'),'is_playable': True,'properties': {'isPlayable': ''}})
				elif item['ico']=='torrent':
					items.append({'label': colorize_label(item['n'], 'bt'), 'path': plugin.url_for('offline_bt',sha1=item['sha']),'is_playable': True,'properties': {'isPlayable': ''}})
			else:
				items.append({'label': colorize_label(item['n'], 'dir'), 'path': plugin.url_for('getfile',cid=item['cid'],offset=0,star='0')})
		if data['count']>int(offset)+int(pageitem):
			items.append({'label': colorize_label('下一页', 'next'), 'path': plugin.url_for('search',mstr=mstr,offset=str(int(offset)+int(pageitem)))})
		skindir=xbmc.getSkinDir()
		if imagecount >= 10 and imagecount * 2 > len(items):              
			if ALL_VIEW_CODES['thumbnail'].has_key(skindir):
				xbmc.executebuiltin('Container.SetViewMode(%s)' % ALL_VIEW_CODES['thumbnail'][skindir])
		return items
	else:
		plugin.notify(msg='数据获取失败,错误信息:'+str(data['error']))
		return
	
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
		# if star=='0':
			# items.append({'label': colorize_label('星标列表', 'true'), 'path': plugin.url_for('getfile',cid=cid,offset='0',star='1')})
		# else:
			# items.append({'label': colorize_label('正常列表', 'false'), 'path': plugin.url_for('getfile',cid=cid,offset='0',star='0')})
		#items.append({'label': colorize_label("制作播放列表", 'back'), 'path': plugin.url_for('lxlist',cid=cid,name=data['path'][len(data['path'])-1]['name'].encode('UTF-8'))})
		for item in data['data']:
			if item.has_key('sha'):
				if item.has_key('iv'):
					items.append({'label': colorize_label(item['n'], 'video'),'thumbnail':item['u'], 'path': plugin.url_for('play',pc=item['pc'],name=item['n'].encode('UTF-8'),iso='0'),'is_playable': True,'properties': {'isPlayable': ''}})
				elif item.has_key('ms'):
					items.append({'label': colorize_label(item['n'], 'video'),'thumbnail':item['u'], 'path': plugin.url_for('playimg',pc=item['pc'],name=item['n'].encode('UTF-8')),'is_playable': True,'properties': {'isPlayable': ''}})
					imagecount+=1
				elif  is_subtitle(item['ico']):					
					subcache[item['n'].encode('UTF-8')]=item['pc']
					#items.append({'label': colorize_label(item['n'], 'video'),'path': plugin.url_for('play',pc=item['pc'],name=item['n'].encode('UTF-8'),iso='1'),'is_playable': True,'properties': {'isPlayable': ''}})
				elif  is_video(item['ico']) or is_ext_video(item['ico']):
					#items.append({'label': colorize_label(item['n'], 'video'),'path': plugin.url_for('playiso',pc=item['pc'],name=item['n'].encode('UTF-8')),'is_playable': True,'properties': {'isPlayable': ''}})
					items.append({'label': colorize_label(item['n'], 'video'),'path': plugin.url_for('play',pc=item['pc'],name=item['n'].encode('UTF-8'),iso='1'),'is_playable': True,'properties': {'isPlayable': ''}})
				#elif  is_audio(item['ico']):
				#	items.append({'label': colorize_label(item['n'], 'video'),'path': plugin.url_for('play',pc=item['pc'],name=item['n'].encode('UTF-8'),iso='1'),'is_playable': True,'properties': {'isPlayable': ''}})
				elif item['ico']=='torrent':
					items.append({'label': colorize_label(item['n'], 'bt'), 'path': plugin.url_for('offline_bt',sha1=item['sha']),'is_playable': True,'properties': {'isPlayable': ''}})
			else:
				items.append({'label': colorize_label(item['n'], 'dir'), 'path': plugin.url_for('getfile',cid=item['cid'],offset=0,star='0')})
		if data['count']>int(offset)+int(pageitem):
			items.append({'label': colorize_label('下一页', 'next'), 'path': plugin.url_for('getfile',cid=cid,offset=str(int(offset)+int(pageitem)),star=star)})
			#urlcache[cid+"/"+offset+"/"+str(star)] = items
		#xbmc.executebuiltin('Container.SetViewMode(8)')
		skindir=xbmc.getSkinDir()
		if imagecount >= 10 and imagecount * 2 > len(items):              
			if ALL_VIEW_CODES['thumbnail'].has_key(skindir):
				xbmc.executebuiltin('Container.SetViewMode(%s)' % ALL_VIEW_CODES['thumbnail'][skindir])
		return items
	else:
		plugin.notify(msg='数据获取失败,错误信息:'+str(data['error']))
		return

@plugin.route('/offline_bt/<sha1>')
def offline_bt(sha1):
	dialog = xbmcgui.Dialog()
	ret = dialog.yesno('115网盘提示', '是否离线文件?')
	if ret:
		uid = xl.getcookieatt('.115.com', 'ssoinfoA1')
		uid=uid[:uid.index('%')]
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
	
@plugin.route('/playiso/<pc>/<name>')
def playiso(pc,name):
	data=xl.urlopen("http://web.api.115.com/files/download?pickcode="+pc+"&_="+str(long(time.time())))
	data=json.loads(xl.fetch(data))
	if data['state']:
		videourl=data['file_url']
	else:
		plugin.notify(msg='无视频文件.')
		return
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
			
		# data=xl.urlopen("http://web.api.115.com/files/download?pickcode="+pc+"&_="+str(long(time.time())))		
		# data=json.loads(xl.fetch(data))
		# if data['state']:
			# videourl=data['file_url']
		# else:
			# plugin.notify(msg='无视频文件.')
			# return
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
	
	sublist = []
	if iso=='0':
		msg=''
		name=name[:name.rfind('.')]		
		sub_pcs=[]
		for k,v in subcache.items():
			if k.find(name)!= -1:
				sub_pcs.append(v)
		
		for subpc in sub_pcs:
			suburl=get_file_download_url(subpc)
			if videourl!='':
				sublist.append(suburl)
			msg+="同目录下找到"+str(len(sublist))+"个字幕 "		
	
		# data=xl.urlopen('http://web.api.115.com/files/video?pickcode='+pc)
		# data=json.loads(xl.fetch(data))
		# if 'subtitle_info' in data:
			# sublist+=[s['url'] for s in data['subtitle_info']]
		#plugin.notify(plugin.get_setting('subtitle'))
		if len(sublist)==0:
			if plugin.get_setting('subtitle')=='true':		
				data=xl.urlopen('http://web.api.115.com/movies/subtitle?pickcode='+pc)
				data=json.loads(xl.fetch(data))		
				if data['state']:
					sublist+=[s['url'] for s in data['data']]
					msg+="共找到"+str(len(sublist))+"个字幕"
		plugin.notify(msg)
		
	
	listitem=xbmcgui.ListItem()
	listitem.setInfo(type="Video", infoLabels={'Title': name})
	player = Player()
	player.play(videourl, listitem, sublist=sublist)
	return
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
	uid = xl.getcookieatt('.115.com', 'ssoinfoA1')
	uid=uid[:uid.index('%')]
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
	return
	
@plugin.route('/offline_list')
def offline_list():
	msg_st={'-1': '任务失败','0': '任务停止','1': '下载中','2': '下载完成'}
	data=xl.urlopen("http://115.com/?ct=offline&ac=space&_="+str(time.time()))
	data=xl.fetch(data)
	data=json.loads(data[data.index('{'):])
	sign=data['sign']
	time1=data['time']
	uid = xl.getcookieatt('.115.com', 'ssoinfoA1')
	uid=uid[:uid.index('%')]
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
@plugin.route('/playnote/<url>')
def playnote(url):
	
	dialog = xbmcgui.Dialog()
	if 'magnet:' in url:
		ret = dialog.yesno('115网盘提示', '是否离线文件?')
		if ret:
			offline(url)
	elif 'http:' in url:
		ret = dialog.yesno('115网盘提示', '是否离线文件?')
		if ret:
			offline(url)
	elif 'ftp:' in url:
		ret = dialog.yesno('115网盘提示', '是否离线文件?')
		if ret:
			offline(url)
	elif 'https:' in url:
		ret = dialog.yesno('115网盘提示', '是否离线文件?')
		if ret:
			offline(url)
	elif 'ed2k:' in url:
		ret = dialog.yesno('115网盘提示', '是否离线文件?')
		if ret:
			offline(url)
	elif '115:' in url:
		plugin.notify(url)
		play(url[4:],url)
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
            # # print self._start_time, time.time()
            if self._stopped or time.time() - self._start_time > 300:
                if self._totalTime == 999999:
					raise PlaybackFailed('XBMC silently failed to start playback')
					break

            xbmc.sleep(500)

    def __init__(self):
        self._stopped = False
        self._totalTime = 999999

        xbmc.Player.__init__(self, xbmc.PLAYER_CORE_AUTO)

    def onPlayBackStarted(self):
        self._totalTime = self.getTotalTime()
        self._start_time = time.time()

        sublist = self._sublist
        if sublist:
            for surl in reversed(sublist):
                # print '$'*50, surl
                self.setSubtitles(surl)

            #self.setSubtitleStream(1)
            self.showSubtitles(True)

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