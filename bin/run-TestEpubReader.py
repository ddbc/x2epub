# coding: utf_8_sig
import x2epub
BASE = '../examples/Test-EPUB-Reader/'
config = {
	'xml': BASE + 'TestEpubReader.xml',  #xml的位置
	'css': BASE + 'TestEpubReader.css',  #optional,引用的CSS檔的來源位置，會copy到epub封裝中與html相同資料夾下面
	'epub_path': '../output/test-epub-reader.epub', #輸出的epub位置
	'temp_folder': './temp/epub', #封裝前暫存檔產生位置
	'epub_validator': r'./epubcheck-3.0.1/epubcheck-3.0.1.jar', #optional,驗證檔, 環境中必須已經設好java
}

converter = x2epub.XmlToEpub(config)
converter.convert()
