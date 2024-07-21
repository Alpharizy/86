import os
import sys
import time
import json
import httpx
import random
import asyncio
import argparse
from urllib.parse import parse_qs

class Tethertod:
    def __init__(self, query, click_min, click_max, interval):
        self.query = query
        self.marin_kitagawa = {key: value[0] for key, value in parse_qs(query).items()}
        user = json.loads(self.marin_kitagawa.get("user", '{}'))
        self.first_name = user.get("first_name", "Unknown")
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en,en-US;q=0.9",
            "Access-Control-Allow-Origin": "*",
            "Authorization": f"tma {query}",
            "Connection": "keep-alive",
            "Host": "tap-tether.org",
            "Referer": "https://tap-tether.org/?tgWebAppStartParam=ZJHQ8GY",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; Redmi 4A / 5A Build/QQ3A.200805.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.185 Mobile Safari/537.36",
        }
        self.ses = httpx.AsyncClient(headers=headers, timeout=200)
        self.click_min = click_min
        self.click_max = click_max
        self.interval = interval

    def log(self, msg):
        print(f"[{self.first_name}] {msg}")

    async def http(self, url, data=None):
        while True:
            try:
                if data is None:
                    res = await self.ses.get(url)
                else:
                    res = await self.ses.post(url, data=data)
                
                open("http.log", "a", encoding="utf-8").write(f"{res.text}\n")
                return res
            except (httpx.HTTPError, httpx.ConnectError) as e:
                self.log(f"Connection error: {e}")
                await asyncio.sleep(1)
            except httpx.RemoteProtocolError:
                self.log("Server not sending response")
                await asyncio.sleep(1)

    async def start(self):
        login_url = "https://tap-tether.org/server/login"
        res = await self.http(login_url)
        if res.status_code != 200:
            return False
        error = res.json().get("error")
        if error is not None and "Expires data" in error:
            self.log("This account needs new query data")
            return False

        data = res.json().get("userData", {})
        usdt = int(data.get("balance", 0)) / 1000000
        usdc = int(data.get("balanceGold", 0)) / 1000000
        re_click = int(data.get("remainingClicks", 0))
        self.log(f"Balance: {usdt} USDT, {usdc} USD Gold")
        
        while True:
            click = random.randint(self.click_min, self.click_max)
            if click > re_click:
                click = re_click
            click_url = f"https://tap-tether.org/server/clicks?clicks={click}&lastClickTime={round(time.time())}"
            res = await self.http(click_url)
            if res.status_code != 200:
                return False
            self.log(f"Success sending tap: {click}")
            re_click = int(res.json().get("remainingClicks", 0))
            if re_click < 10:
                break
            await countdown(self.interval)

        return True

async def countdown(t):
    for i in range(t, 0, -1):
        minu, sec = divmod(i, 60)
        hour, minu = divmod(minu, 60)
        sec = str(sec).zfill(2)
        minu = str(minu).zfill(2)
        hour = str(hour).zfill(2)
        print(f"Waiting {hour}:{minu}:{sec}", flush=True, end="\r")
        await asyncio.sleep(1)

async def main():
    config = json.loads(open("config.json").read())
    click_min = config["click_range"]["min"]
    click_max = config["click_range"]["max"]
    interval = config["interval_click"]
    _countdown = config["countdown"]
    arg = argparse.ArgumentParser()
    arg.add_argument("--data", default="data.txt")
    args = arg.parse_args()
    os.system("cls" if os.name == "nt" else "clear")
    print("Auto Taptether Bot\nBy: @AkasakaID")

    datas = open(args.data).read().splitlines()
    datas = [i for i in datas if len(i) > 0]

    print(f"Total accounts: {len(datas)}")
    while True:
        tasks = [
            Tethertod(q, click_min, click_max, interval).start()
            for q in datas
        ]
        await asyncio.gather(*tasks)
        await countdown(_countdown)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit()

