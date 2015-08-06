#!/usr/bin/env python

import adns
import argparse
from lxml import etree
import os
import os.path
from shutil import copy,move
import subprocess
import socket
import sys
from urlparse import urlparse


class AsyncResolver(object):
    def __init__(self, hosts, dns, intensity=100):
        """
        hosts: a list of hosts to resolve
        intensity: how many hosts to resolve at once
        """
        self.hosts = hosts
        self.intensity = intensity
        self.dns = dns
        self.adns = adns.init(adns.iflags.noautosys,sys.stderr,"nameserver " + dns)

    def resolve(self):
        resolved_hosts = set()
        active_queries = {}
        host_queue = self.hosts

        def collect_results():
            for query in self.adns.completed():
                answer = query.check()
                host = active_queries[query]
                del active_queries[query]
                if answer[0] == 0:
                    ips = answer[3]
                    for ip in ips:
                        resolved_hosts.add(ip)
                elif answer[0] == 101: # CNAME
                    query = self.adns.submit(answer[1], adns.rr.A)
                    active_queries[query] = host
                # else:
                #     try:
                #         adns.exception(answer[0])
                #     except adns.Error, e:
                #         description = e[1]
                #         print "%s - %s" % (description,host)

        def finished_resolving():
            return len(host_queue) == 0

        while not finished_resolving():
            while host_queue and len(active_queries) < self.intensity:
                host = host_queue.pop()
                
                if not (host.startswith('http://') or host.startswith('https://')):
                    host = '%s%s' % ('//', host)
                host = urlparse(host)

                query = self.adns.submit(host.netloc, adns.rr.A)
                active_queries[query] = host.netloc
            collect_results()

        return resolved_hosts

def cli():
    parser = argparse.ArgumentParser(description='Zapret list parser')
    
    parser.add_argument('-d', required=True, help='path to directory with xml registry file', metavar='path', dest='path')
    parser.add_argument('-r', default='/usr/local/rejik3/banlists/urls', help='path to redirector urls directory (default: /usr/local/rejik3/banlists/urls)', metavar='path', dest='redirector_path')
    parser.add_argument('-g', default='10.32.14.26', help='gateway ip address', metavar='ip', dest='gateway')    
    parser.add_argument('-p', action='store_false', default=True, help='remove http:// or https:// from url (default: True)', dest='protocol_remove')    
    parser.add_argument('-s', '--silent', action='store_true', default=False, help='hide the output', dest='silent_switch')
    
    if len(sys.argv)==1:
        parser.print_help()
        sys.exit()

    return parser.parse_args()   

def resolve_domain(hosts):
    ar = AsyncResolver(hosts, dns = '8.8.8.8', intensity=500)
    resolved_hosts = ar.resolve()
    return resolved_hosts

def export_to_file(items, dstfile):
    with open(dstfile, 'w') as f:
        for item in items:
            if item is not None:
                f.write(item.encode('UTF-8')+'\n')

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
    
    if(os.path.isfile(os.path.join(args.path,'url.txt'))):
        domains = set(line.rstrip('\n') for line in open(os.path.join(args.path,'url.txt')))
    else:
        domains = set()

    if(os.path.isfile(os.path.join(args.path,'ip.txt'))):
        ips = set(line.rstrip('\n') for line in open(os.path.join(args.path,'ip.txt')))
    else:
        ips = set()

    if(os.path.isfile(os.path.join(args.path,'ip.txt.old'))):
        ips_old = set(line.rstrip('\n') for line in open(os.path.join(args.path,'ip.txt.old')))
    else:
        ips_old = set()
    
    ips.update(resolve_domain(domains))
    remove_ips = ips_old.difference(ips)
    if(len(remove_ips) > 0 ):
        for item in remove_ips:
            iproute('remove', item)

    for item in ips:
        iproute('update', item, args.gateway)
    
    export_to_file(ips, os.path.join(args.path,'ip.txt.old'))

def reconfigure_squid(args):
    if(os.path.isdir(args.redirector_path)):
        copy(os.path.join(args.path,'url.txt'),args.redirector_path)
        subprocess.call(["/usr/sbin/squid3", "-k", "reconfigure"])

def iproute(operation, ip, gateway=None):
    if(operation == 'remove'):
        subprocess.call(["ip", "r", "del", ip])
    elif(operation == 'update'):
        subprocess.call(["ip", "r", "replace", ip, "via", gateway])

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

