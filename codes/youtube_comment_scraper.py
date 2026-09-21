## THIS CODE IS DESIGNED TO SCRAPE YOUTUBE COMMENTS USING THE YOUTUBE API

# First, i had to get  google api key to use the api on youtube. you must do this as well as use your own key. go to https://console.cloud.google.com/
# 1. create a project
# 2. go to the project
# 3. go to APIs & Services > Library
# 4. find "YouTube Data API v3" and enable it
# 5. create credentials for the api


#i want to use the top 2,000 comments so that would be
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --top-pct 25 --order "relevance" --max-comments 2000

#=================================================================
#pulling api key from the dotenv for this program
#key is in a .env file in this same directory
import os
from dotenv import load_dotenv

CWD = os.getcwd()
env_file = os.path.join(CWD, "youtube_scraping.env")
load_dotenv(dotenv_path=env_file)
API_KEY = os.getenv("API_KEY")

#=================================================================

#imports and variables
import argparse
import os
import re
import sys
import time
import pandas as pd
import requests

API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"


#helper functions
def extract_video_id(url_or_id: str) -> str:
    """takes a full YouTube URL and returns the video ID."""
    patterns = [
        r"(?:v=)([A-Za-z0-9_-]{11})",             # watch?v=ID
        r"(?:youtu\.be/)([A-Za-z0-9_-]{11})",      # youtu.be/ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id
    raise ValueError(f"Could not extract a video ID from: {url_or_id}")

def fetch_comments(video_id: str, api_key: str, max_comments: int = 5000,
                    order: str = "relevance") -> pd.DataFrame:
    """fetches the comments from video_id and returns them in a pd dataframe"""
    rows = []
    page_token = None

    #while there's still comments
    while len(rows) < max_comments:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "key": api_key,
            "maxResults": 100,
            "order": order,
            "textFormat": "plainText",
        }
        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(API_URL, params=params)

        #if run into bad status code, break the loop and fail loud
        if resp.status_code == 403:
            body = resp.json()
            reason = body.get("error", {}).get("errors", [{}])[0].get("reason", "")
            if reason == "commentsDisabled":
                print(f"Comments are disabled on this video: {reason}, {resp.status_code}")
                break
            print(f"API error 403: {body}")
            break
        resp.raise_for_status()

        print(f"response code: {resp.status_code}")

        #otherwise, we have data. get it and append it
        data = resp.json()
        for item in data.get("items", []):
            top = item["snippet"]["topLevelComment"]["snippet"]
            rows.append({
                "comment_id": item["snippet"]["topLevelComment"]["id"],
                "author": top.get("authorDisplayName"),
                "text": top.get("textDisplay"),
                "like_count": top.get("likeCount", 0),
                "reply_count": item["snippet"].get("totalReplyCount", 0),
                "published_at": top.get("publishedAt"),
                "updated_at": top.get("updatedAt"),
            })

        page_token = data.get("nextPageToken")
        print(f"  fetched {len(rows)} comments so far...")

        if not page_token:
            break
        time.sleep(1) #zzz

    return pd.DataFrame(rows[:max_comments])

def top_percent(df: pd.DataFrame, pct: float) -> pd.DataFrame:
    """return the top % of comments ranked by like_count (descending)."""
    if df.empty:
        return df
    n = max(1, int(len(df) * (pct / 100)))
    return df.sort_values("like_count", ascending=False).head(n).reset_index(drop=True)


#main
def main():
    #args
    parser = argparse.ArgumentParser(description="Pull YouTube comments and filter to top X%.")
    parser.add_argument("--url", required=True, help="YouTube video URL or video ID")
    parser.add_argument("--api-key", default=API_KEY,
                         help="YouTube Data API key (defaults to YOUTUBE_API_KEY env var)")
    parser.add_argument("--max-comments", type=int, default=1000,
                         help="Max total comments to fetch before filtering (default 5000)")
    parser.add_argument("--top-pct", type=float, default=25.0,
                         help="Keep only the top X percent of comments by like count (default 10)")
    parser.add_argument("--order", choices=["relevance", "time"], default="relevance",
                         help="Fetch order from the API (default relevance = YouTube's 'top comments')")
    parser.add_argument("--output", default=os.path.join(CWD, "comments" "comments.csv"), help="Output CSV path")
    args = parser.parse_args()

    if not args.api_key:
        sys.exit("No API key found. Pass --api-key or set the YOUTUBE_API_KEY env var.")

    video_id = extract_video_id(args.url)
    print(f"Video ID: {video_id}")

    all_comments = fetch_comments(video_id, args.api_key, args.max_comments, args.order)
    print(f"Total comments fetched: {len(all_comments)}")

    all_comments.to_csv(args.output, index=False)
    print(f"Saved all fetched comments -> {args.output}")

    filtered = top_percent(all_comments, args.top_pct)
    top_path = args.output.replace(".csv", f"_top{int(args.top_pct)}pct.csv")
    filtered.to_csv(top_path, index=False)
    print(f"Saved top {args.top_pct}% by likes ({len(filtered)} comments) -> {top_path}")


