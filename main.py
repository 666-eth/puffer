# -*- coding: utf-8 -*-
# @Time     :2024/2/1 4:20
# @Author   :ym
# @File     :main.py
# @Software :PyCharm
import random
import re
import time
from typing import Union
from urllib.parse import unquote, urlparse, parse_qs

import requests
from eth_account import Account
from eth_account.messages import encode_defunct
from loguru import logger

family_list = ["Bankless", "BayAreaWSB", "DeFi Dad", "DiscusFish", "Puffers", "SaulDataman", "The Whale", "benmo",
               "mrblock", "陈剑Jason"]


def authorize_twitter(auth_token: str, proxies: dict, auth_data: dict) -> Union[bool, str]:
    try:
        session = requests.session()
        session.proxies = proxies
        response = session.get(url='https://twitter.com/home', cookies={
            'auth_token': auth_token,
            'ct0': '960eb16898ea5b715b54e54a8f58c172'
        })
        ct0 = re.findall('ct0=(.*?);', dict(response.headers)['set-cookie'])[0]
        cookies = {'ct0': ct0, 'auth_token': auth_token}
        _headers = {
            'authority': 'twitter.com',
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://twitter.com',
            'pragma': 'no-cache',
            'referer': 'https://twitter.com/dop_org',
            'x-csrf-token': ct0,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',

        }
        data = {'include_profile_interstitial_type': '1', 'include_blocking': '1', 'include_blocked_by': '1',
                'include_followed_by': '1', 'include_want_retweets': '1', 'include_mute_edge': '1',
                'include_can_dm': '1',
                'include_can_media_tag': '1', 'include_ext_is_blue_verified': '1', 'include_ext_verified_type': '1',
                'include_ext_profile_image_shape': '1', 'skip_status': '1', 'user_id': '1600006045644066816', }
        # 先关注一下
        follow_response = session.post('https://twitter.com/i/api/1.1/friendships/create.json', cookies=cookies,
                                       headers=_headers,
                                       data=data)
        # 转发一下推文
        json_data = {'variables': {'tweet_id': '1751954283052810298', 'dark_request': False, },
                     'queryId': 'ojPdsZsimiJrUGLR1sjUtA'}
        __headers = {'authority': 'twitter.com', 'accept': '*/*', 'accept-language': 'zh-CN,zh;q=0.9',
                     'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
                     'cache-control': 'no-cache', 'content-type': 'application/json', 'origin': 'https://twitter.com',
                     'pragma': 'no-cache', 'referer': 'https://twitter.com/puffer_finance/status/1751954283052810298',
                     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                     'x-csrf-token': ct0}
        repost_response = session.post('https://twitter.com/i/api/graphql/ojPdsZsimiJrUGLR1sjUtA/CreateRetweet',
                                       cookies=cookies, headers=__headers, json=json_data)
        logger.debug(f'关注:{follow_response.status_code},转发:{repost_response.status_code}')

        if repost_response.status_code != 200 or follow_response.status_code != 200:
            logger.warning(f'推特关注或转发失败:{auth_token}')
            return False
        params = {
            'code_challenge': auth_data['code_challenge'],
            'code_challenge_method': 'plain',
            'client_id': auth_data['client_id'],
            'redirect_uri': 'https://quest-api.puffer.fi/puffer-quest/twitter/authorize_callback',
            'response_type': 'code',
            'scope': 'tweet.read users.read offline.access',
            'state': auth_data['state'],
        }

        response = session.get('https://twitter.com/i/api/2/oauth2/authorize', params=params, cookies=cookies,
                               headers=_headers).json()
        auth_code = response.get('auth_code', False)
        if not auth_code:
            logger.warning(f'推特授权失败:{auth_token}')
            return False
        data = {'approval': 'true', 'code': auth_code}
        response = session.post('https://twitter.com/i/api/2/oauth2/authorize', headers=_headers, data=data,
                                cookies=cookies).json()
        logger.info(response)
        redirect_uri = response['redirect_uri']
        return redirect_uri
    except Exception as e:
        logger.error(e)
        return False


