"""Make one kids Short (1080x1920, 30 fps) from an episode spec in episodes.json.

usage: python3 tool/gen.py EPISODE_ID            -> videos/EPISODE_ID.mp4
       python3 tool/gen.py EPISODE_ID --stills   -> preview PNGs in /tmp

Episode types:
  count : icons pile up one by one while the number and its word are shown
  cards : one card per item (letter, colour, animal, shape...), each with a big icon
"""
import json, math, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tool")
FPS, W, H = 30, 1080, 1920
CARD = 3.0          # seconds per card
START = 2.0         # first card starts here
OUTRO = 3.5         # outro length
WORDS = "ZERO ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN ELEVEN TWELVE".split()
PALETTE = ["#ff4d6d", "#ff9f1c", "#2ec4b6", "#3a86ff", "#8338ec", "#06a77d", "#f15bb5", "#e76f51"]

THEMES = {
 "sky": """<div style="position:absolute;inset:0;background:linear-gradient(#7fd3ff,#c9efff 70%)"></div>
  <div class="sun"></div><div class="cloud c1"></div><div class="cloud c2"></div>
  <div class="hill" style="background:#7bd389"></div><div class="hill" style="top:1500px;left:-400px;background:#5cb85c"></div>""",
 "night": """<div style="position:absolute;inset:0;background:linear-gradient(#141e4a,#3b2f7a 75%,#5b3f8f)"></div>
  <div class="moon"></div>{stars}
  <div class="hill" style="background:#2b4f6e"></div><div class="hill" style="top:1500px;left:-400px;background:#1f3b55"></div>""",
 "beach": """<div style="position:absolute;inset:0;background:linear-gradient(#5ec8f2,#bfeeff 60%)"></div>
  <div class="sun"></div><div class="cloud c1"></div>
  <div style="position:absolute;left:0;right:0;top:1350px;height:200px;background:#2a9df4;animation:wave 4s ease-in-out infinite alternate"></div>
  <div style="position:absolute;left:-100px;right:-100px;top:1500px;height:600px;border-radius:50% 50% 0 0;background:#f6d79a"></div>""",
 "candy": """<div style="position:absolute;inset:0;background:linear-gradient(160deg,#ffd6e8,#e2c6ff 60%,#c6e6ff)"></div>{dots}""",
}
TEXT_DARK = {"sky": False, "night": False, "beach": False, "candy": False}


def icon(code):
    return f'<img src="{TOOL}/icons/{code}.svg">'


def stars():
    import random
    r = random.Random(7)
    return "".join(f'<div class="star" style="left:{r.randint(0,1060)}px;top:{r.randint(0,1250)}px;'
                   f'animation-delay:{r.random()*2:.2f}s"></div>' for _ in range(45))


def dots():
    import random
    r = random.Random(3)
    return "".join(f'<div class="dot" style="left:{r.randint(-40,1040)}px;top:{r.randint(-40,1880)}px;'
                   f'width:{(s:=r.randint(30,90))}px;height:{s}px;background:{r.choice(PALETTE)}"></div>' for _ in range(22))


