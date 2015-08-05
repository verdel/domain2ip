#!/usr/bin/env python

import sys
from lxml import etree
import argparse
import socket
import os.path
import os
from shutil import copy,move
import subprocess

def cli():
    parser = argparse.ArgumentParser(description='Zapret list parser')
    
    #parser_xml.add_argument('-f', '--file', required=True, help='input xml file', metavar='file', dest='inputfile')
    #parser_xml.add_argument('-i', '--ip', nargs='?', default='ip.txt', help='output txt file with ip addresses', metavar='file', dest='ipfile')
    #parser_xml.add_argument('-u', '--url', nargs='?', default='url.txt', help='output txt file with url addresses', metavar='file', dest='urlfile')
    
    parser.add_argument('-d', required=True, help='path to directory with xml registry file', metavar='path', dest='path')
    parser.add_argument('-g', default='10.32.14.26', help='gateway ip address', metavar='ip', dest='gateway')    
    parser.add_argument('-r', default='/usr/local/rejik3/banlists/urls', help='path to redirector urls directory', metavar='path', dest='redirector_path')
    parser.add_argument('-p', action='store_false', default=True, help='remove http:// or https:// from url', dest='protocol_remove')    
    parser.add_argument('-s', '--silent', action='store_true', default=False, help='hide the output', dest='silent_switch')
    
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit()

    return parser.parse_args()   

def cli_progress(i, end_val, title='Progress', bar_length=20):
    percent = float(i) / end_val
    hashes = '#' * int(round(percent * bar_length))
    spaces = ' ' * (bar_length - len(hashes))
    sys.stdout.write("\r{0}: [{1}] {2}%".format(title, hashes + spaces, int(round(percent * 100))))
    sys.stdout.flush()

def resolve_domain(d):
    """
    This method returns an array containing
    one or more IP address strings that respond
    as the given domain name
    """
    try:
        data = socket.gethostbyname_ex(d)
        ipx = data[2]
        return ipx
    except Exception:
        return False

def export_to_file(items, dstfile):
    with open(dstfile, 'w') as f:
        count = 1
        size = len(items)
        for item in items:
            if item is not None:
                f.write(item.encode('UTF-8')+'\n')
            if not args.silent_switch:
                cli_progress(count, size, 'Write to file %s' % dstfile)
                count = count + 1

def parse_xml(args):
    parser = etree.XMLParser(encoding='cp1251')
    root = etree.parse(os.path.join(args.path,'dump.xml'), parser).getroot()
    ips = list()
    urls = list()
    
    for item in root:
        ips.append(item.findtext('ip'))
        url = item.findtext('url')
        if args.protocol_remove and url is not None:
            url = url.replace("http://","")
            url = url.replace("https://","")
        urls.append(url)
    
    export_to_file(ips, os.path.join(args.path,'ip.txt'))
    export_to_file(urls, os.path.join(args.path,'url.txt'))

def add_routes(args):
    domains = set(line.rstrip('\n') for line in open(os.path.join(args.path,'url.txt')))
    ips = set(line.rstrip('\n') for line in open(os.path.join(args.path,'ip.txt')))
    
    if not args.silent_switch:
        count = 1
        size = len(domains)
    
    for domain in domains:        
        resolve_ips = resolve_domain(domain)
        if resolve_ips:
            for ip in resolve_ips:
                ips.add(ip)
        
        if not args.silent_switch:
            cli_progress(count, size, 'Resolving domains')
            count = count + 1

    if(os.path.isfile(os.path.join(args.path,'ip.txt.old'))):
        ips_old = set(line.rstrip('\n') for line in open(os.path.join(args.path,'ip.txt.old')))
    else:
        ips_old = set()

    remove_ips = ips_old.difference(ips)
    if(len(remove_ips) > 0 ):
        for item in remove_ips:
            iproute('remove', item)

    for item in ips:
        iproute('update', item)
    
    export_to_file(ips, os.path.join(args.path,'ip.txt.old'))

def reconfigure_squid(args):
    if(os.path.isdir(args.redirector_path)):
        copy(os.path.join(args.path,'url.txt'),args.redirector_path)
        subprocess.call(["/usr/sbin/squid3", "-k", "reconfigure"])

def iproute(operation, ip):
    if(operation == 'remove'):
        subprocess.call(["ip", "r", "del", ip])
    elif(operation == 'update'):
        subprocess.call(["ip", "r", "replace", "via", ip])

if __name__ == "__main__":
    args = cli()
    
    if(os.path.isdir(args.path)):
        if(os.path.isfile(os.path.join(args.path,'dump.xml'))):
            parse_xml(args)
            move(os.path.join(args.path,'dump.xml'),os.path.join(args.path,'dump.xml.old'))
            reconfigure_squid(args)

        add_routes(args)
        
    
    else:
        sys.exit(1)

