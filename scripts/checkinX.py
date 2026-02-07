import os
import asyncio
import aiohttp
import random
import hashlib
import time
from typing import List, Optional, Dict
from urllib.parse import parse_qs, urlparse
from aiohttp_socks import ProxyConnector
from colorama import init, Fore, Style
from datetime import datetime

init(autoreset=True)

BORDER_WIDTH = 80

CLIENT_ID = "WFVrTEdYOFJUNHk0NnVHUXowZGc6MTpjaQ"
REDIRECT_URI = "https://app.onvoyage.ai/auth/callback/x"
SCOPE = "users.read tweet.read offline.access"
CODE_CHALLENGE = "challenge"
CODE_CHALLENGE_METHOD = "plain"
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

ONVOYAGE_BACKEND = "https://onvoyage-backend-954067898723.us-central1.run.app"

CONFIG = {
    "DELAY_BETWEEN_ACCOUNTS": 3,
    "RETRY_ATTEMPTS": 3,
    "RETRY_DELAY": 5,
    "THREADS": 5,
    "TIMEOUT": 60,
}

LANG = {
    'vi': {
        'title': 'ONVOYAGE AUTO CHECK-IN - TWITTER LOGIN',
        'loading_accounts': 'Đang tải tài khoản Twitter...',
        'found_accounts': 'Tìm thấy {count} tài khoản',
        'loading_proxies': 'Đang tải proxy...',
        'found_proxies': 'Tìm thấy {count} proxy',
        'no_proxies': 'Không tìm thấy proxy, chạy không proxy',
        'processing': '⚙ ĐANG XỬ LÝ {count} TÀI KHOẢN',
        'twitter_auth': 'Đang xác thực Twitter...',
        'twitter_auth_success': 'Twitter xác thực thành công!',
        'twitter_auth_failed': 'Twitter xác thực thất bại',
        'logging_in': 'Đang đăng nhập Onvoyage...',
        'login_success': 'Đăng nhập thành công!',
        'login_failed': 'Đăng nhập thất bại',
        'onboarding': 'Đang hoàn thành onboarding...',
        'onboard_success': 'Onboarding thành công!',
        'onboard_skip': 'Đã onboard trước đó',
        'checking_in': 'Đang check-in...',
        'checkin_success': 'Check-in thành công!',
        'checkin_failed': 'Check-in thất bại',
        'already_checkin': 'Đã check-in hôm nay',
        'reward': 'Phần thưởng',
        'streak': 'Chuỗi ngày',
        'username': 'Tên người dùng',
        'status': 'Trạng thái',
        'wallets': 'Ví',
        'vpoints': 'VPoints',
        'vpoints_earned': 'VPoints kiếm được',
        'vpoints_spent': 'VPoints đã dùng',
        'success': '✅ Thành công',
        'failed': '❌ Thất bại',
        'error': 'Lỗi',
        'using_proxy': 'Proxy',
        'no_proxy': 'Không proxy',
        'completed': '✅ HOÀN THÀNH: {successful}/{total} TÀI KHOẢN THÀNH CÔNG',
        'pausing': 'Tạm dừng',
        'seconds': 'giây',
        'account': 'Tài khoản',
        'public_ip': 'IP công khai',
        'unknown': 'Không xác định',
        'thog': 'Đã check-in hôm nay rồi! Vui lòng thực hiện vào ngày mai...',
    },
    'en': {
        'title': 'ONVOYAGE AUTO CHECK-IN - TWITTER LOGIN',
        'loading_accounts': 'Loading Twitter accounts...',
        'found_accounts': 'Found {count} accounts',
        'loading_proxies': 'Loading proxies...',
        'found_proxies': 'Found {count} proxies',
        'no_proxies': 'No proxies found, running without proxy',
        'processing': '⚙ PROCESSING {count} ACCOUNTS',
        'twitter_auth': 'Authenticating Twitter...',
        'twitter_auth_success': 'Twitter authentication successful!',
        'twitter_auth_failed': 'Twitter authentication failed',
        'logging_in': 'Logging in to Onvoyage...',
        'login_success': 'Login successful!',
        'login_failed': 'Login failed',
        'onboarding': 'Completing onboarding...',
        'onboard_success': 'Onboarding successful!',
        'onboard_skip': 'Already onboarded',
        'checking_in': 'Checking in...',
        'checkin_success': 'Check-in successful!',
        'checkin_failed': 'Check-in failed',
        'already_checkin': 'Already checked in today',
        'reward': 'Reward',
        'streak': 'Streak',
        'username': 'Username',
        'status': 'Status',
        'wallets': 'Wallets',
        'vpoints': 'VPoints',
        'vpoints_earned': 'VPoints Earned',
        'vpoints_spent': 'VPoints Spent',
        'success': '✅ Success',
        'failed': '❌ Failed',
        'error': 'Error',
        'using_proxy': 'Proxy',
        'no_proxy': 'No proxy',
        'completed': '✅ COMPLETED: {successful}/{total} ACCOUNTS SUCCESSFUL',
        'pausing': 'Pausing',
        'seconds': 'seconds',
        'account': 'Account',
        'public_ip': 'Public IP',
        'unknown': 'Unknown',
        'thog': 'Check-in has already happened today! Please do it tomorrow...',
    }
}

