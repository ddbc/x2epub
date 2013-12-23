# coding: utf_8_sig
import x2epub

config = {
	'xml': '../examples/example1/simple.xml',  #xml的位置
	'epub_path': '../output/test-ex1.epub', #輸出的epub位置
	'epub_ver': 3, #optional,產生的epub版本, 2,3 都行, 但2測試的比較少, 預設是3
	'temp_folder': './temp/epub', #封裝前暫存檔產生位置
	'epub_validator': r'./epubcheck-3.0/epubcheck-3.0.jar', #optional,驗證檔, 環境中必須已經設好java
}

converter = x2epub.XmlToEpub(config)
converter.convert()