CSS = """
@font-face{font-family:Baloo;src:url(%(tool)s/fonts/baloo-2-latin-800-normal.woff2);font-weight:800}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;font-family:Baloo,sans-serif}
.sun{position:absolute;right:-30px;top:-30px;width:230px;height:230px;border-radius:50%%;background:#ffd23f;box-shadow:0 0 0 30px rgba(255,210,63,.3);animation:spin %(dur)ss linear forwards}
.moon{position:absolute;right:60px;top:330px;width:150px;height:150px;border-radius:50%%;box-shadow:-40px 10px 0 0 #fff4c2}
.star{position:absolute;width:8px;height:8px;border-radius:50%%;background:#fff;animation:tw 1.2s ease-in-out infinite alternate}
.dot{position:absolute;border-radius:50%%;opacity:.25;animation:float %(dur)ss linear forwards}
.cloud{position:absolute;background:#fff;border-radius:100px;height:90px;opacity:.95}
.cloud:before,.cloud:after{content:"";position:absolute;background:#fff;border-radius:50%%}
.cloud:before{width:110px;height:110px;left:40px;top:-55px}.cloud:after{width:80px;height:80px;left:120px;top:-35px}
.c1{width:260px;left:-40px;top:330px;animation:drift %(dur)ss linear forwards}.c2{width:220px;left:700px;top:470px;animation:drift2 %(dur)ss linear forwards}
.hill{position:absolute;left:-200px;right:-200px;top:1350px;height:900px;border-radius:50%% 50%% 0 0}
@keyframes spin{to{transform:rotate(90deg)}}@keyframes tw{to{opacity:.2}}@keyframes float{to{transform:translateY(-160px)}}
@keyframes drift{to{transform:translateX(220px)}}@keyframes drift2{to{transform:translateX(-200px)}}@keyframes wave{to{transform:translateY(18px)}}
.title{position:absolute;top:150px;left:40px;right:40px;text-align:center;font-size:118px;line-height:1.05;color:#fff;-webkit-text-stroke:7px %(accent)s;paint-order:stroke fill;opacity:0;animation:pop .7s cubic-bezier(.3,1.6,.5,1) .2s forwards}
.blk{position:absolute;left:0;right:0;text-align:center;opacity:0;animation:pop .6s cubic-bezier(.3,1.6,.5,1) forwards,gone .3s ease-in forwards}
.big{font-size:300px;line-height:1;-webkit-text-stroke:10px #fff;paint-order:stroke fill;text-shadow:0 12px 0 rgba(0,0,0,.12)}
.mid{font-size:120px;line-height:1.05;-webkit-text-stroke:7px #fff;paint-order:stroke fill;text-shadow:0 8px 0 rgba(0,0,0,.12)}
.sub{font-size:76px;line-height:1.1;color:#fff;-webkit-text-stroke:6px #333;paint-order:stroke fill;margin-top:10px}
.ic img{width:100%%;height:100%%;filter:drop-shadow(0 14px 0 rgba(0,0,0,.15))}
.ic{position:absolute;opacity:0;animation:drop .7s cubic-bezier(.3,1.5,.5,1) forwards,hop .5s ease-in-out 4 alternate}
.cardic{width:560px;height:560px;margin:30px auto 0;position:relative;animation:bob 1.5s ease-in-out infinite alternate}
.cardic img{width:100%%;height:100%%;filter:drop-shadow(0 18px 0 rgba(0,0,0,.15))}
.swatch{position:absolute;inset:-40px;border-radius:50%%;opacity:.9}
.badge{position:absolute;right:-10px;bottom:-10px;font-size:90px;color:#fff;-webkit-text-stroke:6px #333;paint-order:stroke fill}
@keyframes bob{to{transform:translateY(-30px) rotate(3deg)}}
@keyframes pop{from{opacity:0;transform:scale(.2)}to{opacity:1;transform:scale(1)}}
@keyframes gone{to{opacity:0;transform:scale(.6)}}
@keyframes drop{from{opacity:0;transform:translateY(-500px) scale(.6)}to{opacity:1;transform:none}}
@keyframes hop{to{transform:translateY(-45px)}}
.fin{position:absolute;top:640px;left:0;right:0;text-align:center;opacity:0;animation:pop .7s cubic-bezier(.3,1.6,.5,1) forwards}
.fin .a{font-size:170px;line-height:1;color:#ffd23f;-webkit-text-stroke:9px #ff4d6d;paint-order:stroke fill}
.fin .b{font-size:84px;color:#fff;-webkit-text-stroke:6px #3a86ff;paint-order:stroke fill;margin-top:24px;line-height:1.1}
"""


def grid(n, top=1080, bottom=1780):
    per = 3 if n <= 6 else 4
    rows = math.ceil(n / per)
    size = min(260 if per == 3 else 210, (bottom - top) / rows - 20)
    gap = (W - per * size) / (per + 1)
    pos = []
    for i in range(n):
        r, c = divmod(i, per)
        inrow = min(per, n - r * per)
        x0 = (W - (inrow * size + (inrow - 1) * gap)) / 2
        pos.append((x0 + c * (size + gap), top + r * (size + 20), size))
    return pos