def print_border(text: str, color=Fore.CYAN, language='vi'):
    """In border với text giống bot.py"""
    width = BORDER_WIDTH
    if len(text) > width - 4:
        text = text[:width - 7] + "..."
    padded_text = f" {text} ".center(width - 2)
    print(f"{color}┌{'─' * (width - 2)}┐{Style.RESET_ALL}")
    print(f"{color}│{padded_text}│{Style.RESET_ALL}")
    print(f"{color}└{'─' * (width - 2)}┘{Style.RESET_ALL}")

def print_separator(color=Fore.MAGENTA):
    """In dấu phân cách giống bot.py"""
    print(f"{color}{'═' * BORDER_WIDTH}{Style.RESET_ALL}")

def print_message(text: str, color=Fore.WHITE, language='vi'):
    """In message với indent"""
    print(f"{color}  {text}{Style.RESET_ALL}")

def generate_fingerprint(account_index: int) -> dict:
    """Tạo unique browser fingerprint cho mỗi account"""
    seed = f"onvoyage_{account_index}_{time.time()}"
    hash_val = hashlib.md5(seed.encode()).hexdigest()
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    ]
    
    return {
        "user_agent": user_agents[int(hash_val[:2], 16) % len(user_agents)],
        "fp_hash": hash_val[:12]
    }

def generate_state() -> str:
    """Tạo random state cho OAuth2"""
    return f"v_{random.randint(10000000, 99999999)}"

def generate_random_username() -> str:
    """Tạo random username cho onboarding"""
    adjectives = ["happy", "cool", "swift", "brave", "bright", "calm", "eager"]
    nouns = ["traveler", "voyager", "explorer", "wanderer", "adventurer"]
    return f"{random.choice(adjectives)}{random.choice(nouns)}{random.randint(100, 9999)}"

INVITE_CODE = "v_98282504"

def load_accounts(filepath: str, language='vi') -> List[Dict]:
    """Load Twitter accounts từ file"""
    if not os.path.exists(filepath):
        print(f"{Fore.RED}  ❌ File {filepath} không tìm thấy!{Style.RESET_ALL}")
        return []
    
    accounts = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '|' in line:
                    parts = line.split('|')
                elif ':' in line:
                    parts = line.split(':')
                else:
                    continue
                
                if len(parts) >= 2:
                    accounts.append({
                        "auth_token": parts[0].strip(),
                        "ct0": parts[1].strip()
                    })
        
        if not accounts:
            print(f"{Fore.RED}  ❌ Không tìm thấy tài khoản hợp lệ trong {filepath}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}  ❌ Lỗi đọc file: {str(e)}{Style.RESET_ALL}")
    
    return accounts

def load_proxies(language='vi') -> List[str]:
    """Load proxies từ file"""
    if not os.path.exists('proxies.txt'):
        print(f"{Fore.YELLOW}  ℹ {LANG[language]['no_proxies']}{Style.RESET_ALL}")
        return []
    
    proxies = []
    with open('proxies.txt', 'r', encoding='utf-8') as f:
        for line in f:
            proxy = line.strip()
            if proxy and not proxy.startswith('#'):
                proxies.append(proxy)
    
    if proxies:
        print(f"{Fore.YELLOW}  ℹ {LANG[language]['found_proxies'].format(count=len(proxies))}{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}  ℹ {LANG[language]['no_proxies']}{Style.RESET_ALL}")
    
    return proxies

