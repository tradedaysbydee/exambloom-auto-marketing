"""ExamBloom automated organic Facebook/Instagram publisher.
Daily render + caption generation is free; publishing needs owner-authorized Meta credentials.
"""
import argparse
import datetime as dt
import json
import os
import random
import subprocess
import time
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).parent.resolve()
HISTORY_FILE = ROOT / "data" / "history.json"
SITE = "https://exambloom.co.uk"
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
]
FONT_REGULAR = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]
NAVY, PURPLE, YELLOW, WHITE = "#0C1A3B", "#6436EF", "#FFC83D", "#FFFFFF"
VERSION = os.getenv("GRAPH_API_VERSION", "v26.0")
GRAPH = "https://graph.facebook.com/" + VERSION

# Parent-directed, benefits-first messaging; deliberately avoid unverified guarantees.
from creative_library import OFFERS, QUIZZES
from strategy import choose_offer
from campaign_gallery import select_campaign, as_post


def font(size, bold=True):
    for path in (FONT_CANDIDATES if bold else FONT_REGULAR):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def today():
    return dt.datetime.now(ZoneInfo("Europe/London")).date()

def url_for(day, campaign, destination):
    base = destination or SITE
    if not base.startswith("https://exambloom.co.uk"):
        raise ValueError("Destination must stay on the verified ExamBloom domain.")
    if "?" in base:
        sep = "&"
    else:
        sep = "?"
    return base + sep + urlencode({
        "utm_source": "facebook",
        "utm_medium": "organic_social",
        "utm_campaign": "exam_bloom_daily",
        "utm_content": f"{day.isoformat()}_{campaign}"
    })

