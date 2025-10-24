import asyncio
import os
import httpx
import traceback
from hoshino import Service
from nonebot import get_bot, on_command, logger
from .pcrclient import pcrclient, bsdkclient
from .playerpref import decryptxml
from asyncio import Lock
from .util.tools import DATA_PATH, check_client, write_config, load_config

sv_help = '【绑定账号+账号+密码】加号为空格'

sv = Service('你只需要好好出刀', help_=sv_help, visible=True)


@sv.on_fullmatch('绑定账号帮助', only_to_me=False)
async def send_jjchelp(bot, ev):
    await bot.send_private_msg(user_id=ev.user_id, message=sv_help)

account_path = os.path.join(DATA_PATH, 'account')
bind_lck = Lock()
qu_bind_lck = Lock()
bot = get_bot()
client = None
client_cache = {}

captcha_header = {"Content-Type": "application/json",
                  "User-Agent": "pcrjjc2/1.0.0"}

async def captchaVerifier(*args):
    gt = args[0]
    challenge = args[1]
    userid = args[2]
    async with httpx.AsyncClient(timeout=30) as AsyncClient:
        try:
            res = await AsyncClient.get(url=f"https://pcrd.tencentbot.top/geetest_renew?captcha_type=1&challenge={challenge}&gt={gt}&userid={userid}&gs=1", headers=captcha_header)
            res = res.json()
            uuid = res["uuid"]
            ccnt = 0
            while (ccnt := ccnt + 1) < 10:
                res = await AsyncClient.get(url=f"https://pcrd.tencentbot.top/check/{uuid}", headers=captcha_header)
                res = res.json()

                if "queue_num" in res:
                    tim = min(int(res['queue_num']), 3) * 10
                    logger.info(f"过码排队，当前有{res['queue_num']}个在前面，等待{tim}s")
                    await asyncio.sleep(tim)
                    continue

                info = res["info"]
                if 'validate' in info:
                    return info["challenge"], info["gt_user_id"], info["validate"]

                if res["info"] in ["fail", "url invalid"]:
                    raise Exception(f"自动过码失败")

                if res["info"] == "in running":
                    logger.info(f"正在过码。等待5s")
                    await asyncio.sleep(5)

            raise Exception(f"自动过码多次失败")

        except Exception as e:
            raise Exception(f"自动过码异常，{e}")


async def query(acccount_info, is_force=False):
    try:
        acccount_info = acccount_info[0].copy()
        player = acccount_info.get('account', 0) or acccount_info.get('uid')
        if player in client_cache and not is_force:
            client = client_cache[player]
            if await check_client(client):
                return client
        client = pcrclient(bsdkclient(acccount_info))
        await client.login()
        if await check_client(client):
            client_cache[player] = client
            return client
        raise Exception(f"登录失败，请重试")
    except Exception as e:
        raise Exception(f"未知错误：{e}")


@on_command("绑定账号")
async def bind_support(session):
    acccount = {'platform': 4, 'channel': 1, }
    content = session.ctx['message'].extract_plain_text().split()
    qq_id = session.ctx['user_id']
    if len(content) != 3:
        await bot.send_private_msg(user_id=qq_id, message=sv_help)
    else:
        acccount["account"] = content[1]
        acccount['password'] = content[2]
        try:
            client = await query([acccount.copy()], True)
            if await check_client(client):
                load_index = await client.callapi('/load/index', {'carrier': 'OPPO'})
                acccount["name"] = load_index['user_info']['user_name']
                acccount["viewer_id"] = load_index['user_info']['viewer_id']
                await write_config(os.path.join(account_path, f'{qq_id}.json'), [acccount])
                await bot.send_private_msg(user_id=qq_id, message=f'绑定成功账号，当前账号为{acccount["name"]}')
        except Exception as e:
            logger.info(traceback.format_exc())
            await bot.send_private_msg(user_id=qq_id, message="绑定失败" + str(e))


@on_command("删除绑定")
async def unbind_support(session):
    qq_id = session.ctx['user_id']
    account_file = os.path.join(account_path, f'{qq_id}.json')
    
    async with bind_lck:
        try:
            if os.path.exists(account_file):
                os.remove(account_file)
                await bot.send_private_msg(user_id=qq_id, message="已成功解除账号绑定")
            else:
                await bot.send_private_msg(user_id=qq_id, message="您尚未绑定过账号")
        except Exception as e:
            logger.error(f"删除绑定失败: {str(e)}")
            await bot.send_private_msg(user_id=qq_id, message="解除绑定失败，请稍后重试")
