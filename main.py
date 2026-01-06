from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_spotify_top200(output_csv="spotify_top200.csv", headless=True):
    """Scrape Spotify Global Top 200 chart from kworb.net with Artist/Song split."""
    url = "https://kworb.net/spotify/country/global_daily.html"
    print(f"🌍 Starting scraper for: {url}")

    # Setup Chrome
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")

    service = Service()  # assumes chromedriver is in PATH
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    table = soup.find("table")
    if not table:
        print("⚠️ Could not find chart table. The site layout may have changed.")
        return

    data = []
    rows = table.find_all("tr")[1:]  # skip header

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        try:
            # Rank
            rank = cols[0].get_text(strip=True)

            # Movement (= means 0)
            movement = cols[1].get_text(strip=True)
            if movement == "=":
                movement = "0"

            # The column with Artist - Song combined
            combined_text = cols[2].get_text(strip=True)
            # Split only at the first hyphen
            if "-" in combined_text:
                artist, song = combined_text.split("-", 1)
                artist = artist.strip()
                song = song.strip()
            else:
                artist = combined_text.strip()
                song = ""

            # Streams
            streams_text = cols[4].get_text(strip=True).replace(",", "")
            streams = int(streams_text) if streams_text.isdigit() else None

            # Spotify URL
            href_tag = cols[2].find("a")
            spotify_url = "N/A"
            if href_tag and "href" in href_tag.attrs:
                href = href_tag["href"]
                if href.startswith("../track/"):
                    track_id = href.split("/")[-1].replace(".html", "")
                    spotify_url = f"https://open.spotify.com/track/{track_id}"
                elif href.startswith("../artist/"):
                    artist_id = href.split("/")[-1].replace(".html", "")
                    spotify_url = f"https://open.spotify.com/artist/{artist_id}"

            data.append({
                "Rank": rank,
                "Movement": movement,
                "Artist": artist,
                "Song": song,
                "Streams": streams,
                "Spotify_URL": spotify_url
            })

        except Exception as e:
            print(f"⚠️ Skipped one row due to error: {e}")
            continue

    # Save to CSV
    if data:
        df = pd.DataFrame(data)
        df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        print(f"✅ Successfully scraped {len(df)} songs and saved to '{output_csv}'")
    else:
        print("⚠️ No data scraped.")

if __name__ == "__main__":
    scrape_spotify_top200("spotify_top200.csv", headless=True)