def build(ep):
    theme = ep.get("theme", "sky")
    k = ep["n"] if ep["type"] == "count" else len(ep["items"])
    out_t = START + CARD * k + 0.3
    dur = out_t + OUTRO
    body = [THEMES[theme].format(stars=stars(), dots=dots())]
    body.append(f'<div class="title">{ep["title"]}</div>')
    cue = []
    if ep["type"] == "count":
        for i, (x, y, s) in enumerate(grid(ep["n"])):
            t = START + CARD * i
            c = PALETTE[i % len(PALETTE)]
            body.append(f'<div class="blk" style="top:470px;animation-delay:{t}s,{t+CARD-0.3}s;color:{c}">'
                        f'<div class="big">{i+1}</div><div class="mid">{WORDS[i+1]}</div></div>')
            body.append(f'<div class="ic" style="left:{x:.0f}px;top:{y:.0f}px;width:{s:.0f}px;height:{s:.0f}px;'
                        f'animation-delay:{t}s,{out_t}s">{icon(ep["icon"])}</div>')
            cue.append(t)
    else:
        for i, it in enumerate(ep["items"]):
            t = START + CARD * i
            c = it.get("color") or PALETTE[i % len(PALETTE)]
            sw = f'<div class="swatch" style="background:{it["swatch"]}"></div>' if it.get("swatch") else ""
            badge = f'<div class="badge">{it["badge"]}</div>' if it.get("badge") else ""
            big = f'<div class="{"big" if len(it["big"]) <= 2 else "mid"}" style="color:{c}">{it["big"]}</div>'
            body.append(f'<div class="blk" style="top:{470 if len(it["big"])<=2 else 520}px;animation-delay:{t}s,{t+CARD-0.3}s">'
                        f'{big}<div class="cardic">{sw}{icon(it["icon"])}{badge}</div>'
                        f'<div class="sub">{it["sub"]}</div></div>')
            cue.append(t)
    body.append(f'<div class="fin" style="animation-delay:{out_t}s"><div class="a">{ep.get("outro","Great Job!")}</div>'
                f'<div class="b">{ep.get("outro_sub","")}</div></div>')
    accent = {"night": "#8338ec", "candy": "#f15bb5"}.get(theme, "#ff4d6d")
    css = CSS % {"tool": TOOL, "dur": f"{dur:.2f}", "accent": accent}
    html = f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css}</style></head><body>{"".join(body)}</body></html>'
    return html, dur, cue, out_t


def audio(cue, out_t, dur, path):
    """Rising 'pop' per card plus a chime at the outro, all synthesised."""
    ins, parts = [], []
    for i, t in enumerate(cue):
        f = 523 * 2 ** ((i * 2) / 12)
        ins += ["-f", "lavfi", "-i", f"sine=f={f:.1f}:d=0.2"]
        parts.append(f"[{len(parts)}]afade=t=out:d=0.2,volume=0.45,adelay={int(t*1000)+80}:all=1[p{len(parts)}]")
    base = len(parts)
    for j, f in enumerate([523, 659, 784]):
        ins += ["-f", "lavfi", "-i", f"sine=f={f}:d={0.25 if j < 2 else 0.6}"]
    chime = f"[{base}][{base+1}][{base+2}]concat=n=3:v=0:a=1,afade=t=out:st=0.7:d=0.4,volume=0.45,adelay={int(out_t*1000)}:all=1[ch]"
    labels = "".join(f"[p{i}]" for i in range(base)) + "[ch]"
    fc = ";".join(parts + [chime, f"{labels}amix=inputs={base+1}:normalize=0,apad=whole_dur={dur}[out]"])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *ins, "-filter_complex", fc, "-map", "[out]",
                    "-ar", "44100", "-ac", "2", path], check=True)


def render(html, dur, out, stills=None):
    from playwright.sync_api import sync_playwright
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
        page = f.name
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto("file://" + page)
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(500)
        seek = "t=>{document.getAnimations().forEach(a=>{a.pause();a.currentTime=t*1000});}"
        if stills:
            for t in stills:
                pg.evaluate(seek, t)
                pg.screenshot(path=f"{out}_{t:.1f}.png")
        else:
            ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS),
                                   "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                                   "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
            for i in range(int(dur * FPS)):
                pg.evaluate(seek, i / FPS)
                ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
            ff.stdin.close()
            if ff.wait() != 0:
                sys.exit("ffmpeg failed")
        b.close()


def main():
    eid = sys.argv[1]
    eps = {e["id"]: e for e in json.load(open(os.path.join(ROOT, "episodes.json")))}
    ep = eps[eid]
    html, dur, cue, out_t = build(ep)
    if "--stills" in sys.argv:
        k = len(cue)
        render(html, dur, f"/tmp/{eid}", [START + CARD * (k - 1) + 1.2, out_t + 1.5])
        print(f"/tmp/{eid}_*.png")
        return
    os.makedirs(os.path.join(ROOT, "videos"), exist_ok=True)
    tmp_v = f"/tmp/{eid}_v.mp4"
    tmp_a = f"/tmp/{eid}_a.wav"
    render(html, dur, tmp_v)
    audio(cue, out_t, dur, tmp_a)
    final = os.path.join(ROOT, "videos", f"{eid}.mp4")
    part = final[:-4] + ".part.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp_v, "-i", tmp_a, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", part], check=True)
    os.replace(part, final)
    print(final, f"{dur:.1f}s")


if __name__ == "__main__":
    main()
