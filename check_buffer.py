"""Read-only Buffer connectivity check for ExamBloom GitHub Actions."""
import os
from buffer_publish import connected_channels

def main():
    if not os.getenv("BUFFER_API_KEY", "").strip():
        print("BUFFER_API_KEY has not been saved in GitHub Actions secrets yet.")
        return
    channels = connected_channels()
    print("Buffer authentication succeeded.")
    print("Instagram connected:", "yes" if "instagram" in channels else "no")
    print("TikTok connected:", "yes" if "tiktok" in channels else "no")
    if "instagram" not in channels or "tiktok" not in channels:
        raise SystemExit("Both ExamBloom social channels must be connected before activation.")
    print("Connection check passed. No posts have been published.")

if __name__ == "__main__":
    main()
