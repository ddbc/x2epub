x2epub
======

Convert TEI XML to EPUB

針對當代佛學著作，從 TEI 中選用標籤子集，配合產生電子書 EPUB 程式。

選用的標籤集說明：
http://wiki.ddbc.edu.tw/pages/電子書_XML_TEI_標記

schema/ebook.rnc 是本標籤集的 schema，採用較 TEI 嚴格的限制。


Examples
------------

examples 資料夾裡有幾個簡單範例
	example1/simple.xml 是一個最簡單的範例。
	example2/mixed.xml 是一個綜合範例，使用表格、圖表、項目清單等標記。
	example3/1-1-6.xml 是聖嚴法師的一本結緣電子書的實務範例。


bin
===

bin 資料夾裡是產生 EPUB 的程式

環境: 

* python 3.3.2
* lxml 3.2.3
	
x2epub.py

* x2epub.py 是讀取 XML、產生 EPUB 的程式
* 執行 x2epub.py -h 可以看到參數說明
* 如果參數提供 EPUB Validator 的路徑，那麼 x2epub.py 在產生 EPUB 檔之後也會做驗證，EPUB Validator 可以從這裡下載：https://code.google.com/p/epubcheck/

run-*.py 是執行範例，它呼叫 x2epub.py，並提供一些參數。

epub.py 是製作 EPUB 的模組，x2epub 會使用它，epub.py 改寫自網友分享的模組 https://code.google.com/p/python-epub-builder/。


docs
------

docs/tei2html.txt
	> TEI Element 轉為 HTML Element 對照

Notes
-------

注意：running under linux, 
    run.py 中的epub_path是系統會嘗試產生的目錄，預設產生權限模式為：0755
    若資料夾已存在，但權限模式不為：0755, 有也會有錯誤，請小心。
