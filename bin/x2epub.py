# coding: utf8
''' 將 XML 轉換為 EPUB 格式
作者: 周邦信, 2013.10.22-11.19
環境:
	MS Windows 8.1
	Python 3.3.2
	lxml 3.2.3
'''
import argparse, collections
import datetime
import os
import re
import sys
import shutil
from string import Template
from lxml import etree
import epub

IGNORE_SPACE = ('table', 'row')

class HtmlClass:
	def __init__(self, c=None):
		self.classes = []
		if c is not None:
			self.classes.append(c)
	def add(self, c):
		self.classes.append(c)
	def __str__(self):
		return ' '.join(self.classes)
		
class MyNode:
	def __init__(self, tag=None):
		self.tag = tag
		self.att = collections.OrderedDict()
		self.content = ''
		
	def set(self, key, value):
		self.att[key] = value
		
	def __str__(self):
		r = '<' + self.tag
		for k, v in self.att.items():
			r += ' {}="{}"'.format(k, v)
		if self.content == '':
			r += '/>'
		else:
			r += '>' + self.content + '</{}>'.format(self.tag)
		return r

class XmlToEpub:
	def __init__(self, config):
		self.config = config
		self.config.setdefault('convert_lb_to_br', True) # 預設 lb 標記會換行
		self.config.setdefault('epub_ver', 3) # 預設 EPUB version 3
		
		# graphic_base
		# 圖片的來源位置，預設與來源 XML 同一目錄
		# 圖片會 copy 到 EPUB 封裝中與 HTML 相同資料夾下面
		if 'xml' in config:
			self.config.setdefault('graphic_base', os.path.dirname(config['xml']))
		
		# glyph_base
		# 缺字字圖的來源位置，預設與來源 XML 同一目錄
		if 'xml' in config:
			self.config.setdefault('glyph_base', os.path.dirname(config['xml']))
		
		self.div_level = 0
		self.chapter = 0
		self.counter_note = 0
		self.head_count = 0
		self.list_level = 0
		self.anchors = set()
		self.chars = {}
		self.properties = set()
		
	def handle_text(self, s):
		if s is None: return ''
		s = s.replace('&', '&amp;')
		s = s.replace('\n', '')
		if 'handle_text' in self.config:
			func = self.config['handle_text']
			s = func(s)
		return s
	
	def traverse(self, node, mode='html'):
		r=''
		if node.tag not in IGNORE_SPACE:
			r += self.handle_text(node.text)
		for n in node.iterchildren(): 
			r += self.handle_node(n, mode)
			if node.tag not in IGNORE_SPACE:
				r += self.handle_text(n.tail)
		return r
		
	def handle_bibl(self, e):
		parent = e.getparent()
		rend = e.get('rend')
		content = self.traverse(e)
		if rend is None:
			return content
		if 'display:block' in rend:
			class1 = 'bibl'
			if e.get('lang')=='zh':
				class1 = 'bibl_zh'
			return '<p style="{}" class="{}">{}</p>'.format(rend, class1, content)
		else:
			return content
			
	def handle_cell(self, e):
		n = MyNode('td')
		rend = e.get('rend')
		if rend is not None:
			n.set('style', rend)
		if 'rows' in e.attrib:
			n.set('rowspan', e.get('rows'))
		if 'cols' in e.attrib:
			n.set('colspan', e.get('cols'))
		n.content = self.traverse(e)
		return str(n)
		
	def handle_cit(self, e):
		rend = e.get('rend')
		content = self.traverse(e)
		if rend is None:
			r = content
		elif 'display:block' in rend:
			r = '<div class="cit">{}</div>\n'.format(content)
		else:
			r = '<span style="{}">{}</span>'.format(rend, content)
		return r
		
	def handle_div(self, e):
		parent = e.getparent()
		self.div_level += 1
		head = e.find('head')
		if head is not None:
			node = self.book.add_toc_node(self.current_toc_node[-1])
			self.current_toc_node.append(node)
			if self.div_level > self.book.toc_depth:
				self.book.toc_depth = self.div_level
		if parent.tag!='front' and self.div_level == 1:
			self.chapter += 1
			self.bottom_notes = ''
			self.counter_note = 0
			self.anchors = set()
			self.properties = set()
			content = self.traverse(e)
			if (e.get('type')=='copyright') and ('after_copyright' in self.config):
				content += self.config['after_copyright']
			r = '<html xmlns="http://www.w3.org/1999/xhtml">\n<head>\n'
			r += self.charset_declaration + '\n'
			r += '<title>{}</title>\n'.format(self.book.title)
			if 'css' in self.config:
				r += '<link rel="stylesheet" type="text/css" href="{}" />\n'.format(self.css_filename)
			r += '</head>\n<body>\n'
			
			node = MyNode('div')
			rend = e.get('rend')
			if rend is not None:
				node.set('style', rend)
				
			rendition = e.get('rendition')
			if rendition is not None:
				node.set('class', rendition)
				
			node.content = content
			r += str(node)
			if self.bottom_notes != '':
				r += '<div>' + self.bottom_notes + '</div>\n'
			r += '</body></html>'
			
			fn = '{}.htm'.format(self.chapter)
			if len(self.properties) > 0:
				properties = ' '.join(self.properties)
			else:
				properties = None
			self.book.add_html('', fn, r, properties=properties)
		else:
			node = MyNode('div')
			rend = e.get('rend')
			if rend is not None:
				node.set('style', rend)
				
			rendition = e.get('rendition')
			if rendition is not None:
				node.set('class', rendition)
				
			node.content = self.traverse(e)
			r = str(node)
		self.div_level -= 1
		if head is not None:
			self.current_toc_node.pop()
		return r
		
	def handle_figure(self, e):
		rend = e.get('rend', 'text-align:center')
		content = self.traverse(e)
		r = '<div style="{}">{}</div>\n'.format(rend, content)
		return r
		
	def handle_front(self, e):
		r = '<html xmlns="http://www.w3.org/1999/xhtml">\n<head>\n'
		r += self.charset_declaration + '\n'
		r += '<title>{}</title>\n'.format(self.book.title)
		if self.css_filename is not None:
			r += '<link rel="stylesheet" type="text/css" href="{}" />\n'.format(self.css_filename)
		r += '</head>\n<body>\n<div>\n' + self.traverse(e) + '</div></body></html>'
		
		fn = 'front.htm'
		self.book.add_html('', fn, r)
		return r
		
	def handle_g(self, e):
		ref = e.get('ref')
		id = ref[1:]
		url = self.chars[id]
		if url.endswith('.svg'):
			self.properties.add('svg')
		r = '<img class="glyph" src="{}" width="18" />'.format(url)
		src = os.path.join(self.config['glyph_base'], url)
		print(191, src)
		self.book.add_image(src, url)
		return r
		
	def handle_graphic(self, e):
		url = e.get('url')
		rend = e.get('rend')
		
		if url.endswith('.svg'):
			self.properties.add('svg')
			
		src = os.path.join(self.config['graphic_base'], e.get('url'))
		self.book.add_image(src, url)
		
		node = MyNode('img')
		node.set('src', url)
		node.set('alt', '')
		if rend is not None:
			node.set('style', rend)
			
		if 'width' in e.attrib:
			w = e.get('width')
			mo = re.match(r'([\d\.]+)([^\d]*)$', w)
			node.set('width', mo.group(1))
			if mo.group(2) != '':
				node.set('unit', mo.group(2))
				
		if 'height' in e.attrib:
			h = e.get('height')
			mo = re.match(r'([\d\.]+)([^\d]*)$', h)
			node.set('height', mo.group(1))
			if mo.group(2) != '':
				node.set('unit', mo.group(2))

		r = str(node)
		return r
		
	def handle_head(self, e):
		head = self.traverse(e)
		parent = e.getparent()
		rend = e.get('rend', '')
		node = MyNode()
		if parent.tag == 'div':
			if e.get('type')=='sub':
				if self.div_level > 5:
					node.tag = 'p'
					node.set('class', 'head')
				else:
					node.tag = 'h{}'.format(self.div_level+1)
			else:
				self.head_count += 1
				toc_node = self.current_toc_node[-1]
				if e.get('lang') == 'en' and toc_node.title != '':
					toc_node.title += ' '
				toc_node.title += self.traverse(e, 'text')
				if toc_node.href == '':
					toc_node.href = '{}.htm#a_{}'.format(self.chapter, self.head_count)
					toc_node.play_order = self.head_count
				if self.div_level > 6:
					node.tag = 'p'
					node.set('class', 'head')
				else:
					node.tag = 'h{}'.format(self.div_level)
				node.set('id', 'a_{}'.format(self.head_count))
		elif parent.tag == 'table':
			node.tag = 'caption'
		elif parent.tag == 'figure':
			node.tag = 'p'
			node.set('class', 'figure_head')
		else:
			node.tag = 'p'
			node.set('class', 'head')
		if rend != '':
			node.set('style', rend)
		node.content = head
		return str(node)
		
	def handle_label(self, e):
		rend = e.get('rend', '')
		node = MyNode('div')
		node.set('class', 'label')
		if rend != '':
			node.set('style', rend)
		node.content = self.traverse(e)
		return str(node)
		
	def handle_lg(self, e):
		c = HtmlClass('lg')
		if 'rendition' in e.attrib:
			c.add(e.get('rendition'))
			
		parent = e.getparent()
		if parent.tag=='quote' and e.get('lang')=='zh':
			c.add('quote_zh')
			
		node = MyNode('div')
		node.set('class', str(c))
		rend = e.get('rend')
		if rend is not None:
			node.set('style', rend)
		node.content = self.traverse(e)
		return str(node)
		
	def handle_list(self, e):
		self.list_level += 1
		
		node = MyNode()
		rend = e.get('rend')
		if rend is not None:
			node.set('style', rend)
		node.content = self.traverse(e)
		
		type = e.get('type')
		if type=='ordered':
			node.tag = 'ol'
			r = str(node)
		elif type=='bulleted':
			node.tag = 'ul'
			r = str(node)
		else:
			node.tag = 'div'
			node.set('class', 'list')
			r = str(node)
			
		self.list_level -= 1
		return r
		
	def handle_note(self, e, mode):
		place = e.get('place', '')
		r = ''
		content = self.traverse(e)
		if place == 'inline':
			r = '<span class="inline_note">' + content + '</span>'
		elif place == 'inline2':  # 雙行夾註
			r = '<span class="inline_note2">' + content + '</span>'
		elif place == 'bottom':
			if mode=='text':
				r = ''
			else:
				id = e.get('id')
				n = e.get('n')
				if id is None:
					if n is None:
						self.counter_note += 1
						n = str(self.counter_note)
					id = 'n' + n
				id = id.replace('*', 'star')
				self.bottom_notes += '<p id="{}" class="note"><a href="#noteAnchor_{}">{}</a> {}</p>\n'.format(id, id, n, content)
				a_id = 'noteAnchor_{}'.format(id)
				r = '<a id="{}" href="#{}" class="noteAnchor">{}</a>'.format(a_id, id, n)
				self.anchors.add(a_id)
		else:
			id = e.get('id')
			n = e.get('n')
			if id is not None:
				node = MyNode('a')
				node.set('id', id)
				if n is not None:
					href = '#noteAnchor_{}'.format(id)
					node.set('href', href)
					node.content = n
					r = str(node) + ' '
				else:
					r = str(node)
			r += content
		return r
		
	def handle_opener(self, e):
		node = MyNode('p')
		rend = e.get('rend', '')
		if rend != '':
			node.set('style', rend)
		if 'rendition' in e.attrib:
			c = e.get('rendition')
			if c.startswith('#'):
				c = c[1:]
			node.set('class', c)
		else:
			node.set('class', 'opener')
		node.content = self.traverse(e)
		r = str(node) + '\n'
		return r
		
	def handle_p(self, e):
		# 賢度法師《華嚴經十地品淺釋》p. 332, <p> 包 <lg>
		if has_descendant(e, 'lg'):
			tag = 'div'
		else:
			tag = 'p'
		node = MyNode(tag)
		rend = e.get('rend', '')
		if rend != '':
			node.set('style', rend)
		if 'rendition' in e.attrib:
			c = e.get('rendition')
			if c.startswith('#'):
				c = c[1:]
			node.set('class', c)
		node.content = self.traverse(e)
		r = str(node) + '\n'
		return r
		
	def handle_quote(self, e):
		rend = e.get('rend', '')
		c = HtmlClass('quote')
		lang = e.get('lang')
		if lang is None or lang=='zh':
			c.add('quote_zh')
		node = MyNode('p')
		node.set('class', c)
		if ('display:block' in rend) or ('display:inline-block' in rend):
			node.tag = 'div'
		else:
			if (e.find('p') is None) and (e.find('lg') is None):
				node.tag = 'span'
			else:
				node.tag = 'div'
		if rend != '':
			node.set('style', rend)
		node.content = self.traverse(e)
		r = str(node)
		return r
		
	def handle_ref(self, e):
		content = self.traverse(e)
		if e.get('type')=='noteAnchor':
			target = e.get('target')
			a_id = 'noteAnchor_{}'.format(target[1:])
			# 如果相同的 target 已出現過, 就不給 ID, 避免 ID 重複
			if a_id in self.anchors:
				r = '<a href="{}" class="noteAnchor">{}</a>'.format(target, content)
			else:
				self.anchors.add(a_id)
				r = '<a id="{}" href="{}" class="noteAnchor">{}</a>'.format(a_id, target, content)
		else:
			r = '<a href="{}">{}</a>'.format(e.get('target'), content)
		return r
		
	def handle_seg(self, e):
		node = MyNode('span')
		if 'rend' in e.attrib:
			node.set('style', e.get('rend'))
		if 'rendition' in e.attrib:
			node.set('class', e.get('rendition'))
		node.content = self.traverse(e)
		if e.get('rendition') == 'ruby_base' and  node.content == ' ':
			node.content = '　'
		r = str(node)
		return r
		
	def handle_supplied(self,e):
		node = MyNode('span')
		node.set('class', 'supplied')
		node.content = self.traverse(e)
		return str(node)
		
	def handle_table(self, e):
		rend = e.get('rend')
		rendition = e.get('rendition')
		node = MyNode('table')
		if rend is None:
			node.set('style', 'border-collapse: collapse;')
		else:
			node.set('style', rend)
		if rendition is not None:
			node.set('class', rendition)
		node.content = self.traverse(e)
		return str(node)
		
	def handle_title(self, e):
		rend = e.get('rend')
		content = self.traverse(e)
		if rend is None:
			lang = e.get('lang')
			if lang is None:
				r = content
			else:
				if lang in ('en', 'pi'):
					r = '<span style="font-style:italic">{}</span>'.format(content)
				else:
					r = content
		else:
			r = '<span style="{}">{}</span>'.format(rend, content)
		return r
		
	def handle_node(self, e, mode):
		tag=e.tag
		if tag==etree.Comment: return ''
		parent = e.getparent()
		if 'lang' not in e.attrib:
			lang = parent.get('lang', 'zh')
			e.set('lang', lang)
		r = ''
		if tag=='bibl': 
			r = self.handle_bibl(e)
		elif tag=='byline': 
			rend = e.get('rend')
			if rend is None:
				r = '<p class="byline">'
			else:
				r = '<p class="byline" style="{}">'.format(rend)
			r += self.traverse(e) + '</p>\n'
		elif tag=='cell': 
			r = self.handle_cell(e)
		elif tag=='cit':
			r = self.handle_cit(e)
		elif tag=='div':
			r = self.handle_div(e)
		elif tag=='emph':
			r = '<span class="emph">{}</span>'.format(self.traverse(e))
		elif tag=='figure':
			r = self.handle_figure(e)
		elif tag=='front':
			r = self.handle_front(e)
		elif tag=='g': 
			r = self.handle_g(e)
		elif tag=='graphic': 
			r = self.handle_graphic(e)
		elif tag=='head': 
			r = self.handle_head(e)
		elif tag=='item':
			rend = e.get('rend')
			if parent.get('type') is None:
				if rend is None:
					r += '<div class="item">' + self.traverse(e) + '</div>'
				else:
					r += '<div style="{}">{}</div>'.format(rend, self.traverse(e))
			else:
				node = MyNode('li')
				node.content = self.traverse(e)
				if rend is not None:
					node.set('style', rend)
				r += str(node)
		elif tag=='l':
			r += self.traverse(e)
			next = e.getnext()
			if (next is not None) and (next.tag in ('l', 'lb', 'pb')):
				r += '<br/>\n'
		elif tag=='label':
			r = self.handle_label(e)
		elif tag=='lb':
			type = e.get('type', '')
			if mode=='html':
				if type=='always-newline':
					r = '<br/>'
				elif parent.tag != 'table':
					if self.config['convert_lb_to_br']:
						r = '<br/>'
		elif tag=='lg':
			r = self.handle_lg(e)
		elif tag=='list':
			r = self.handle_list(e)
		elif tag=='note':
			r = self.handle_note(e, mode)
		elif tag=='opener': 
			r = self.handle_opener(e)
		elif tag=='p': 
			r = self.handle_p(e)
		elif tag=='placeName': 
			rend = e.get('rend')
			if rend is None:
				r = self.traverse(e)
			else:
				r = '<span style="{}">{}</span>'.format(rend, self.traverse(e))
		elif tag=='q': 
			rend = e.get('rend')
			if rend is None:
				r = '<span class="quote">' + self.traverse(e) + '</span>'
			elif 'display:block' in rend:
				r = '<p class="quote">{}</p>\n'.format(self.traverse(e))
			else:
				r = '<span class="quote" style="{}">{}</span>'.format(rend, self.traverse(e))
		elif tag=='quote':
			r = self.handle_quote(e)
		elif tag=='ref':
			r = self.handle_ref(e)
		elif tag=='row': 
			r = '<tr>' + self.traverse(e) + '</tr>\n'
		elif tag=='seg': 
			r = self.handle_seg(e)
		elif tag=='supplied':
			r = self.handle_supplied(e)
		elif tag=='table': 
			r = self.handle_table(e)
		elif tag=='term': 
			rend = e.get('rend')
			if rend is None:
				r = self.traverse(e)
			else:
				r = '<span style="{}">{}</span>'.format(rend, self.traverse(e))
		elif tag=='text':
			if e.get('lang') is None:
				e.set('lang', 'zh')
			r = self.traverse(e)
		elif tag=='title': 
			r = self.handle_title(e)
		else: 
			r = self.traverse(e)
		return r
		
	def get_author(self):
		root = self.root
		# 可能有多個作者
		authors = root.xpath('//titleStmt/author')
		if len(authors) == 0: # 如果沒有 author 就用 editor
			authors = root.xpath('//titleStmt/editor')
		names = []
		for a in authors:
			names.append(a.text)
		return '、'.join(names)

	def add_license_page(self):
		''' 加入版權頁 '''
		with open(self.config['license_template'], 'r', encoding='utf8') as fi:
			text = fi.read()
		template = Template(text)
		
		args = {}
		
		root = self.root
		authors = root.xpath('//titleStmt/author')
		names = {}
		for a in authors:
			role = a.get('role', '著者')
			if role not in names:
				names[role] = []
			names[role].append(a.text)
			
		args['author'] = ''
		for k, v in names.items():
			args['author'] += '<p style="margin-left:3em;text-indent:-3em">' + k + '：' + '、'.join(v) + '</p>'
		
		args['resp'] = ''
		for e in root.iter("respStmt"):
			args['resp'] += etree.tounicode(e, method="text") + '<br />\n'
			
		isbn = root.findtext('.//idno')
		if isbn is None:
			args['isbn'] = ''
		else:
			args['isbn'] = 'ISBN：{}'.format(isbn)
			
		e = root.find('.//date')
		if e is None:
			args['date'] = ''
		else:
			d = e.get('when-iso')
			if d is None:
				d = e.get('when')
			args['date'] = '紙本出版時間：{}<br />'.format(d)
		args['today'] = datetime.date.today()
		args['charset_declaration'] = self.charset_declaration
		html = template.substitute(args)
		
		self.book.add_html('', 'license.htm', html)
		node = self.book.add_toc_node(self.book.toc_root)
		self.head_count += 1
		node.title = '版權頁'
		node.href = 'license.htm'
		node.play_order = self.head_count
		
	def convert(self):
		if 'xml' in self.config:
			tree = etree.parse(self.config['xml'])
			tree.xinclude()
			tree = strip_namespaces(tree)
		elif 'lxml-etree' in self.config:
			tree = self.config['lxml-etree']
		else:
			return False
		root = tree.getroot()
		self.root = root

		self.book = epub.EpubBook()
		self.book.epub_ver = self.config['epub_ver']
		if self.book.epub_ver == 3:
			# 避開 epub validate 時產生的問題
			self.charset_declaration = '<meta charset="utf-8" />'
		else:
			self.charset_declaration = '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />'
		self.book.title = root.findtext('.//titleStmt/title')
		
		if 'publisher' in self.config:
			self.book.publisher = self.config['publisher']

		author = self.get_author()
		self.book.add_creator(author)

		self.book.add_lang('zh-TW')
		self.book.add_lang('en')

		if 'cover_page' in self.config:
			if os.path.exists(self.config['cover_page']):
				self.book.add_cover(self.config['cover_page'])

		self.css_filename = None
		if 'css' in self.config:
			self.css_filename = os.path.basename(self.config['css'])
			self.book.add_css(self.config['css'], self.css_filename)
			
		# 收集缺字資訊
		char_decl = root.find('.//charDecl')
		if char_decl is not None:
			for e in char_decl.iter('char'):
				id = e.get('id')
				graphic = e.find('graphic')
				url = graphic.get('url')
				self.chars[id] = url
				print(id, url)
		self.current_toc_node = [self.book.toc_root]
		self.list_level = 0
		
		text_node = root.find('.//text')
		self.traverse(text_node)
		
		if 'license_template' in self.config:
			self.add_license_page()
		
		temp = self.config['temp_folder']
		if os.path.exists(temp):
			clear_folder(temp)
		self.book.create_book(temp)

		epub.create_archive(temp, self.config['epub_path'])
		if 'epub_validator' in self.config:
			epub.check_epub(self.config['epub_validator'], self.config['epub_path'])

def clear_folder(folder):
	files = os.listdir(folder)
	for f in files:
		path = os.path.join(folder, f)
		if os.path.isdir(path):
			clear_folder(path)
			#os.rmdir(path)
			shutil.rmtree(path)
		else:
			os.remove(path)

def strip_namespaces(tree):
	# http://wiki.tei-c.org/index.php/Remove-Namespaces.xsl
	xslt_root = etree.XML('''\
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" indent="no"/>

<xsl:template match="/|comment()|processing-instruction()">
    <xsl:copy>
      <xsl:apply-templates/>
    </xsl:copy>
</xsl:template>

<xsl:template match="*">
    <xsl:element name="{local-name()}">
      <xsl:apply-templates select="@*|node()"/>
    </xsl:element>
</xsl:template>

<xsl:template match="@*">
    <xsl:attribute name="{local-name()}">
      <xsl:value-of select="."/>
    </xsl:attribute>
</xsl:template>
</xsl:stylesheet>
''')
	transform = etree.XSLT(xslt_root)
	tree = transform(tree)
	return tree

def has_descendant(ance, desc):
	for e in ance.iterdescendants(tag=desc):
		return True
	return False