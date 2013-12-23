x2epub
======

Convert TEI XML to EPUB

�w���N��ǵۧ@�A�q TEI ����μ��Ҥl���A�t�X���͹q�l�� EPUB �{���C

��Ϊ����Ҷ������G
http://wiki.ddbc.edu.tw/pages/�q�l��_XML_TEI_�аO

schema/ebook.rnc �O�����Ҷ��� schema�A�ĥθ� TEI �Y�檺����C


Examples
------------

examples ��Ƨ��̦��X��²��d��
	example1/simple.xml �O�@�ӳ�²�檺�d�ҡC
	example2/mixed.xml �O�@�Ӻ�X�d�ҡA�ϥΪ��B�Ϫ�B���زM�浥�аO�C
	example3/1-1-6.xml �O�t�Y�k�v���@�����t�q�l�Ѫ���Ƚd�ҡC


bin
===

bin ��Ƨ��̬O���� EPUB ���{��

����: 

* python 3.3.2
* lxml 3.2.3
	
x2epub.py

* x2epub.py �OŪ�� XML�B���� EPUB ���{��
* ���� x2epub.py -h �i�H�ݨ�Ѽƻ���
* �p�G�Ѽƴ��� EPUB Validator �����|�A���� x2epub.py �b���� EPUB �ɤ���]�|�����ҡAEPUB Validator �i�H�q�o�̤U���Ghttps://code.google.com/p/epubcheck/

run-*.py �O����d�ҡA���I�s x2epub.py�A�ô��Ѥ@�ǰѼơC

epub.py �O�s�@ EPUB ���ҲաAx2epub �|�ϥΥ��Aepub.py ��g�ۺ��ͤ��ɪ��Ҳ� https://code.google.com/p/python-epub-builder/�C


docs
------

docs/tei2html.txt
	> TEI Element �ର HTML Element ���

Notes
-------

�`�N�Grunning under linux, 
    run.py ����epub_path�O�t�η|���ղ��ͪ��ؿ��A�w�]�����v���Ҧ����G0755
    �Y��Ƨ��w�s�b�A���v���Ҧ������G0755, ���]�|�����~�A�Фp�ߡC
