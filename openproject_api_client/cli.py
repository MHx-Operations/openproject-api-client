import argparse
import os
import json

import openproject_api_client as opc

def main():
    parser = argparse.ArgumentParser(description='openproject api client')
    parser.add_argument('--apikey', help='api key to access', metavar='apikey', dest='apikey',
                        required=False)
    parser.add_argument('--baseurl', help='baseurl of openproject', metavar='baseurl', dest='baseurl',
                        required=False)

    parser.add_argument('--json', help='output as json', action='store_true', dest='json')

    subparsers = parser.add_subparsers(dest='mode')

    args = parser.parse_args()

    # get OPENPROJECT_BASEURL from cli arg or environment
    baseurl = args.baseurl
    if not baseurl:
        baseurl = os.environ.get('OPENPROJECT_BASEURL')

    if not baseurl:
        raise Exception('specify base url with env:OPENPROJECT_BASEURL or by --baseurl argument')

    # get OPENPROJECT_APIKEY from cli arg or environment
    apikey = args.apikey
    if not apikey:
        apikey = os.environ.get('OPENPROJECT_APIKEY')

    if not apikey:
        raise Exception('specify API key with env:OPENPROJECT_APIKEY or by --apikey argument')

    client = opc.ApiClient(baseurl, apikey)
    try:
        pass
        #if args.mode == 'projects':

    except opc.ApiError as err:
        print("error during request: {}".format(err))


def json_out(data):
    print(json.dumps(data,
                     default=lambda o: o.__dict__,
                     sort_keys=True,
                     indent=2,
                     separators=(',', ': ')))