def compose_post(day, destination):
    # Approved real-image campaigns go out on four sales days each week.
    # A missing image cleanly falls back to the regular generated graphic.
    gallery = select_campaign(day)
    if gallery is not None:
        return as_post(gallery, day, destination, url_for)

    # Five conversion posts and two educational engagement posts per week.
    weekday = day.weekday()
    day_index = (day.toordinal() // 7) % 1000
    if weekday in (2, 5):
        quiz_index = (day_index + weekday) % len(QUIZZES)
        title, question, answers, correct = QUIZZES[quiz_index]
        creative_id = "quiz-" + str(quiz_index)
        tag = "quiz"
        headline = (title, "Test your knowledge.")
        detail = question
        helper = answers
        facebook = (
            f"Can your family answer this? {question}\n{answers}\n\n"
            f"Answer: {correct}. For more learning activities, explore ExamBloom: "
        )
        instagram = (
            f"Today's family quiz! {question}\n{answers}\n\n"
            f"Answer: {correct}. Explore more practice via the link in our bio.\n"
            "#ExamBloom #FamilyLearning #UKParents #LearningAtHome"
        )
    else:
        baseline_index = (day_index + weekday) % len(OFFERS)
        # Learn from observed theme scores, while exploring a new idea in 1/5 posts.
        offer_index = choose_offer(day, baseline_index, ROOT / "data" / "performance.json")
        headline1, headline2, detail, cta = OFFERS[offer_index]
        creative_id = "offer-" + str(offer_index)
        tag = "membership"
        headline = (headline1, headline2)
        helper = "Practice tests • Daily Brain Sprint • Progress"
        facebook = (
            f"{headline1} {headline2}\n\n{detail}\n\n{cta} "
            "Create a free test and explore membership options: "
        )
        instagram = (
            f"{headline1} {headline2}\n\n{detail}\n\n{cta} "
            "Visit the link in our bio.\n"
            "#ExamBloom #UKParents #HomeLearning #LearningAtHome"
        )
    return {
        "date": day.isoformat(), "category": tag,
        "headline": list(headline), "detail": detail, "helper": helper,
        "creative_id": creative_id,
        "facebook_caption": facebook + url_for(day, tag, destination),
        "instagram_caption": instagram, "site": SITE,
    }

def wrap_text(draw, words, font_obj, width):
    lines, current = [], ""
    for word in words.split():
        candidate = (current + " " + word).strip()
        if draw.textbbox((0, 0), candidate, font=font_obj)[2] > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines

def render(post, target):
    # Gallery items are pre-approved artwork; keep their imagery intact.
    # Convert to the stable 1080×1350 JPEG format used by Buffer.
    gallery_rel = post.get("gallery_asset")
    if gallery_rel:
        source = (ROOT / gallery_rel).resolve()
        campaigns = (ROOT / "assets" / "campaigns").resolve()
        if source.parent != campaigns or not source.is_file():
            raise ValueError("Campaign image is missing or outside the approved gallery.")
        with Image.open(source) as original:
            image = ImageOps.fit(original.convert("RGB"), (1080, 1350),
                                 method=Image.Resampling.LANCZOS)
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target, "JPEG", quality=90, optimize=True)
        return

    img = Image.new("RGB", (1080, 1350), "#F7F3FF")
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 1080, 170), fill=WHITE)
    d.rounded_rectangle((58, 46, 132, 120), radius=20, fill=PURPLE)
    d.text((78, 49), "✦", font=font(42), fill=WHITE)
    d.text((150, 57), "exam", font=font(48), fill=NAVY)
    d.text((291, 57), "bloom.", font=font(48), fill=PURPLE)
    d.ellipse((-210, 1000, 490, 1650), fill="#E5DBFF")
    d.ellipse((740, -290, 1400, 430), fill="#EBE2FF")

    photo = None
    for name in (("family.jpg", "family.png") if post["category"] == "membership"
                 else ("challenge.jpg", "challenge.png", "test.jpg", "test.png")):
        path = ROOT / "assets" / name
        if path.exists():
            photo = path
            break
    if post["category"] == "quiz":
        # The answers are now prominent, not buried below the post or hidden.
        d.rounded_rectangle((65, 658, 1015, 1035), radius=30,
                            fill=WHITE, outline="#DED2FF", width=5)
        options = [s.strip() for s in post["helper"].split("|")]
        for n, option in enumerate(options[:3]):
            top = 681 + n * 113
            d.rounded_rectangle((105, top, 975, top + 94), radius=22,
                                fill="#EEE8FF", outline="#E1D6FF", width=3)
            option_font = font(48, True)
            while option_font.size > 27 and d.textbbox((0, 0), option, font=option_font)[2] > 805:
                option_font = font(option_font.size - 2, True)
            d.text((142, top + 17), option, font=option_font, fill=NAVY)
    elif photo:
        with Image.open(photo) as original:
            panel = ImageOps.fit(original.convert("RGB"), (970, 420))
        img.paste(panel, (55, 595))
        d.rounded_rectangle((45, 585, 1035, 1025), radius=30, outline=WHITE, width=15)
    else:
        d.rounded_rectangle((65, 650, 1015, 1030), radius=32, fill=WHITE, outline="#DED2FF", width=5)
        d.rounded_rectangle((130, 730, 950, 930), radius=26, fill="#ECE5FF")
        d.text((190, 784), "MATHS  •  ENGLISH", font=font(45), fill=PURPLE)
        d.text((245, 856), "QUIZZES  •  11+ PREP", font=font(39), fill=NAVY)

    for y, heading, heading_color, size in (
        (220, post["headline"][0], NAVY, 65),
        (304, post["headline"][1], PURPLE, 67),
    ):
        head_font = font(size)
        while head_font.size > 33 and d.textbbox((0, 0), heading, font=head_font)[2] > 955:
            head_font = font(head_font.size - 2)
        d.text((62, y), heading, font=head_font, fill=heading_color)
    d.rounded_rectangle((62, 409, 495, 419), radius=4, fill=YELLOW)
    if post["category"] == "quiz":
        # Make the main quiz question big, bold, and easy to read on phones.
        question_font = font(60, True)
        y = 454
        for line in wrap_text(d, post["detail"], question_font, 950)[:2]:
            d.text((62, y), line, font=question_font, fill=NAVY)
            y += 76
    else:
        # Preserve the original size for longer sales/benefit captions.
        description_font = font(34, False)
        y = 465
        for line in wrap_text(d, post["detail"], description_font, 950)[:3]:
            d.text((62, y), line, font=description_font, fill=NAVY)
            y += 48
    d.rounded_rectangle((50, 1094, 1030, 1235), radius=48, fill=PURPLE)
    d.text((95, 1128), "Explore ExamBloom", font=font(56), fill=WHITE)
    d.text((61, 1277), "exambloom.co.uk   |   Little steps. Big progress.", font=font(26), fill=NAVY)
    target.parent.mkdir(parents=True, exist_ok=True)
    img.save(target, "JPEG", quality=90)

def api(method, path, token, *, data=None, files=None, params=None):
    form = dict(data or {})
    query = dict(params or {})
    if method == "GET":
        query["access_token"] = token
    else:
        form["access_token"] = token
    try:
        response = requests.request(
            method, GRAPH + "/" + path.lstrip("/"),
            params=query, data=form if method != "GET" else None,
            files=files, timeout=45,
        )
        parsed = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError("Meta request failed; check connection and Meta permissions.") from exc
    if not response.ok or "error" in parsed:
        problem = parsed.get("error", {})
        raise RuntimeError(
            "Meta API error " + str(problem.get("code", response.status_code))
            + ": " + str(problem.get("message", "request failed"))[:200]
        )
    return parsed