def parse_proxy(proxy: str) -> Optional[str]:
    """Parse proxy string thành URL format"""
    if not proxy:
        return None
    
    try:
        if '://' in proxy:
            return proxy
        
        parts = proxy.split(':')
        if len(parts) == 2:
            return f"http://{parts[0]}:{parts[1]}"
        elif len(parts) == 4:
            return f"http://{parts[2]}:{parts[3]}@{parts[0]}:{parts[1]}"
        
    except:
        pass
    
    return None

async def check_proxy_ip(session: aiohttp.ClientSession) -> str:
    """Check public IP của proxy"""
    try:
        async with session.get('https://api.ipify.org?format=json', timeout=10) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get('ip', 'Unknown')
    except:
        pass
    return 'Unknown'

class TwitterOAuth:
    def __init__(self, auth_token: str, ct0: str, fingerprint: dict, session: aiohttp.ClientSession):
        self.auth_token = auth_token
        self.ct0 = ct0
        self.fingerprint = fingerprint
        self.session = session
    
    def _get_headers(self, referer: str = None) -> dict:
        """Lấy headers cho Twitter request"""
        headers = {
            "User-Agent": self.fingerprint["user_agent"],
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "X-Csrf-Token": self.ct0,
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-client-language": "en",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
        }
        
        if referer:
            headers["Referer"] = referer
        
        return headers
    
    def _get_cookies(self) -> dict:
        """Lấy cookies cho Twitter request"""
        return {
            "auth_token": self.auth_token,
            "ct0": self.ct0,
        }
    
    async def get_authorization_code(self, state: str) -> Optional[str]:
        """Lấy OAuth authorization code từ Twitter"""
        auth_url = "https://twitter.com/i/api/2/oauth2/authorize"
        
        params = {
            "client_id": CLIENT_ID,
            "code_challenge": CODE_CHALLENGE,
            "code_challenge_method": CODE_CHALLENGE_METHOD,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": SCOPE,
            "state": state
        }
        
        referer = f"https://twitter.com/i/oauth2/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE.replace(' ', '%20')}&state={state}&code_challenge={CODE_CHALLENGE}&code_challenge_method={CODE_CHALLENGE_METHOD}"
        
        try:
            async with self.session.get(
                auth_url,
                params=params,
                headers=self._get_headers(referer),
                cookies=self._get_cookies(),
                timeout=CONFIG['TIMEOUT']
            ) as resp:
                if resp.status != 200:
                    return None
                
                data = await resp.json()
                auth_code = data.get("auth_code")
                
                if not auth_code:
                    return None
                
                return await self._approve_authorization(auth_code, state)
        except:
            return None
    
    async def _approve_authorization(self, auth_code: str, state: str) -> Optional[str]:
        """Approve OAuth authorization"""
        approve_url = "https://twitter.com/i/api/2/oauth2/authorize"
        
        referer = f"https://twitter.com/i/oauth2/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE.replace(' ', '%20')}&state={state}&code_challenge={CODE_CHALLENGE}&code_challenge_method={CODE_CHALLENGE_METHOD}"
        
        headers = self._get_headers(referer)
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        
        data = f"approval=true&code={auth_code}"
        
        try:
            async with self.session.post(
                approve_url,
                headers=headers,
                cookies=self._get_cookies(),
                data=data,
                timeout=CONFIG['TIMEOUT']
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    redirect_uri = result.get("redirect_uri", "")
                    
                    if redirect_uri:
                        parsed = urlparse(redirect_uri)
                        query_params = parse_qs(parsed.query)
                        if 'code' in query_params:
                            return query_params['code'][0]
        except:
            pass
        
        return None

class OnvoyageAPI:
    def __init__(self, fingerprint: dict, session: aiohttp.ClientSession):
        self.fingerprint = fingerprint
        self.session = session
        self.access_token = None
        self.user_info = None
    
    def _get_headers(self, with_auth: bool = False) -> dict:
        """Lấy headers cho Onvoyage request"""
        headers = {
            "User-Agent": self.fingerprint["user_agent"],
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://app.onvoyage.ai",
            "Referer": "https://app.onvoyage.ai/",
            "Content-Type": "application/json",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
        }
        
        if with_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        return headers
    
    async def login(self, twitter_code: str) -> bool:
        """Login vào Onvoyage bằng Twitter OAuth code"""
        login_url = f"{ONVOYAGE_BACKEND}/api/v1/auth/login"
        
        payload = {
            "provider": "twitter",
            "code": twitter_code,
            "redirect_uri": REDIRECT_URI
        }
        
        try:
            async with self.session.post(
                login_url,
                json=payload,
                headers=self._get_headers(),
                timeout=CONFIG['TIMEOUT']
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    
                    if result.get("code") == 0:
                        data = result.get("data", {})
                        self.access_token = data.get("access_token")
                        self.user_info = data.get("user_info", {})
                        return True
        except:
            pass
        
        return False
    
    async def onboard(self, invite_code: str = None) -> bool:
        """Hoàn thành onboarding"""
        if not self.access_token:
            return False
        
        onboard_url = f"{ONVOYAGE_BACKEND}/api/v1/auth/onboard"
        display_name = generate_random_username()
        
        payload = {"display_name": display_name}
        if invite_code:
            payload["invite_code"] = invite_code
        
        try:
            async with self.session.post(
                onboard_url,
                json=payload,
                headers=self._get_headers(with_auth=True),
                timeout=CONFIG['TIMEOUT']
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("code") == 0:
                        self.user_info["display_name"] = display_name
                        return True
        except:
            pass
        
        return False
    
    async def get_profile(self) -> Optional[dict]:
        """Lấy user profile"""
        if not self.access_token:
            return None
        
        profile_url = f"{ONVOYAGE_BACKEND}/api/v1/user/profile"
        
        try:
            async with self.session.get(
                profile_url,
                headers=self._get_headers(with_auth=True),
                timeout=CONFIG['TIMEOUT']
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("code") == 0:
                        return result.get("data")
        except:
            pass
        
        return None
    
    async def get_vpoints_balance(self) -> Optional[dict]:
        """Lấy VPoints balance"""
        if not self.access_token:
            return None
        
        vpoints_url = f"{ONVOYAGE_BACKEND}/api/v1/points/balance"
        
        try:
            async with self.session.get(
                vpoints_url,
                headers=self._get_headers(with_auth=True),
                timeout=CONFIG['TIMEOUT']
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("code") == 0:
                        return result.get("data")
        except:
            pass
        
        return None
    
    async def checkin(self) -> Optional[dict]:
        """Daily check-in"""
        if not self.access_token:
            return None
        
        checkin_url = f"{ONVOYAGE_BACKEND}/api/v1/task/checkin"
        
        try:
            async with self.session.post(
                checkin_url,
                headers=self._get_headers(with_auth=True),
                timeout=CONFIG['TIMEOUT']
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("code") == 0:
                        return result.get("data", {})
        except:
            pass
        
        return None

async def process_account(account: dict, account_index: int, proxy: Optional[str], language: str) -> bool:
    """Xử lý 1 account"""
    auth_token = account['auth_token']
    ct0 = account['ct0']
    
    fingerprint = generate_fingerprint(account_index)
    
    print(f"{Fore.MAGENTA}{'─' * BORDER_WIDTH}{Style.RESET_ALL}")
    print()
    print(f"{Fore.CYAN}  Tài khoản #{account_index + 1} (FP: {fingerprint['fp_hash']}){Style.RESET_ALL}")
    print()
    
    connector = None
    if proxy:
        proxy_url = parse_proxy(proxy)
        if proxy_url:
            connector = ProxyConnector.from_url(proxy_url)
    
    timeout = aiohttp.ClientTimeout(total=CONFIG['TIMEOUT'])
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        if proxy:
            public_ip = await check_proxy_ip(session)
            print(f"{Fore.CYAN}  🔄 Proxy: {proxy} | IP công khai: {public_ip}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}  > {LANG[language]['twitter_auth']}{Style.RESET_ALL}")
        
        twitter_oauth = TwitterOAuth(auth_token, ct0, fingerprint, session)
        state = generate_state()
        twitter_code = await twitter_oauth.get_authorization_code(state)
        
        if not twitter_code:
            print(f"{Fore.RED}  ✖ {LANG[language]['twitter_auth_failed']}{Style.RESET_ALL}")
            return False
        
        print(f"{Fore.GREEN}  ✓ {LANG[language]['twitter_auth_success']}{Style.RESET_ALL}")
        await asyncio.sleep(random.uniform(0.5, 1))
        
        print(f"{Fore.CYAN}  > {LANG[language]['logging_in']}{Style.RESET_ALL}")
        
        onvoyage_api = OnvoyageAPI(fingerprint, session)
        login_success = await onvoyage_api.login(twitter_code)
        
        if not login_success:
            print(f"{Fore.RED}  ✖ {LANG[language]['login_failed']}{Style.RESET_ALL}")
            return False
        
        print(f"{Fore.GREEN}  ✓ {LANG[language]['login_success']}{Style.RESET_ALL}")
        await asyncio.sleep(random.uniform(0.5, 1))
        
        print(f"{Fore.CYAN}  > {LANG[language]['onboarding']}{Style.RESET_ALL}")
        
        onboard_success = await onvoyage_api.onboard(INVITE_CODE)
        
        if onboard_success:
            print(f"{Fore.GREEN}  ✓ {LANG[language]['onboard_success']}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}  - {LANG[language]['onboard_skip']}{Style.RESET_ALL}")
        
        await asyncio.sleep(random.uniform(0.5, 1))
        
        print(f"{Fore.CYAN}  > {LANG[language]['checking_in']}{Style.RESET_ALL}")
        
        checkin_data = await onvoyage_api.checkin()
        
        if checkin_data:
            reward = checkin_data.get('reward', 0)
            streak = checkin_data.get('streak_days', 0)
            print(f"{Fore.GREEN}  ✓ {LANG[language]['checkin_success']}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}  - {LANG[language]['reward']}: +{reward} | {LANG[language]['streak']}: {streak} days{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}  - {LANG[language]['thog']}{Style.RESET_ALL}")
        
        profile = await onvoyage_api.get_profile()
        if profile:
            username = profile.get('display_name') or profile.get('username', 'Unknown')
            status = profile.get('status', 'active')
            wallets = profile.get('wallets', [])
            
            print()
            print(f"{Fore.YELLOW}  - {LANG[language]['username']}: {username}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}  - {LANG[language]['status']}: {status}{Style.RESET_ALL}")
            
            vpoints_data = await onvoyage_api.get_vpoints_balance()
            if vpoints_data:
                vpoints_balance = vpoints_data.get('balance', 0)
                vpoints_earned = vpoints_data.get('total_earned', 0)
                vpoints_spent = vpoints_data.get('total_spent', 0)
                print(f"{Fore.YELLOW}  - {LANG[language]['vpoints']}: {vpoints_balance} | {LANG[language]['vpoints_earned']}: {vpoints_earned} | {LANG[language]['vpoints_spent']}: {vpoints_spent}{Style.RESET_ALL}")
            
            if wallets:
                wallet_strs = []
                for w in wallets:
                    chain = w.get('chain', '').title()
                    addr = w.get('address', '')
                    if addr:
                        wallet_strs.append(f"{chain}: {addr[:8]}***{addr[-6:]}")
                if wallet_strs:
                    print(f"{Fore.YELLOW}  - {LANG[language]['wallets']}: {' | '.join(wallet_strs)}{Style.RESET_ALL}")
        
        print()
        print(f"{Fore.GREEN}  ✅ {LANG[language]['success']}{Style.RESET_ALL}")
        print()
        
        return True

async def run_checkinX(language: str = 'vi'):
    """Main function"""
    print()
    print_border(LANG[language]['title'], Fore.CYAN, language)
    print()
    
    proxies = load_proxies(language)
    print()
    
    accounts = load_accounts('tokenX.txt', language)
    print(f"{Fore.YELLOW}  ℹ {LANG[language]['found_accounts'].format(count=len(accounts))}{Style.RESET_ALL}")
    print()
    
    if not accounts:
        return
    
    print_separator()
    print_border(LANG[language]['processing'].format(count=len(accounts)), Fore.MAGENTA, language)
    print()
    
    successful = 0
    total = len(accounts)
    
    semaphore = asyncio.Semaphore(CONFIG['THREADS'])
    
    async def process_with_semaphore(idx, acc):
        nonlocal successful
        async with semaphore:
            proxy = proxies[idx % len(proxies)] if proxies else None
            success = await process_account(acc, idx, proxy, language)
            if success:
                successful += 1
            
            if idx < total - 1:
                delay = CONFIG['DELAY_BETWEEN_ACCOUNTS']
                print_message(f"{LANG[language]['pausing']} {delay} {LANG[language]['seconds']}...", Fore.YELLOW, language)
                await asyncio.sleep(delay)
    
    tasks = [process_with_semaphore(i, acc) for i, acc in enumerate(accounts)]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    print()
    print_border(LANG[language]['completed'].format(successful=successful, total=total), Fore.GREEN, language)
    print()

if __name__ == "__main__":
    asyncio.run(run_checkinX('vi'))
