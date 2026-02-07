import os
import asyncio
import aiohttp
import random
import hashlib
import time
from typing import List, Optional, Dict
from aiohttp_socks import ProxyConnector
from colorama import init, Fore, Style
from datetime import datetime

init(autoreset=True)


BORDER_WIDTH = 80

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
        'title': 'ONVOYAGE AUTO CHECK-IN - TOKEN LOGIN',
        'loading_tokens': 'Đang tải access tokens...',
        'found_tokens': 'Tìm thấy {count} tokens',
        'loading_proxies': 'Đang tải proxy...',
        'found_proxies': 'Tìm thấy {count} proxy',
        'no_proxies': 'Không tìm thấy proxy, chạy không proxy',
        'processing': '⚙ ĐANG XỬ LÝ {count} TÀI KHOẢN',
        'getting_profile': 'Đang lấy thông tin profile...',
        'profile_success': 'Lấy thông tin thành công!',
        'profile_failed': 'Lấy thông tin thất bại',
        'checking_in': 'Đang check-in...',
        'checkin_success': 'Check-in thành công!',
        'checkin_failed': 'Check-in thất bại',
        'already_checkin': 'Đã check-in hôm nay',
        'reward': 'Phần thưởng',
        'streak': 'Chuỗi ngày',
        'username': 'Tên người dùng',
        'status': 'Trạng thái',
        'wallets': 'Ví',
        'user_id': 'User ID',
        'balance': 'Số dư',
        'total_earnings': 'Tổng kiếm được',
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
        'token': 'Token',
        'public_ip': 'IP công khai',
        'unknown': 'Không xác định',
        'invalid_token': 'Token không hợp lệ hoặc hết hạn',
        'thog': 'Đã check-in hôm nay rồi! Vui lòng thực hiện vào ngày mai...',
    },
    'en': {
        'title': 'ONVOYAGE AUTO CHECK-IN - TOKEN LOGIN',
        'loading_tokens': 'Loading access tokens...',
        'found_tokens': 'Found {count} tokens',
        'loading_proxies': 'Loading proxies...',
        'found_proxies': 'Found {count} proxies',
        'no_proxies': 'No proxies found, running without proxy',
        'processing': '⚙ PROCESSING {count} ACCOUNTS',
        'getting_profile': 'Getting profile info...',
        'profile_success': 'Profile info retrieved!',
        'profile_failed': 'Failed to get profile',
        'checking_in': 'Checking in...',
        'checkin_success': 'Check-in successful!',
        'checkin_failed': 'Check-in failed',
        'already_checkin': 'Already checked in today',
        'reward': 'Reward',
        'streak': 'Streak',
        'username': 'Username',
        'status': 'Status',
        'wallets': 'Wallets',
        'user_id': 'User ID',
        'balance': 'Balance',
        'total_earnings': 'Total Earnings',
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
        'token': 'Token',
        'public_ip': 'Public IP',
        'unknown': 'Unknown',
        'invalid_token': 'Invalid or expired token',
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
    seed = f"onvoyage_token_{account_index}_{time.time()}"
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

def load_tokens(filepath: str, language='vi') -> List[str]:
    """Load access tokens từ file"""
    if not os.path.exists(filepath):
        print(f"{Fore.RED}  ❌ File {filepath} không tìm thấy!{Style.RESET_ALL}")
        return []
    
    tokens = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    tokens.append(line)
        
        if not tokens:
            print(f"{Fore.RED}  ❌ Không tìm thấy token hợp lệ trong {filepath}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}  ❌ Lỗi đọc file: {str(e)}{Style.RESET_ALL}")
    
    return tokens

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

class OnvoyageAPI:
    def __init__(self, access_token: str, fingerprint: dict, session: aiohttp.ClientSession):
        self.access_token = access_token
        self.fingerprint = fingerprint
        self.session = session
    
    def _get_headers(self) -> dict:
        """Lấy headers cho Onvoyage request"""
        return {
            "User-Agent": self.fingerprint["user_agent"],
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://app.onvoyage.ai",
            "Referer": "https://app.onvoyage.ai/",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
        }
    
    async def get_profile(self) -> Optional[dict]:
        """Lấy user profile"""
        profile_url = f"{ONVOYAGE_BACKEND}/api/v1/user/profile"
        
        try:
            async with self.session.get(
                profile_url,
                headers=self._get_headers(),
                timeout=CONFIG['TIMEOUT']
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("code") == 0:
                        return result.get("data")
                elif resp.status == 401:
                    return {"error": "unauthorized"}
        except:
            pass
        
        return None
    
    async def get_balance(self) -> Optional[dict]:
        """Lấy wallet balance"""
        balance_url = f"{ONVOYAGE_BACKEND}/api/v1/wallet/balance"
        
        try:
            async with self.session.get(
                balance_url,
                headers=self._get_headers(),
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
        vpoints_url = f"{ONVOYAGE_BACKEND}/api/v1/points/balance"
        
        try:
            async with self.session.get(
                vpoints_url,
                headers=self._get_headers(),
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
        checkin_url = f"{ONVOYAGE_BACKEND}/api/v1/task/checkin"
        
        try:
            async with self.session.post(
                checkin_url,
                headers=self._get_headers(),
                timeout=CONFIG['TIMEOUT']
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("code") == 0:
                        return result.get("data", {})
        except:
            pass
        
        return None
    
    async def get_checkin_status(self) -> Optional[dict]:
        """Kiểm tra checkin status"""
        status_url = f"{ONVOYAGE_BACKEND}/api/v1/task/checkin/status"
        
        try:
            async with self.session.get(
                status_url,
                headers=self._get_headers(),
                timeout=CONFIG['TIMEOUT']
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get("code") == 0:
                        return result.get("data")
        except:
            pass
        
        return None

async def process_account(access_token: str, account_index: int, proxy: Optional[str], language: str) -> bool:
    """Xử lý 1 account"""
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
        
        api = OnvoyageAPI(access_token, fingerprint, session)
        
        print(f"{Fore.CYAN}  > {LANG[language]['getting_profile']}{Style.RESET_ALL}")
        
        profile = await api.get_profile()
        
        if not profile:
            print(f"{Fore.RED}  ✖ {LANG[language]['profile_failed']}{Style.RESET_ALL}")
            return False
        
        if profile.get("error") == "unauthorized":
            print(f"{Fore.RED}  ✖ {LANG[language]['invalid_token']}{Style.RESET_ALL}")
            return False
        
        print(f"{Fore.GREEN}  ✓ {LANG[language]['profile_success']}{Style.RESET_ALL}")
        
        username = profile.get('display_name') or profile.get('username', 'Unknown')
        user_id = profile.get('id', 'Unknown')
        status = profile.get('status', 'active')
        
        print(f"{Fore.YELLOW}  - {LANG[language]['user_id']}: {user_id}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  - {LANG[language]['username']}: {username}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  - {LANG[language]['status']}: {status}{Style.RESET_ALL}")
        
        balance_data = await api.get_balance()
        if balance_data:
            available = balance_data.get('available_balance', 0)
            total = balance_data.get('total_earnings', 0)
            print(f"{Fore.YELLOW}  - {LANG[language]['balance']}: {available} | {LANG[language]['total_earnings']}: {total}{Style.RESET_ALL}")
        
        vpoints_data = await api.get_vpoints_balance()
        if vpoints_data:
            vpoints_balance = vpoints_data.get('balance', 0)
            vpoints_earned = vpoints_data.get('total_earned', 0)
            vpoints_spent = vpoints_data.get('total_spent', 0)
            print(f"{Fore.YELLOW}  - {LANG[language]['vpoints']}: {vpoints_balance} | {LANG[language]['vpoints_earned']}: {vpoints_earned} | {LANG[language]['vpoints_spent']}: {vpoints_spent}{Style.RESET_ALL}")
        
        wallets = profile.get('wallets', [])
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
        
        print(f"{Fore.CYAN}  > {LANG[language]['checking_in']}{Style.RESET_ALL}")
        
        checkin_data = await api.checkin()
        
        if checkin_data:
            reward = checkin_data.get('reward', 0)
            streak = checkin_data.get('streak_days', 0)
            print(f"{Fore.GREEN}  ✓ {LANG[language]['checkin_success']}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}  - {LANG[language]['reward']}: +{reward} | {LANG[language]['streak']}: {streak} days{Style.RESET_ALL}")
        else:
            checkin_status = await api.get_checkin_status()
            if checkin_status and checkin_status.get('checked_in'):
                print(f"{Fore.YELLOW}  - {LANG[language]['thog']}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}  ✖ {LANG[language]['checkin_failed']}{Style.RESET_ALL}")
        
        print()
        print(f"{Fore.GREEN}  ✅ {LANG[language]['success']}{Style.RESET_ALL}")
        print()
        
        return True

async def run_checkintoken(language: str = 'vi'):
    """Main function"""
    print()
    print_border(LANG[language]['title'], Fore.CYAN, language)
    print()
    
    proxies = load_proxies(language)
    print()
    
    tokens = load_tokens('token.txt', language)
    print(f"{Fore.YELLOW}  ℹ {LANG[language]['found_tokens'].format(count=len(tokens))}{Style.RESET_ALL}")
    print()
    
    if not tokens:
        return
    
    print_separator()
    print_border(LANG[language]['processing'].format(count=len(tokens)), Fore.MAGENTA, language)
    print()
    
    successful = 0
    total = len(tokens)
    
    semaphore = asyncio.Semaphore(CONFIG['THREADS'])
    
    async def process_with_semaphore(idx, token):
        nonlocal successful
        async with semaphore:
            proxy = proxies[idx % len(proxies)] if proxies else None
            success = await process_account(token, idx, proxy, language)
            if success:
                successful += 1
            
            if idx < total - 1:
                delay = CONFIG['DELAY_BETWEEN_ACCOUNTS']
                print_message(f"{LANG[language]['pausing']} {delay} {LANG[language]['seconds']}...", Fore.YELLOW, language)
                await asyncio.sleep(delay)
    
    tasks = [process_with_semaphore(i, token) for i, token in enumerate(tokens)]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    print()
    print_border(LANG[language]['completed'].format(successful=successful, total=total), Fore.GREEN, language)
    print()

if __name__ == "__main__":
    asyncio.run(run_checkintoken('vi'))
