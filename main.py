import tkinter as tk
from tkinter import ttk, scrolledtext
import asyncio
import aiohttp
import threading
import time
import json
import os
import math

class RobloxDevTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("RoSpy")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TFrame", background="#2e2e2e")
        self.style.configure("TLabel", background="#2e2e2e", foreground="#f0f0f0", font=("Arial", 10))
        self.style.configure("TButton", background="#4a4a4a", foreground="#f0f0f0", font=("Arial", 10, "bold"))
        self.style.map("TButton", background=[('active', '#6a6a6a')])
        self.style.configure("TEntry", fieldbackground="#4a4a4a", foreground="#f0f0f0", insertbackground="#f0f0f0")

        self.tracking_thread = None
        self.is_tracking = False
        self.player_data = {}
        self.log_filename = "roblox_event_log.txt"
        self.loop = None

        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill=tk.X, pady=5)

        ttk.Label(input_frame, text="Place ID:").pack(side=tk.LEFT, padx=(0, 5))
        self.place_id_entry = ttk.Entry(input_frame, width=40)
        self.place_id_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=10)

        self.start_button = ttk.Button(control_frame, text="Start Tracking", command=self.start_tracking)
        self.start_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        self.stop_button = ttk.Button(control_frame, text="Stop Tracking", command=self.stop_tracking, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        log_frame = ttk.Frame(self.main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(log_frame, text="Log:").pack(anchor="w")
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled',
                                                   bg="#1e1e1e", fg="#d4d4d4", font=("Courier New", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=(5,0))

    def log(self, message):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"{timestamp} - {message}\n"
        
        try:
            with open(self.log_filename, 'a', encoding='utf-8') as f:
                f.write(log_line)
        except Exception as e:
            print(f"Failed to write to log file: {e}")
            
        self.root.after(0, self._log_update, message)

    def _log_update(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_area.config(state='disabled')
        self.log_area.yview(tk.END)

    def start_tracking(self):
        place_id = self.place_id_entry.get().strip()
        if not place_id.isdigit():
            self.log("Error: Place ID must be numeric.")
            return

        self.is_tracking = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log(f"Starting tracking for Place ID: {place_id}")
        
        self.player_data.clear()

        self.tracking_thread = threading.Thread(target=self._start_async_tracking, args=(place_id,), daemon=True)
        self.tracking_thread.start()

    def _start_async_tracking(self, place_id):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.track_players_loop(place_id))
        finally:
            self.loop.close()

    def stop_tracking(self):
        if self.is_tracking:
            self.is_tracking = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.log("Tracking stopped by user.")

    def format_duration(self, seconds):
        if seconds < 0:
            return "0s"
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{math.floor(hours)}h")
        if minutes > 0:
            parts.append(f"{math.floor(minutes)}m")
        if seconds > 0 or not parts:
            parts.append(f"{math.floor(seconds)}s")
        
        return " ".join(parts)

    async def track_players_loop(self, place_id):
        async with aiohttp.ClientSession() as session:
            while self.is_tracking:
                try:
                    url = f"https://games.roblox.com/v1/games/{place_id}/servers/Public?sortOrder=Desc&excludeFullGames=false&limit=100"
                    
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                        if response.status == 429:
                            self.log("Rate limited by API (429). Waiting 15 seconds...")
                            await asyncio.sleep(15)
                            continue

                        response.raise_for_status()
                        data = await response.json()

                        errors = data.get("errors")
                        if isinstance(errors, list) and errors:
                            if errors[0].get("message") == "Too many requests":
                                self.log("Rate limited by API (message). Waiting 15 seconds...")
                                await asyncio.sleep(15)
                                continue
                        
                        servers = data.get('data', [])
                        
                        current_tokens = set()
                        if servers:
                             self.log(f"Found {len(servers)} server(s). Processing players...")
                        for server in servers:
                            for token in server.get('playerTokens', []):
                                current_tokens.add(token)

                        scan_time = time.time()
                        thumbnail_tasks = []

                        for token in current_tokens:
                            if token not in self.player_data:
                                self.player_data[token] = {
                                    'join_count': 1,
                                    'session_start_time': scan_time,
                                    'is_currently_in_game': True,
                                    'image_saved': False
                                }
                                self.log(f"New player found: {token[:20]}... (Join #{self.player_data[token]['join_count']})")
                                thumbnail_tasks.append(self.fetch_thumbnail(session, token))
                            else:
                                player = self.player_data[token]
                                if not player['is_currently_in_game']:
                                    player['join_count'] += 1
                                    player['session_start_time'] = scan_time
                                    self.log(f"Player rejoined: {token[:20]}... (Join #{player['join_count']})")
                                player['is_currently_in_game'] = True

                        if thumbnail_tasks:
                            await asyncio.gather(*thumbnail_tasks)

                        for token, data in list(self.player_data.items()):
                            if data['is_currently_in_game'] and token not in current_tokens:
                                duration = scan_time - data['session_start_time']
                                self.log(f"Player left: {token[:20]}... (Session: {self.format_duration(duration)}, Total Joins: {data['join_count']})")
                                data['is_currently_in_game'] = False

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    self.log(f"Network error fetching servers: {e}")
                    await asyncio.sleep(5)
                except json.JSONDecodeError:
                    self.log("Error: Failed to decode JSON from game servers API.")
                except Exception as e:
                    self.log(f"An unexpected error occurred in main loop: {e}")
            
        self.log("Tracking loop has ended.")

    async def fetch_thumbnail(self, session, token):
        if self.player_data.get(token, {}).get('image_saved'):
            return

        self.log(f"Requesting thumbnail for {token[:20]}...")
        try:
            url = "https://thumbnails.roblox.com/v1/batch"
            payload = [{"requestId": f"0:{token}:AvatarHeadshot:150x150:webp:regular:0", "type": "AvatarHeadShot", "targetId": 0, "token": token, "format": "png", "size": "150x150"}]
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as response:
                response.raise_for_status()
                thumbnail_data = await response.json()
                
                data_list = thumbnail_data.get('data', [])
                if data_list and data_list[0].get('state') == 'Completed':
                    image_url = data_list[0].get('imageUrl')
                    if image_url:
                        self.log(f"Successfully fetched thumbnail URL for {token[:20]}...")
                        await self.save_image(session, image_url, token)
                elif data_list:
                    self.log(f"Thumbnail request state for {token[:20]}...: {data_list[0].get('state', 'Unknown')}")
                else:
                    self.log(f"Thumbnail request returned no data for {token[:20]}...")

        except Exception as e:
            self.log(f"Error during thumbnail fetch for {token[:20]}...: {e}")

    async def save_image(self, session, image_url, token):
        try:
            if not os.path.exists('thumbnails'):
                os.makedirs('thumbnails')
                self.log("Created 'thumbnails' directory.")

            filepath = os.path.join('thumbnails', f'{token}.png')
            
            async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=20)) as image_response:
                image_response.raise_for_status()

                with open(filepath, 'wb') as f:
                    while True:
                        chunk = await image_response.content.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
            
            self.log(f"Image successfully saved: {filepath}")
            if token in self.player_data:
                self.player_data[token]['image_saved'] = True

        except Exception as e:
            self.log(f"Error during image save for {token[:20]}...: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = RobloxDevTracker(root)
    root.mainloop()
