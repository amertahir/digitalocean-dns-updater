#!/usr/bin/env python

import argparse
from urllib.request import urlopen
import json
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "digitalocean-api"))
from digitalocean import ClientV2

config = {
    'api_key':          None,
    'domain':           None,
    'records':          None,
    'record_values':    None,
}


def parse_arguments():
    parser = argparse.ArgumentParser(description='Update DNS A records on a DigitalOcean domain.')
    parser.add_argument('api_key', metavar='api-key', help='DigitalOcean API Key')
    parser.add_argument('domain', help='domain name to update DNS records of')
    parser.add_argument('records', help='list of A records to update, e.g. "remote, pc"')
    parser.add_argument('--record-values',
                        help='assign records to these values instead of external (public) IP address, e.g. '
                             '"10.1.0.1, 192.168.1.1"')
    args = parser.parse_args()
    if len(args.api_key) < 2:
        print("Invalid api-key specified")
        return False
    if len(args.domain) < 2:
        print("Invalid domain specified")
        return False
    if len(args.records) < 2:
        print("Invalid records specified len")
        return False
    records = None
    try:
        records_raw = args.records.split(",")
        if len(records_raw) > 0:
            records = []
        for record in records_raw:
            records.append(record.strip())
    except:
        print("Invalid records specified")
        return False
    if not records or len(records) <= 0:
        print("No records specified")
        return False
    record_values = None
    if args.record_values:
        try:
            record_values_raw = args.record_values.split(",")
            if len(record_values_raw) > 0:
                record_values = []
            for record_value in record_values_raw:
                record_values.append(record_value.strip())
        except:
            print("Invalid record-values specified")
            return False
        if len(record_values) <= 0:
            print("Invalid record-values specified")
            return False
        elif len(record_values) < len(records):
            for i in range(len(records) - len(record_values)):
                record_values.append(record_values[-1])
    config['api-key'] = args.api_key
    config['domain'] = args.domain
    config['records'] = records
    config['record_values'] = record_values
    return True


def get_public_ip():
    data = json.loads(str(urlopen("http://ip.jsontest.com/").read().decode('utf-8')))
    return data["ip"]


def main():
    global config

    if not parse_arguments():
        return

    if not config['record_values']:
        config['record_values'] = []
        public_ip = get_public_ip()
        for i in range(len(config['records'])):
            config['record_values'].append(public_ip)

    client = None
    try:
        client = ClientV2(config['api-key'])
    except:
        print("Cannot connect to DigitalOcean API with specified api-key. Exiting...")
        return

    domain_records = None
    try:
        domain_records = client.domains.list_domain_records(config['domain']).get('domain_records')
    except:
        print("Cannot retrieve " + config['domain'] + "'s domain records. Exiting...")
        return

    for i in range(len(config['records'])):
        record = config['records'][i]
        print("Updating " + record + " in " + config['domain'] + " to point to " + config['record_values'][i])
        domain_record = None
        for obj_dmrec in domain_records:
            if obj_dmrec['type'] == 'A' and obj_dmrec['name'] == record:
                domain_record = obj_dmrec
        if not domain_record:
            print("Cannot find A record " + record + " in " + config['domain'] + ", skipping this record...")
            continue
        try:
            client.domains.update_domain_record(config['domain'], domain_record['id'],
                                                {'data': config['record_values'][i]})
        except:
            print("Cannot update " + record + " in " + config['domain'] + ", skipping this record...")
            continue
        print("done.")


if __name__ == "__main__":
    main()