if __name__ == "__main__":
    main()


#for kendrick's not like us video
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=H58vbez_m4E" --top-pct 25 --order "relevance" --max-comments 2000

#======================================================================

#for drake's first person shooter
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=sRs2o36a1Us" --top-pct 25 --order "relevance" --max-comments 1000

#for Rap city's lyrics of drake's first person shooter
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=XpPhCURVOGw" --top-pct 25 --order "relevance" --max-comments 1000

#for Knox Hill's reaction of drake's first person shooter
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=FUtC0E6WLtc" --top-pct 25 --order "relevance" --max-comments 1000

#======================================================================

#for Future's Like That
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=N9bKBAA22Go" --top-pct 25 --order "relevance" --max-comments 1000

#for Vibe Music's lyrics to Future's Like That
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=yGIWOtl-PME" --top-pct 25 --order "relevance" --max-comments 1000

#for Lost In Vegas' reaction to Future's Like That
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=vLX8UR5MZZY" --top-pct 25 --order "relevance" --max-comments 1000

#======================================================================

#for Drake's Push Ups
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=HKH9p19PRLA&list=RDHKH9p19PRLA&start_radio=1" --top-pct 25 --order "relevance" --max-comments 1000

#for Scru Face Jean's reaction to Drake's Push Ups
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=3Jpl3vkcX3E" --top-pct 25 --order "relevance" --max-comments 1000

#for BagOnly's Lyrics to Drake's Push Ups
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=DMvaSqDnHl8" --top-pct 25 --order "relevance" --max-comments 1000

#for Knox Hill's reaction to Drake's Push Ups
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=pRYzt5mHgqA" --top-pct 25 --order "relevance" --max-comments 1000

#======================================================================

#for Drake's Taylor Made Freestyle
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=lwu3RQQ_rDU" --top-pct 25 --order "relevance" --max-comments 1000

#for Joe Budden TV's reaction to Drake's Taylor Made Freestyle
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=VqobbMG1pz8" --top-pct 25 --order "relevance" --max-comments 1000

#for Knox Hill's reaction to Drake's Taylor Made Freestyle
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=UjWjojbYrao" --top-pct 25 --order "relevance" --max-comments 1000

#======================================================================

#for Kdot's Euphoria
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=NPqDIwWMtxg" --top-pct 25 --order "relevance" --max-comments 1000

#for VibesOnly's lyrics to Kdot's Euphoria
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=_sJ79aDQTeQ" --top-pct 25 --order "relevance" --max-comments 1000

#for Lost in Vegas's reaction to Kdot's Euphoria
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=Y3OurXW8AM4" --top-pct 25 --order "relevance" --max-comments 1000

#======================================================================

#for Rap Nation's lyrics to Kdot's 6:16 in LA
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=R1ypnmTMNqA" --top-pct 25 --order "relevance" --max-comments 1000

#for Lost in Vegas's reaction to Kdot's 6:16 in LA
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=0k95llnaSOc" --top-pct 25 --order "relevance" --max-comments 1000

#for Knox Hill's reaction to Kdot's 6:16 in LA
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=_reSOtwSyhc" --top-pct 25 --order "relevance" --max-comments 1000

#======================================================================

#for Drake's FAMILY MATTER
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=ZkXG3ZrXlbc" --top-pct 25 --order "relevance" --max-comments 1000

#for BagOnly's lyrics to Drake's FAMILY MATTER
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=VXRglPYwkvs" --top-pct 25 --order "relevance" --max-comments 1000

#for Knox Hill's reaction to Drake's FAMILY MATTER
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=S_LDhrelePQ" --top-pct 25 --order "relevance" --max-comments 1000

#======================================================================

#for Kdot's meet the grahams
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=2QiFl9Dc7D0" --top-pct 25 --order "relevance" --max-comments 1000

#for BagOnly's lyrics to Kdot's meet the grahams
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=j3OhV1och50" --top-pct 25 --order "relevance" --max-comments 1000

#for Lost in Vegas's reaction to Kdot's meet the grahams
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=_0_dqg4vgkg" --top-pct 25 --order "relevance" --max-comments 1000

#======================================================================

#for Kdot's Not Like Us
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=T6eK-2OQtew" --top-pct 25 --order "relevance" --max-comments 1000

#for BagOnly's lyrics to Kdot's Not Like Us
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=3wkNLqetX0M" --top-pct 25 --order "relevance" --max-comments 1000

#for Lost in Vegas's reaction to Kdot's Not Like Us
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=jfAYqh40zVY" --top-pct 25 --order "relevance" --max-comments 1000

#======================================================================

#for Drake's THE HEART PART 6
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=HJeY-FXidDQ" --top-pct 25 --order "relevance" --max-comments 1000

#for BagOnly's lyrics to Drake's THE HEART PART 6
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=y745KgtdIbA" --top-pct 25 --order "relevance" --max-comments 1000

#for Knox Hill's reaction to Drake's THE HEART PART 6
# python youtube_comment_scraper.py --url "https://www.youtube.com/watch?v=yjanCnC3baQ" --top-pct 25 --order "relevance" --max-comments 1000

