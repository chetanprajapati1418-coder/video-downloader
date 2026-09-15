from flask import Flask, render_template, request, jsonify, send_from_directory
import os, uuid, yt_dlp

app = Flask(__name__)
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.get("/")
def index():
    return render_template("index.html")

@app.post("/info")
def info():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify(error="Please enter a video URL."), 400
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True}) as ydl:
            i = ydl.extract_info(url, download=False)
        return jsonify(title=i.get("title","Untitled"), thumbnail=i.get("thumbnail"), duration=i.get("duration"))
    except Exception as e:
        return jsonify(error=str(e)[:500]), 400

@app.post("/download")
def download():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    quality = str(data.get("quality") or "720")
    if not url:
        return jsonify(error="URL is required."), 400
    try:
        h = int(quality) if quality.isdigit() else 720
        uid = uuid.uuid4().hex
        out = os.path.join(DOWNLOAD_DIR, uid + ".%(ext)s")
        fmt = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/best"
        opts = {"format":fmt,"outtmpl":out,"noplaylist":True,"quiet":True,"merge_output_format":"mp4"}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
        candidates=[f for f in os.listdir(DOWNLOAD_DIR) if f.startswith(uid+".") and not f.endswith(".part")]
        if not candidates:
            return jsonify(error="Output file was not found."),500
        return jsonify(file=candidates[0], title=info.get("title","video"))
    except Exception as e:
        return jsonify(error=str(e)[:700]),400

@app.get("/files/<path:name>")
def files(name):
    return send_from_directory(DOWNLOAD_DIR,name,as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
