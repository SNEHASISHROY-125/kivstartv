from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from create_db import insert_channels
from fastapi import File, UploadFile
from urllib.parse import unquote
import sqlite3,configparser
import os,json,uvicorn,re
from typing import List

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# app .conf
config = configparser.ConfigParser()
config.read('app.conf')
# DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'iptv_channels.db'))
DB_PATH = config['app']['channels_db_path']

# --- Database helpers ---
def get_channels():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT * FROM channels')
    channels = cur.fetchall()
    conn.close()
    return channels

def add_channel(tvg_id, name, stream_url, logo_url):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO channels (tvg_id, name, logo_url, stream_url) VALUES (?, ?, ?, ?)', (tvg_id, name, logo_url, stream_url))
    conn.commit()
    conn.close()

def update_channel(ch_id, tvg_id, name, stream_url, logo_url):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE channels SET tvg_id=?, name=?, logo_url=?, stream_url=? WHERE id=?', (tvg_id, name, logo_url, stream_url, ch_id))
    conn.commit()
    conn.close()

def delete_channel(ch_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('DELETE FROM channels WHERE id=?', (ch_id,))
    conn.commit()
    conn.close()

# --- WebSocket manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- API endpoints ---
@app.get("/api/channels")
def api_get_channels():
    channels = get_channels()
    return {"channels": channels}

@app.post("/channels")
def api_add_channel(tvg_id: str = Form(""), name: str = Form(...), stream_url: str = Form(...), logo_url: str = Form("")):
    add_channel(tvg_id, name, stream_url, logo_url)
    return {"status": "ok"}

@app.post("/channels/{ch_id}")
def api_update_channel(ch_id: int, tvg_id: str = Form(""), name: str = Form(...), stream_url: str = Form(...), logo_url: str = Form("")):
    update_channel(ch_id, tvg_id, name, stream_url, logo_url)
    return {"status": "ok"}

@app.delete("/channels/{ch_id}")
def api_delete_channel(ch_id: int):
    delete_channel(ch_id)
    return {"status": "ok"}

@app.post("/channels_upload")
async def api_upload_m3u8(file: UploadFile = File(...)):
    def parse_m3u(file_content):
        channels = []
        current_channel = None
        current_options = []
        for line in file_content.splitlines():
            line = line.strip()
            if not line or line.startswith('#EXTM3U'):
                continue
            if line.startswith('#EXTINF'):
                match = re.match(r'#EXTINF:-?\d+\s*(.*?),(.*)', line)
                if match:
                    attrs = match.group(1)
                    name = unquote(match.group(2)).strip()
                    tvg_id = re.search(r'tvg-id="([^"]+)"', attrs)
                    logo = re.search(r'tvg-logo="([^"]+)"', attrs)
                    groups = re.search(r'group-title="([^"]+)"', attrs)
                    current_channel = {
                        'tvg_id': tvg_id.group(1) if tvg_id else None,
                        'name': name,
                        'logo': unquote(logo.group(1)) if logo else None,
                        'groups': [g.strip() for g in groups.group(1).split(';')] if groups else [],
                        'url': None,
                        'options': []
                    }
            elif line.startswith('#EXTVLCOPT:'):
                option = line[len('#EXTVLCOPT:'):].strip()
                current_options.append(option)
            elif line and not line.startswith('#'):
                if current_channel:
                    current_channel['url'] = unquote(line)
                    current_channel['options'] = current_options.copy()
                    channels.append(current_channel)
                    current_channel = None
                    current_options.clear()
        return channels

    if not file:
        print("No file received!")
        return {"status": "error", "detail": "No file uploaded"}
    print(f"Received file: {file.filename}, content_type: {file.content_type}")
    content = (await file.read()).decode('utf-8')
    channels = parse_m3u(content)
    # Do not insert into DB yet, just return parsed channels for preview/edit
    return {"status": "ok", "channels": channels, "detail": "File parsed successfully"}

# --- WebSocket endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # For now, just broadcast the full channel list on any message
            channels = get_channels()
            await manager.broadcast(json.dumps({"channels": channels}))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- Serve frontend ---
FRONTEND_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>IPTV Channel Manager (FastAPI)</title>
    <style>
        table, th, td { border: 1px solid black; border-collapse: collapse; padding: 5px; }
        th { background: #eee; }
        img { max-height: 40px; }
        .truncate { max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: inline-block; vertical-align: middle; }
        .edit-btn, .save-btn, .cancel-btn { margin-left: 5px; }
        #spinner {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(255,255,255,0.7);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        #spinner .loader {
            border: 8px solid #f3f3f3;
            border-top: 8px solid #3498db;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div id="spinner"><div class="loader"></div></div>
    <h1>IPTV Channel Manager (FastAPI)</h1>
    <input type="text" id="filterInput" placeholder="Filter channels by name, tvg_id, or URL..." style="margin-bottom:10px;width:350px;">
    <div style="max-height: 600px; overflow-y: auto;" id="tableContainer">
    <table id="channels">
        <thead><tr><th>ID</th><th>tvg_id</th><th>Logo</th><th>Name</th><th>Stream URL</th><th>Actions</th></tr></thead>
        <tbody></tbody>
    </table>
    </div>
    <h2>Add Channel</h2>
    <form id="addForm">
        tvg_id: <input name="tvg_id"> Name: <input name="name" required> Stream URL: <input name="stream_url" required> Logo URL: <input name="logo_url">
        <button type="submit">Add</button>
    </form>
    <h2>Add Channels from m3u8</h2>
    <form id="uploadForm" enctype="multipart/form-data">
        <input type="file" name="file" accept=".m3u8" required>
        <button type="submit">Upload</button>
    </form>
    <div id="m3uPreviewSection" style="display:none; margin-top:20px;">
        <h2>Preview/Edit Uploaded Channels</h2>
        <div style="display: flex; align-items: flex-start; gap: 30px;">
            <table id="m3uPreviewTable">
                <thead><tr><th>Name</th><th>Logo</th><th>Group</th><th>Stream URL</th><th>Preview</th><th>Keep</th></tr></thead>
                <tbody></tbody>
            </table>
            <div style="min-width:420px;">
                <video id="m3uPreviewPlayer" controls width="400" style="display:none;"></video>
            </div>
        </div>
        <button id="saveM3uChannelsBtn" style="margin-top:10px;">Save Selected Channels</button>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <script>
    let editingId = null;
    let allChannels = [];
    let filteredChannels = [];
    let renderedCount = 0;
    const PAGE_SIZE = 50;
    let loading = false;
    let m3uChannels = [];
    let m3uKeep = [];
    function showSpinner(show) {
        document.getElementById('spinner').style.display = show ? 'flex' : 'none';
    }
    function truncateUrl(url) {
        if (!url) return '';
        return url.length > 30 ? url.slice(0, 30) + '...' : url;
    }
    function filterChannels(channels, filter) {
        if (!filter) return channels;
        filter = filter.toLowerCase();
        return channels.filter(ch =>
            (ch[1] && ch[1].toLowerCase().includes(filter)) || // tvg_id
            (ch[2] && ch[2].toLowerCase().includes(filter)) || // name
            (ch[3] && ch[3].toLowerCase().includes(filter)) || // logo_url
            (ch[4] && ch[4].toLowerCase().includes(filter))    // stream_url
        );
    }
    async function loadChannels() {
        showSpinner(true);
        let resp = await fetch('/api/channels');
        let data = await resp.json();
        allChannels = data.channels;
        applyFilterAndRender(true);
        showSpinner(false);
    }
    function applyFilterAndRender(reset) {
        let filter = document.getElementById('filterInput').value;
        filteredChannels = filterChannels(allChannels, filter);
        renderedCount = reset ? 0 : renderedCount;
        renderChannels(true);
    }
    function renderChannels(reset) {
        let tbody = document.querySelector('#channels tbody');
        if (reset) {
            tbody.innerHTML = '';
            renderedCount = 0;
        }
        let toRender = filteredChannels.slice(renderedCount, renderedCount + PAGE_SIZE);
        for (let ch of toRender) {
            let row = document.createElement('tr');
            if (editingId === ch[0]) {
                row.innerHTML = `
                <td>${ch[0]}</td>
                <td><input value="${ch[1] || ''}" id="edit-tvgid"></td>
                <td><input value="${ch[3] || ''}" id="edit-logo"></td>
                <td><input value="${ch[2] || ''}" id="edit-name"></td>
                <td><input value="${ch[4] || ''}" id="edit-url" style="width:220px"></td>
                <td>
                    <button class="save-btn" onclick="saveEdit(${ch[0]})">Save</button>
                    <button class="cancel-btn" onclick="cancelEdit()">Cancel</button>
                    <button class="delete-btn" onclick="deleteChannel(${ch[0]})" style="color:red;">Delete</button>
                </td>`;
            } else {
                row.innerHTML = `
                <td>${ch[0]}</td>
                <td>${ch[1] || ''}</td>
                <td>${ch[3] ? `<img src='${ch[3]}'/>` : ''}</td>
                <td>${ch[2]}</td>
                <td><span class="truncate" title="${ch[4] || ''}">${truncateUrl(ch[4])}</span></td>
                <td><button class="edit-btn" onclick="startEdit(${ch[0]})">Edit</button></td>`;
            }
            tbody.appendChild(row);
        }
        renderedCount += toRender.length;
    }
    function renderM3uPreview() {
        const section = document.getElementById('m3uPreviewSection');
        const table = document.getElementById('m3uPreviewTable').getElementsByTagName('tbody')[0];
        table.innerHTML = '';
        m3uChannels.forEach((ch, idx) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><input value="${ch.name || ''}" onchange="window.m3uEditName(${idx}, this.value)"></td>
                <td>${ch.logo ? `<img src='${ch.logo}' style='max-height:30px;'/>` : ''}</td>
                <td>${ch.groups && ch.groups.length ? ch.groups.join(', ') : ''}</td>
                <td><input value="${ch.url || ''}" style="width:220px" onchange="window.m3uEditUrl(${idx}, this.value)"></td>
                <td><button onclick="window.m3uPreviewStream('${ch.url || ''}')">Preview</button></td>
                <td><input type="checkbox" ${m3uKeep[idx] ? 'checked' : ''} onchange="window.m3uToggleKeep(${idx}, this.checked)"></td>
            `;
            table.appendChild(row);
        });
        section.style.display = m3uChannels.length ? '' : 'none';
    }
    function onScroll() {
        let container = document.getElementById('tableContainer');
        if (container.scrollTop + container.clientHeight >= container.scrollHeight - 10) {
            if (renderedCount < filteredChannels.length && !loading) {
                loading = true;
                showSpinner(true);
                setTimeout(() => {
                    renderChannels(false);
                    showSpinner(false);
                    loading = false;
                }, 10);
            }
        }
    }
    window.startEdit = function(id) {
        editingId = id;
        applyFilterAndRender(true);
    }
    window.cancelEdit = function() {
        editingId = null;
        applyFilterAndRender(true);
    }
    window.saveEdit = async function(id) {
        showSpinner(true);
        let tvg_id = document.getElementById('edit-tvgid').value;
        let logo_url = document.getElementById('edit-logo').value;
        let name = document.getElementById('edit-name').value;
        let stream_url = document.getElementById('edit-url').value;
        let fd = new FormData();
        fd.append('tvg_id', tvg_id);
        fd.append('logo_url', logo_url);
        fd.append('name', name);
        fd.append('stream_url', stream_url);
        await fetch(`/channels/${id}`, {method: 'POST', body: fd});
        editingId = null;
        await loadChannels();
        showSpinner(false);
    }
    window.deleteChannel = async function(id) {
        if (!confirm('Are you sure you want to delete this channel?')) return;
        showSpinner(true);
        await fetch(`/channels/${id}`, {method: 'DELETE'});
        editingId = null;
        await loadChannels();
        showSpinner(false);
    }
    window.m3uEditName = function(idx, val) { m3uChannels[idx].name = val; }
    window.m3uEditUrl = function(idx, val) { m3uChannels[idx].url = val; }
    window.m3uToggleKeep = function(idx, checked) { m3uKeep[idx] = checked; }
    window.m3uPreviewStream = function(url) {
        const player = document.getElementById('m3uPreviewPlayer');
        if (window.hls) {
            window.hls.destroy();
            window.hls = null;
        }
        if (Hls.isSupported() && url.endsWith('.m3u8')) {
            window.hls = new Hls();
            window.hls.loadSource(url);
            window.hls.attachMedia(player);
            player.style.display = '';
            player.play();
        } else if (player.canPlayType('application/vnd.apple.mpegurl')) {
            player.src = url;
            player.style.display = '';
            player.play();
        } else {
            player.src = url;
            player.style.display = '';
            player.play();
            setTimeout(() => {
                if (player.error) {
                    alert('Your browser does not support HLS playback for this stream.');
                }
            }, 1000);
        }
    }
    document.getElementById('filterInput').addEventListener('input', function() {
        showSpinner(true);
        setTimeout(() => {
            applyFilterAndRender(true);
            showSpinner(false);
        }, 100);
    });
    document.getElementById('tableContainer').addEventListener('scroll', onScroll);
    loadChannels();
    document.getElementById('addForm').onsubmit = async function(e) {
        e.preventDefault();
        showSpinner(true);
        let form = e.target;
        let fd = new FormData(form);
        await fetch('/channels', {method: 'POST', body: fd});
        form.reset();
        await loadChannels();
        showSpinner(false);
    };
    document.getElementById('uploadForm').onsubmit = async function(e) {
        e.preventDefault();
        showSpinner(true);
        let form = e.target;
        let fd = new FormData(form);
        let resp = await fetch('/channels_upload', {method: 'POST', body: fd});
        let data = await resp.json();
        if (data.status === 'ok' && data.channels) {
            m3uChannels = data.channels;
            m3uKeep = m3uChannels.map(() => true);
            renderM3uPreview();
        } else {
            alert('Failed to parse M3U file: ' + (data.detail || 'Unknown error'));
        }
        form.reset();
        showSpinner(false);
    };
    document.getElementById('saveM3uChannelsBtn').onclick = async function() {
        showSpinner(true);
        const toSave = m3uChannels.filter((_, idx) => m3uKeep[idx]);
        for (let ch of toSave) {
            let fd = new FormData();
            fd.append('tvg_id', ch.tvg_id || '');
            fd.append('logo_url', ch.logo || '');
            fd.append('name', ch.name || '');
            fd.append('stream_url', ch.url || '');
            await fetch('/channels', {method: 'POST', body: fd});
        }
        m3uChannels = [];
        m3uKeep = [];
        renderM3uPreview();
        await loadChannels();
        showSpinner(false);
        alert('Selected channels saved!');
    };
    </script>
</body>
</html>
'''

@app.get("/channels", response_class=HTMLResponse)
def serve_channels_frontend():
    return FRONTEND_HTML

    

import threading

class ChannelManager(threading.Thread):
    def __init__(self , host="0.0.0.0" , port=8030):
        super().__init__()
        self.host = host
        self.port = port
        threading.Thread.__init__(self)
        self.daemon = True
        self.name = "ChannelManager"

    def run(self):
        uvicorn.run("manager:app", host=self.host, port=self.port, log_level="info")


# if __name__ == "__main__":
uvicorn.run(app, host="0.0.0.0", port=8030, log_level="info")