def write_fail(account, auth_token):
    with open('fail.txt', 'a+') as f:
        f.writelines(f'{account.address}----{auth_token}\n')


def run(private_key: str, auth_token: str, invite_code='', proxies=None):
    """

    :param private_key: 私钥
    :param auth_token: 推特 auth_token
    :param invite_code: 邀请码
    :param proxies: 代理 格式 : {"http":"http://user:password@ip:port","https":"http://user:password@ip:port"}
    :return:
    """
    account = Account.from_key(private_key)
    try:
        session = requests.session()
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://quest.puffer.fi/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        }

        response = session.get(
            f'https://quest-api.puffer.fi/puffer-quest/twitter/request_authorize?uuid=&operate=bind&source=puffer_quest&invite_code=&redirect=https://quest.puffer.fi/chapter1&t={int(time.time() * 1000)}',
            headers=headers, allow_redirects=True)
        query_params = parse_qs(urlparse(unquote(response.url)).query)
        auth_data = dict(
            client_id=query_params['client_id'][0],
            code_challenge=query_params['code_challenge'][0],
            state=query_params['state'][0])
        redirect_uri = authorize_twitter(auth_token, proxies, auth_data)
        if redirect_uri is False:
            logger.warning(f'推特授权失败:{account.address.lower()}')
            write_fail(account, auth_token)
            return
        response = session.get(url=redirect_uri, headers=headers)
        query_params = parse_qs(urlparse(unquote(response.url)).query)
        if not query_params:
            logger.warning(f'认证失败:{account.address}:{auth_token}')
            write_fail(account, auth_token)
            return
        uuid = query_params['uuid'][0]
        username = query_params['username'][0]
        params = {'uuid': uuid, 'address': account.address.lower(), 'invite_code': ''}
        response = session.get('https://quest-api.puffer.fi/puffer-quest/wallet/tip_info', params=params,
                               headers=headers).json()
        logger.debug(response)
        signature = account.sign_message(encode_defunct(text=response['data']['tip_info'])).signature.hex()
        logger.debug(f'address:{account.address},signature:{signature}')
        json_data = {'timestamp': response["data"]['timestamp'], 'uuid': uuid, 'address': account.address.lower(),
                     'signature': signature, 'invite_code': invite_code}

        response = session.post('https://quest-api.puffer.fi/puffer-quest/wallet/connect', headers=headers,
                                json=json_data).json()
        if response['errno'] == 0 and response['errmsg'] == 'no error':
            logger.info(f'{account.address}:{response["data"]["username"]}')
            token = response['data']['token']
        else:
            logger.warning(f'登录账户失败:{account.address}:{response}')
            write_fail(account, auth_token)
            return
        json_data = {'family': random.choice(family_list)}
        headers.update({'jwt-token': token})

        response = session.post('https://quest-api.puffer.fi/puffer-quest/chapter1/link_family', headers=headers,
                                json=json_data).json()
        if response['errno'] == 0 and response['errmsg'] == 'no error':
            logger.success(f'link_family:{account.address}:{response}')
            with open('success.txt', 'a+') as f:
                f.writelines(f'{account.address}----{account.key.hex()}----{username}----{auth_token}\n')
        else:
            logger.warning(f'link_family:{account.address}:{response}')
            write_fail(account, auth_token)
    except Exception as e:
        logger.error(e)
        with open('fail.txt', 'a+') as f:
            f.writelines(f'{account.address}----{auth_token}\n')


if __name__ == '__main__':
    _account = Account.create()
    logger.debug(_account.address)
    logger.debug(_account.key.hex())
    run(_account.key.hex(), 'e7162cd6e7ff1c79a4b29d78f761dfcbc1c4c1f7')

    # run(_account.key.hex(), 'e7162cd6e7ff1c79a4b29d78f761dfcbc1c4c1f7', 'invite_code',
    #     proxies={'http': "http://127.0.0.1:8888", "https": "http://127.0.0.1:8888"})
