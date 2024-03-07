from hashlib import sha1
import hmac
import requests
import json
import urllib
import os
from pathlib import Path
import logging

import time

DOGECLOUD_ACCESSKEY = os.environ['DOGECLOUD_ACCESSKEY']
DOGECLOUD_SECRETKEY = os.environ['DOGECLOUD_SECRETKEY']

DOMAIN_CERT_PAIRS = os.environ['DOMAIN_CERT_PAIRS']

def do_cert_update(domain_path_list):
    dp_dict = { d[0]: d[1] for d in domain_path_list if len(d) == 2 }
    d_list = dp_dict.keys()
    resp = dogecloud_api('/cdn/domain/list.json')
    if resp['code'] != 200:
        return logging.warning(f"failed to retrieve domain list, reason {resp['msg']}")
    online_list = resp['data']['domains']
    domain_to_replace = [ x for x in online_list if x['name'] in d_list ]

    cert_to_configure = []
    cert_to_remove = []
    for d in domain_to_replace:
        logging.info(f"processing domain {d['name']}")
        cert = upload_cert(d['name'], dp_dict[d['name']])
        if cert is not None:
            cert_to_configure.append((d, cert))

    # configure new certs
    for d, new_cert in cert_to_configure:
        result = configure_cert(d['name'], new_cert)
        if result and d['cert_id'] != 0:
            cert_to_remove.append(d['cert_id'])

    # remove old certs that were successfully replaced
    remove_certs(cert_to_remove)

def upload_cert(domain, path):
    fullchain = Path(path, "fullchain.pem").read_text()
    privkey = Path(path, "privkey.pem").read_text()

    resp = dogecloud_api("/cdn/cert/upload.json", {
        "note": f"{domain} ssl cert",
        "cert": fullchain,
        "private": privkey,
    })
    if resp['code'] != 200:
        logging.warning(f"failed to upload cert for domain {domain}, reason: {resp['msg']}")
        return
    logging.info(f"succefully uploaded cert for domain {domain}")
    return resp['data']['id']

def configure_cert(domain, new_cert_id):
    resp_conf = dogecloud_api(f"/cdn/domain/config.json?domain={domain}",{
        'cert_id': new_cert_id,
    })
    if resp_conf['code'] != 200:
        logging.warning(f"failed to set cert for domain {domain}, reason: {resp_conf['msg']}")
        return False
    logging.info(f"succefully set cert for domain {domain} to cert_id {new_cert_id}")
    return True
        
def remove_certs(cert_ids):
    for id in cert_ids:
        api = dogecloud_api('/cdn/cert/delete.json', {
            'id': id
        })
        if api['code'] != 200:
            logging.warning(f"failed to remove cert id {id}, reason: {api['msg']}")
        else:
            logging.info(f"successfully removed cert id {id}")

## source: https://docs.dogecloud.com/cdn/api-access-token?id=python

def dogecloud_api(api_path, data={}, json_mode=True):
    """
    调用多吉云API

    :param api_path:    调用的 API 接口地址，包含 URL 请求参数 QueryString，例如：/console/vfetch/add.json?url=xxx&a=1&b=2
    :param data:        POST 的数据，字典，例如 {'a': 1, 'b': 2}，传递此参数表示不是 GET 请求而是 POST 请求
    :param json_mode:   数据 data 是否以 JSON 格式请求，默认为 false 则使用表单形式（a=1&b=2）

    :type api_path: string
    :type data: dict
    :type json_mode bool

    :return dict: 返回的数据
    """

    # 这里替换为你的多吉云永久 AccessKey 和 SecretKey，可在用户中心 - 密钥管理中查看
    # 请勿在客户端暴露 AccessKey 和 SecretKey，否则恶意用户将获得账号完全控制权
    access_key = DOGECLOUD_ACCESSKEY
    secret_key = DOGECLOUD_SECRETKEY

    body = ''
    mime = ''
    if json_mode:
        body = json.dumps(data)
        mime = 'application/json'
    else:
        body = urllib.parse.urlencode(data) # Python 2 可以直接用 urllib.urlencode
        mime = 'application/x-www-form-urlencoded'
    sign_str = api_path + "\n" + body
    signed_data = hmac.new(secret_key.encode('utf-8'), sign_str.encode('utf-8'), sha1)
    sign = signed_data.digest().hex()
    authorization = 'TOKEN ' + access_key + ':' + sign
    response = requests.post('https://api.dogecloud.com' + api_path, data=body, headers = {
        'Authorization': authorization,
        'Content-Type': mime
    })
    return response.json()

if __name__ =="__main__":
    logging.basicConfig(level=logging.INFO)

    all_domains = [ d.split(':') for d in DOMAIN_CERT_PAIRS.split(',') ]
    logging.debug("parsed domains to process: ")
    logging.debug(all_domains)
    do_cert_update(all_domains)