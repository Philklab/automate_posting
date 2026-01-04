import os
from youtube_auth import get_youtube_service

def main():
    video_id = "5S-0ypIrV_w"
    playlist_id = "TON_PLAYLIST_ID_ICI"  # ex: PLxxxxxxxxxxxx

    client_secrets = os.environ["YOUTUBE_CLIENT_SECRETS"]
    token_file = os.environ["YOUTUBE_TOKEN_FILE"]
    yt = get_youtube_service(client_secrets, token_file)

    yt.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        },
    ).execute()

    print("✅ Added to playlist.")

if __name__ == "__main__":
    main()
