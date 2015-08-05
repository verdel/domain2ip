#!/usr/bin/env python


import sys
from lxml import etree
import argparse

def cli():
    parser = argparse.ArgumentParser(description='Zapret list parser')
    parser.add_argument('-f', '--file', required=True, help='input xml file', metavar='file', dest='inputfile')
    parser.add_argument('-i', '--ip', nargs='?', default='ip.txt', help='output txt file with ip addresses', metavar='file', dest='ipfile')
    parser.add_argument('-u', '--url', nargs='?', default='url.txt', help='output txt file with url addresses', metavar='file', dest='urlfile')
    parser.add_argument('-p', '--protocol-remove', nargs='?', default=True, help='remove http:// or https:// from url', metavar='true or false', dest='protocol_remove')
    parser.add_argument('-s', '--silent', action='store_true', default=False, help='hide the output', dest='silent_switch')
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit(1)

    return parser.parse_args()   

def cli_progress(i, end_val, title='Progress', bar_length=20):
    percent = float(i) / end_val
    hashes = '#' * int(round(percent * bar_length))
    spaces = ' ' * (bar_length - len(hashes))
    sys.stdout.write("\r{0}: [{1}] {2}%".format(title, hashes + spaces, int(round(percent * 100))))
    sys.stdout.flush()

def list_to_file(items, dstfile):
    with open(dstfile, 'w') as f:
        count = 1
        size = len(items)
        for item in items:
            if item is not None:
                f.write(item.encode('UTF-8')+'\n')
            if not args.silent_switch:
                cli_progress(count, size, 'Progress')
                count = count + 1

if __name__ == "__main__":

    args = cli()
    parser = etree.XMLParser(encoding='cp1251')
    root = etree.parse(args.inputfile, parser).getroot()
    ips = list()
    urls = list()
    
    for item in root:
        ips.append(item.findtext('ip'))
        url = item.findtext('url')
        if args.protocol_remove and url is not None:
            url = url.replace("http://","")
            url = url.replace("https://","")
        urls.append(url)
    
    list_to_file(ips, args.ipfile)
    list_to_file(urls, args.urlfile)
