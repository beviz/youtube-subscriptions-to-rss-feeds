import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from google.auth.transport.requests import Request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def get_youtube_service():
    # Load credentials from environment variables (Github secrets)
    client_id = os.environ.get("YT_CLIENT_ID")
    client_secret = os.environ.get("YT_CLIENT_SECRET")
    refresh_token = os.environ.get("YT_REFRESH_TOKEN")
    if not all([client_id, client_secret, refresh_token]):
        raise Exception("YouTube credentials are not set in environment variables.")

    creds = Credentials(
        None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    # Ensure we have a valid access token (refresh if necessary)
    if not creds.valid or creds.expired:
        creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)

def load_subscribed_channel_ids():
    """Load all subscribed channel ids using the token file with YouTube API."""
    service = get_youtube_service()
    channel_ids = []
    request = service.subscriptions().list(
        part="snippet",
        mine=True,
        maxResults=50
    )
    while request is not None:
        response = request.execute()
        for item in response.get("items", []):
            cid = item["snippet"]["resourceId"]["channelId"]
            channel_ids.append(cid)
        request = service.subscriptions().list_next(request, response)
    return channel_ids

def get_channel_feed_url(channel_id):
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

def fetch_feed(channel_id):
    url = get_channel_feed_url(channel_id)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return {'channel_id': channel_id, 'feed': response.text}
    except Exception as e:
        return {'channel_id': channel_id, 'error': str(e)}

def extract_feed_items(feed_xml, channel_id):
    items = []
    try:
        tree = ET.ElementTree(ET.fromstring(feed_xml))
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in tree.findall('atom:entry', ns):
            published_elem = entry.find('atom:published', ns)
            published = published_elem.text if published_elem is not None else ""
            items.append({
                "channel_id": channel_id,
                "entry": ET.tostring(entry, encoding="unicode"),
                "published": published
            })
    except Exception:
        pass
    return items

def main():
    # 1. Load subscribed YouTube channel ids from token
    channel_ids = load_subscribed_channel_ids()

    # 2. Fetch all feeds in parallel with 10 threads
    feeds = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_cid = {executor.submit(fetch_feed, cid): cid for cid in channel_ids}
        for future in as_completed(future_to_cid):
            cid = future_to_cid[future]
            try:
                result = future.result()
                feeds[cid] = result
            except Exception as e:
                feeds[cid] = {'channel_id': cid, 'error': str(e)}

    # 3. Extract all feed items from successfully fetched feeds
    all_items = []
    for cid, result in feeds.items():
        if "feed" in result:
            items = extract_feed_items(result["feed"], cid)
            all_items.extend(items)
        else:
            print(f"Failed to fetch feed for {cid}: {result.get('error','(unknown error)')}")

    # 4. Sort items by publish time descending, keep top 100
    def parse_dt(dt_str):
        try:
            return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S%z")
        except Exception:
            return datetime.min.replace(tzinfo=None)
    all_items_sorted = sorted(all_items, key=lambda x: parse_dt(x["published"]), reverse=True)
    top_100_items = all_items_sorted[:100]

    # 5. Output result as Atom feed file
    feed_root = ET.Element("feed", xmlns="http://www.w3.org/2005/Atom")
    ET.SubElement(feed_root, "title").text = "Top 100 Recent YouTube Channel Videos"
    ET.SubElement(feed_root, "id").text = "merged:youtube:subscriptions"
    ET.SubElement(feed_root, "updated").text = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    ns_atom = "http://www.w3.org/2005/Atom"
    for item in top_100_items:
        entry_elem = ET.fromstring(item["entry"])
        channel_name = entry_elem.find(".//{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name").text.strip()
        title_elem = entry_elem.find(".//{http://www.w3.org/2005/Atom}title")
        title =  title_elem.text
        title_elem.text = f"[{channel_name}]{title}"

        feed_root.append(entry_elem)

    merged_feed_xml = ET.tostring(feed_root, encoding="utf-8", xml_declaration=True)
    with open("outputs/feed.xml", "wb") as f:
        f.write(merged_feed_xml)

if __name__ == "__main__":
    main()
