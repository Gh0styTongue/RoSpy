# RoSpy 🕵️‍♂️

> An intelligence tool for Roblox event hunters. RoSpy performs high-speed reconnaissance on pre-event games and test hubs, logging every join and fetching avatars to help discover participating developers and other key logistics before an event officially begins.

### Key Features

* **Real-Time Monitoring**: Uses high-speed asynchronous requests to monitor game servers with minimal delay.
* **Session Tracking**: Logs player joins, rejoins, and calculates the duration of each play session.
* **Avatar Fetching**: Automatically downloads the avatar thumbnail of every unique player the first time they are seen.
* **Intelligent Rate-Limit Handling**: Pauses automatically when the Roblox API rate limit is hit and resumes when it's safe.
* **Persistent Logging**: Saves a detailed, timestamped log of all events to `roblox_event_log.txt` so no data is lost.
* **Simple GUI**: Easy-to-use graphical interface built with Tkinter.

### Primary Use Case

`RoSpy` is designed for the Roblox event community. Its primary purpose is to monitor private or soon-to-be-public event games (like test hubs) before they are officially announced. By tracking who joins, you can:

* Identify developers, influencers, and Roblox admins who are involved in an event.
* Gather intelligence on the scale and participants of an upcoming event.
* Get a head start on event news and logistics.

---

### Requirements

* Python 3.7+
* `aiohttp`

### Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Gh0styTongue/RoSpy.git
   cd RoSpy
   ```

2. **Install the required library:**
   ```bash
   pip install aiohttp
   ```
   *(Note: Tkinter is included with most standard Python installations.)*

3. **Run the script:**
   ```bash
   python main.py 
   ```
   *(Assuming you've named your script `main.py` or similar)*

4. **Using the Application:**
   * Enter the **Place ID** of the Roblox game you want to monitor into the input field.
   * Click **"Start Tracking"**.
   * The application will begin logging events in the GUI and to the log file.
   * Click **"Stop Tracking"** to gracefully end the monitoring session.

### Output

The script will generate the following in its directory:

* `thumbnails/`: A folder containing all the downloaded player avatar images, named by their unique player token.
* `roblox_event_log.txt`: A text file containing a complete, timestamped log of all activity (joins, rejoins, leaves, errors, etc.).

### Contributing

Contributions are welcome! If you have ideas for new features or improvements, feel free to open an issue or submit a pull request.

### License

This project is licensed under the MIT License. See the `LICENSE` file for details.
