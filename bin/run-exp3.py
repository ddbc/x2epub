# coding: utf_8_sig
import x2epub

config = {
	'xml': '../examples/example3/1-1-6.xml',  #xml的位置
	'epub_path': '../output/test-ex3.epub', #輸出的epub位置
	'cover_page': '../examples/example3/cover.jpg', #optional, 封面圖片
	'graphic_base': '../examples/example3/graphic', #optional, 內含圖片的來源位置，會copy到epub封裝中與html相同資料夾下面
	'css': '../examples/example3/shengyen.css',  #optional,引用的CSS檔的來源位置，會copy到epub封裝中與html相同資料夾下面
	'epub_ver': 3, #optional,產生的epub版本, 2,3 都行, 但2測試的比較少, 預設是3
	'temp_folder': './temp/epub', #封裝前暫存檔產生位置
	'epub_validator': r'./epubcheck-3.0/epubcheck-3.0.jar', #optional,驗證檔, 環境中必須已經設好java
}

converter = x2epub.XmlToEpub(config)
converter.convert()
