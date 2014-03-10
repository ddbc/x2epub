# coding: utf_8_sig
''' 產生 EPUB 3.0 檔案
環境: Python 3.3 
EPUB 3.0 規格: http://idpf.org/epub
2013.3.21-12.9 周邦信 修改自 https://code.google.com/p/python-epub-builder/
'''
from datetime import datetime, date
import collections
import mimetypes
import os
import shutil
import subprocess
import uuid
import zipfile

class TocNode:
	def __init__(self):
		self.title = ''
		self.href = ''
		self.children = []
		self.play_order = 0

class EpubItem:
	def __init__(self):
		self.id = ''
		self.src_path = ''
		self.dest_path = ''
		self.html = None
		self.mime_type = ''
		self.properties = None

class EpubBook:
	def __init__(self):
		self.epub_ver = 2
		self.uuid = uuid.uuid1()
		self.root_dir = ''
		self.title = '' # 電子書書名
		self.creators = []
		self.items = collections.OrderedDict()
		self.lang = []
		self.toc_root = TocNode() # toc 是 table of content, toc_root 是電子書目錄的根節點
		self.coverImage = None
		self.title_page = None
		self.publisher = None
		self.toc_depth = 0 # 目錄的深度, EPUB 2 目錄規格要用到, EPUB 3 就不需要
		self.toc_style = 'none' # 控制目錄要不要自動加編號, 變數值同 CSS 的 list-style-type
		
	def add_creator(self, name, role = 'aut'):
		c = {'name': name, 'role': role}
		self.creators.append(c)
		
	def add_cover(self, srcPath):
		assert not self.coverImage
		_, ext = os.path.splitext(srcPath)
		destPath = 'cover%s' % ext
		self.coverImage = self.add_image(srcPath, destPath)
	  
	def add_css(self, src_path, dest_path):
		item = EpubItem()
		item.id = 'css_%d' % (len(self.items) + 1)
		item.src_path = src_path
		item.dest_path = dest_path
		item.mime_type = 'text/css'
		self.items[dest_path] = item
		
	def add_image(self, src_path, dest_path):
		if dest_path in self.items:
			return self.items[dest_path]
		item = EpubItem()
		if dest_path in ('cover.jpg', 'cover.png', 'cover.gif'):
			item.id = 'cover-image'
		else:
			item.id = 'image_%d' % (len(self.items) + 1)
		item.src_path = src_path
		item.dest_path = dest_path
		if src_path.endswith('.jpg'):
			item.mime_type = 'image/jpeg'
		elif src_path.endswith('.gif'):
			item.mime_type = 'image/gif'
		elif src_path.endswith('.png'):
			item.mime_type = 'image/png'
		elif src_path.endswith('.svg'):
			item.mime_type = 'image/svg+xml'
		self.items[dest_path] = item
		return item

	def add_html(self, src_path, dest_path, html=None, properties=None):
		''' 在電子書加入一個 HTML '''
		item = EpubItem()
		if dest_path == 'cover.html':
			item.id = 'cover'
		else:
			item.id = 'html_{}'.format(len(self.items) + 1)
		item.src_path = src_path
		item.dest_path = dest_path
		item.html = html
		item.mime_type = 'application/xhtml+xml'
		item.properties = properties
		self.items[dest_path] = item
		return item
		
	def add_toc_node(self, parent):
		node = TocNode()
		parent.children.append(node)
		return node
		
	def add_lang(self, lang):
		self.lang.append(lang)

	def make_dirs(self):
		dir = os.path.join(self.root_dir, 'META-INF')
		if not os.path.exists(dir):
			os.makedirs(dir)
		
		dir = os.path.join(self.root_dir, 'OPS')
		if not os.path.exists(dir):
			os.makedirs(dir)
		
	# _single_leading_underscore: weak "internal use" indicator. 
	# E.g. from M import * does not import objects whose name starts with an underscore.
	def _write_mimetype(self):
		fout = open(os.path.join(self.root_dir, 'mimetype'), 'w')
		fout.write('application/epub+zip')
		fout.close()
		
	def _write_items(self):
		for item in self.items.values():
			if item.html is None:
				dest = os.path.join(self.root_dir, 'OPS', item.dest_path)
				dest_folder = os.path.dirname(dest)
				if not os.path.exists(dest_folder):
					os.makedirs(dest_folder)
				shutil.copyfile(item.src_path, dest)
			else:
				path = os.path.join(self.root_dir, 'OPS', item.dest_path)
				fout = open(path, 'w', encoding='utf8')
				fout.write(item.html)
				fout.close()
			
	def _write_container_xml(self):
		# container.xml 必須要實作在META-INF/ 之下，其內容是用來紀錄主要 EPUB 內容根檔案的mime type 與路徑
		path = os.path.join(self.root_dir, 'META-INF', 'container.xml')
		fout = open(path, 'w')
		# <rootfile> 的 @full-path 屬性放的是 Package Document 的路徑
		fout.write('''<?xml version="1.0" ?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
   <rootfiles>
      <rootfile full-path="OPS/content.opf" media-type="application/oebps-package+xml"/>
   </rootfiles>
</container>''')
		fout.close()
		
	def _write_content_OPF(self):
		''' Package Document 
		規格: http://idpf.org/epub/30/spec/epub30-publications.html '''
		s = '<?xml version="1.0" encoding="UTF-8"?>\n'
		if self.epub_ver == 2:
			s += '<package version="2.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">\n'
		else:
			s += '<package version="3.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId">\n'
		
		# metadate
		if self.epub_ver == 2:
			s += '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">\n'
		else:
			s += '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
		s += '<dc:identifier id="BookId">urn:uuid:{}</dc:identifier>\n'.format(self.uuid)
		s += '<dc:title id="title">{}</dc:title>\n'.format(self.title)
		i = 0
		for creator in self.creators:
			i += 1
			if self.epub_ver == 2:
				s += '<dc:creator opf:role="{}">{}</dc:creator>\n'.format(creator['role'], creator['name'])
			else:
				s += '<dc:creator id="creator{}">{}</dc:creator>\n'.format(i, creator['name'])
				s += '<meta refines="#creator{}" property="role" scheme="marc:relators">{}</meta>\n'.format(i, creator['role'])
				s += '<meta refines="#creator{0}" property="display-seq">{0}</meta>\n'.format(i)
			
		for lang in self.lang:
			s += '<dc:language>{}</dc:language>\n'.format(lang)
		if self.epub_ver > 2:
			s += '<meta property="dcterms:modified">{}</meta>\n'.format(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
		if self.publisher is not None:
			s += '<dc:publisher>{}</dc:publisher>\n'.format(self.publisher)
		s += '<dc:date>{}</dc:date>'.format(date.today())
		s += '</metadata>\n'
		
		# manifest
		s += '<manifest>\n'
		if self.epub_ver == 2:
			s += '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />\n'
		else:
			s += '<item id="toc" href="toc.html" properties="nav" media-type="application/xhtml+xml"/>\n'
		for item in self.items.values():
			s += '<item'
			if item.dest_path == 'cover.jpg':
				s += ' properties="cover-image"'
			elif item.properties is not None:
				s += ' properties="{}"'.format(item.properties)
			s += ' id="{}" href="{}" media-type="{}" />\n'.format(item.id, item.dest_path, item.mime_type)
		s += '</manifest>\n'
		
		# spine
		# Package Document 的內容必須含有一個spine 區塊，內含一個或以上的<itemref> 元素。
		# spine 的目的是用來描述當使用者一頁一頁向下翻時，資料的正確讀取順序。
		if self.epub_ver == 2:
			s += '<spine toc="ncx">\n'
		else:
			s += '<spine>\n'
			s += '<itemref idref="toc" />\n'
		for item in self.items.values():
			if item.mime_type == 'application/xhtml+xml':
				s += '<itemref idref="{}" />'.format(item.id)
		s+= '</spine>\n'
		
		s += '</package>'
		
		path = os.path.join(self.root_dir, 'OPS', 'content.opf')
		with open(path, 'w', encoding='utf8') as fo:
			fo.write(s)
			
	def _toc_node2html(self, node):
		if self.toc_style == 'none':
			style = ' style="list-style-type:none;margin-left:-2em"'
		elif self.toc_style != '':
			style = ' style="list-style-type:{};"'.format(self.toc_style)
		else:
			style = ''
		r = ''
		if node.title!='':
			r += '<a href="{}">{}</a>'.format(node.href, node.title)
		if len(node.children)>0:
			r += '<ol{}>\n'.format(style)
			for n in node.children:
				if self.toc_style == 'none':
					r += '<li style="margin-left:1em;text-indent:-1em">'
				else:
					r += '<li>'
				r += self._toc_node2html(n) + '</li>\n'
			r += '</ol>\n'
		return r

	def _write_toc(self):
		s = '''<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
<meta charset="utf-8" />
<title>{}</title>
</head>
<body>
<nav id="toc" epub:type="toc">
<h1>Contents</h1>'''.format(self.title)
		s += self._toc_node2html(self.toc_root)
		s += '</nav></body></html>'
		path = os.path.join(self.root_dir, 'OPS', 'toc.html')
		fo = open(path, 'w', encoding='utf8')
		fo.write(s)
		fo.close()

	def _toc_node2ncx(self, node):
		r = ''
		if node.title!='':
			r = '''<navPoint id="navPoint-{0}" playOrder="{0}">
	<navLabel>
		<text>{1}</text>
	</navLabel>
	<content src="{2}" />\n'''.format(node.play_order, node.title, node.href)
		if len(node.children)>0:
			for n in node.children:
				r += self._toc_node2ncx(n)
		if node.title != '':
			r += '</navPoint>\n'
		return r
		
	def _write_ncx(self):
		s = '''<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN" "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" xml:lang="en" version="2005-1">
    <head>
        <meta name="dtb:uid" content="urn:uuid:{}" />
        <meta name="dtb:depth" content="{}" />
        <meta name="dtb:totalPageCount" content="0" />
        <meta name="dtb:maxPageNumber" content="0" />
    </head>
    <docTitle>
        <text>{}</text>
    </docTitle>
    <navMap>\n'''.format(self.uuid, self.toc_depth, self.title)
		s += self._toc_node2ncx(self.toc_root)
		s += '    </navMap></ncx>'
		path = os.path.join(self.root_dir, 'OPS', 'toc.ncx')
		with open(path, 'w', encoding='utf8') as fo:
			fo.write(s)
			
	def create_book(self, root_dir):
		self.root_dir = root_dir
		self.make_dirs()
		self._write_mimetype()
		self._write_items()
		self._write_container_xml()
		self._write_content_OPF()
		if self.epub_ver == 2:
			self._write_ncx()
		else:
			self._write_toc()

def check_epub(checkerPath, epubPath):
	# 在 linux 下使用 subprocess.call 有問題, 改用 Popen
	#subprocess.call(['java', '-jar', checkerPath, epubPath], shell = True)
	
	# 在 windows 下使用 subprocess.Popen 有問題
	#p = subprocess.Popen("java -jar %s %s" %(checkerPath, epubPath), shell=True)
	#sts = os.waitpid(p.pid, 0)
	
	os.system('java -jar ' + checkerPath + ' ' + epubPath)

def append_folder_to_zip(folder, file_list):
	files = os.listdir(folder)
	for f in files:
		path = os.path.join(folder, f)
		if os.path.isdir(path):
			append_folder_to_zip(path, file_list)
		else:
			file_list.append(path)

def create_archive(root_dir, output_path):
	folder = os.path.dirname(output_path)
	if not os.path.exists(folder):
		os.makedirs(folder)
	
	fout = zipfile.ZipFile(output_path, 'w')
	cwd = os.getcwd()
	os.chdir(root_dir)
	fout.write('mimetype', compress_type = zipfile.ZIP_STORED)
	fileList = []
	fileList.append(os.path.join('META-INF', 'container.xml'))
	append_folder_to_zip('OPS', fileList)
	for filePath in fileList:
		fout.write(filePath, compress_type = zipfile.ZIP_DEFLATED)
	fout.close()
	os.chdir(cwd)
