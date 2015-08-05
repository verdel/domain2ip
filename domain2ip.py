#!/usr/bin/env python

import sys
import argparse
import socket

def cli():
    parser = argparse.ArgumentParser(description='FQDN to ip converter')
    parser.add_argument('-f', '--file', required=True, help='input FQDN list file', metavar='file', dest='inputfile')
    parser.add_argument('-i', '--ip', nargs='?', default='ip.txt', help='output txt file with ip addresses', metavar='file', dest='ipfile')
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

def getIPx(d):
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

def list_to_file(items, dstfile):
    with open(dstfile, 'w') as f:
        count = 1
        size = len(items)
        for item in items:
            if item is not None:
                f.write(item.encode('UTF-8')+'\n')

if __name__ == "__main__":

    args = cli()
    ip_result = list()
    with open(args.inputfile) as f:
        domains = [line.rstrip('\n') for line in f]

    domains_count = len(domains)    
    if domains_count > 0:
        i = 1
        for domain in domains:
            ips = getIPx(domain)
            if ips:
                for ip in ips:
                    ip_result.append(ip)
            if not args.silent_switch:
                cli_progress(i,domains_count)
            i = i + 1

        if len(ip_result) > 0:
            list_to_file(ip_result, args.ipfile)