def git_save(files, message):
    if os.getenv("GITHUB_ACTIONS") != "true":
        return
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
    subprocess.run(["git", "config", "user.email",
                    "41898282+github-actions[bot]@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", "--", *files], check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if diff.returncode == 0:
        return
    subprocess.run(["git", "commit", "-m", message], check=True)
    branch = os.getenv("GITHUB_REF_NAME", "main")
    subprocess.run(["git", "push", "origin", "HEAD:refs/heads/" + branch], check=True)

def photo_public(url):
    for _ in range(10):
        try:
            response = requests.get(url, timeout=20)
            if response.ok and response.headers.get("Content-Type", "").startswith("image/"):
                return
        except requests.RequestException:
            pass
        time.sleep(6)
    raise RuntimeError("Instagram image was not accessible on public GitHub.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD")
    args = parser.parse_args()
    day = dt.date.fromisoformat(args.date) if args.date else today()
    destination = os.getenv("SALES_DESTINATION_URL", "").strip() or SITE
    post = compose_post(day, destination)
    image_path = ROOT / "generated" / (day.isoformat() + ".jpg")
    caption_path = ROOT / "generated" / (day.isoformat() + ".json")
    render(post, image_path)
    caption_path.write_text(json.dumps(post, indent=2) + "\n", encoding="utf-8")
    print("Generated safe preview:", image_path.name, post["category"])

    if not args.publish or os.getenv("PUBLISH_ENABLED", "false").lower() != "true":
        print("SAFE MODE: promotional artwork generated; Buffer publication is separately disabled until the account test passes and PUBLISH_ENABLED=true.")
        return
    token = os.getenv("META_PAGE_ACCESS_TOKEN", "").strip()
    page = os.getenv("META_PAGE_ID", "").strip()
    ig = os.getenv("META_IG_USER_ID", "").strip()
    repo = os.getenv("GITHUB_REPOSITORY", "").strip()
    branch = os.getenv("GITHUB_REF_NAME", "main")
    if not token or (not page and not ig) or not repo:
        raise RuntimeError("Missing Meta token, Facebook/Instagram ID, or GitHub repository.")
    if "/" not in repo:
        raise RuntimeError("Invalid GitHub repository identifier.")

    # Commit the image first, making the image public for Instagram media import.
    git_save(["generated/" + image_path.name, "generated/" + caption_path.name],
             "Generate ExamBloom creative " + day.isoformat())
    history = {}
    if HISTORY_FILE.exists():
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    record = history.setdefault(day.isoformat(), {})
    errors = []

    def checkpoint(key, value):
        record[key] = value
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_FILE.write_text(json.dumps(history, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        git_save(["data/history.json"], "Record ExamBloom " + key + " publication")

    if page and not record.get("facebook"):
        try:
            with image_path.open("rb") as fh:
                resp = api("POST", page + "/photos", token,
                           data={"message": post["facebook_caption"]},
                           files={"source": ("exam-bloom.jpg", fh, "image/jpeg")})
            checkpoint("facebook", resp.get("post_id") or resp.get("id"))
            print("Facebook published")
        except Exception as exc:
            errors.append("Facebook: " + str(exc))
    if ig and not record.get("instagram"):
        try:
            from urllib.parse import quote
            image_url = "https://raw.githubusercontent.com/" + repo + "/" + branch + "/generated/" + quote(image_path.name)
            photo_public(image_url)
            container = api("POST", ig + "/media", token,
                            data={"image_url": image_url, "caption": post["instagram_caption"]})["id"]
            for _ in range(12):
                status = api("GET", container, token, params={"fields": "status_code"}).get("status_code")
                if status == "FINISHED":
                    break
                if status in ("ERROR", "EXPIRED"):
                    raise RuntimeError("Instagram rejected the image container.")
                time.sleep(5)
            else:
                raise RuntimeError("Instagram container did not become ready.")
            result = api("POST", ig + "/media_publish", token, data={"creation_id": container})
            checkpoint("instagram", result["id"])
            print("Instagram published")
        except Exception as exc:
            errors.append("Instagram: " + str(exc))
    if errors:
        raise RuntimeError(" | ".join(errors))
    print("ExamBloom daily publishing workflow complete.")

if __name__ == "__main__":
    main()
