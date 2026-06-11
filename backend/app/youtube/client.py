from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings


class YouTubeAPIError(RuntimeError):
    pass


class YouTubeQuotaError(YouTubeAPIError):
    pass


class YouTubeTransientError(YouTubeAPIError):
    pass


RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
MAX_RETRIES = 3
BASE_BACKOFF = 2.0


@dataclass(frozen=True)
class YouTubeClient:
    api_key: str = settings.youtube_api_key
    base_url: str = "https://www.googleapis.com/youtube/v3"

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        merged = {**params, "key": self.api_key}
        url = f"{self.base_url}/{path}"

        last_exc: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                with httpx.Client(timeout=30) as client:
                    response = client.get(url, params=merged)
            except httpx.TimeoutException as exc:
                last_exc = YouTubeTransientError(f"YouTube API timeout on {path}: {exc}")
                if attempt < MAX_RETRIES:
                    time.sleep(BASE_BACKOFF ** attempt)
                continue
            except httpx.RequestError as exc:
                raise YouTubeAPIError(f"YouTube API request failed: {exc}") from exc

            if response.status_code == 403:
                raise YouTubeQuotaError(f"YouTube API quota error {response.status_code}: {response.text}")
            if response.status_code in RETRYABLE_STATUSES:
                if attempt < MAX_RETRIES:
                    time.sleep(BASE_BACKOFF ** attempt)
                    continue
                raise YouTubeTransientError(
                    f"YouTube API error after {MAX_RETRIES} retries: {response.status_code}: {response.text}"
                )
            if response.status_code >= 400:
                raise YouTubeAPIError(f"YouTube API error {response.status_code}: {response.text}")

            return response.json()

        raise YouTubeAPIError(f"YouTube API request failed after {MAX_RETRIES} retries") from last_exc

    def get_channel(self, *, channel_id: str | None = None, handle: str | None = None) -> dict[str, Any]:
        if not channel_id and not handle:
            raise ValueError("channel_id or handle is required")
        params: dict[str, Any] = {
            "part": "snippet,statistics,contentDetails",
            "maxResults": 1,
        }
        if channel_id:
            params["id"] = channel_id
        else:
            params["forHandle"] = handle
        data = self._get("channels", params)
        items = data.get("items", [])
        if not items:
            raise YouTubeAPIError("Channel not found")
        return items[0]

    def list_upload_playlist_video_ids(self, uploads_playlist_id: str, *, limit: int = 50) -> list[str]:
        video_ids, _ = self.list_upload_playlist_video_ids_with_request_count(
            uploads_playlist_id, limit=limit
        )
        return video_ids

    def list_upload_playlist_video_ids_with_request_count(
        self, uploads_playlist_id: str, *, limit: int = 50
    ) -> tuple[list[str], int]:
        video_ids: list[str] = []
        page_token: str | None = None
        request_count = 0
        while len(video_ids) < limit:
            params: dict[str, Any] = {
                "part": "snippet,contentDetails",
                "playlistId": uploads_playlist_id,
                "maxResults": min(50, limit - len(video_ids)),
            }
            if page_token:
                params["pageToken"] = page_token
            data = self._get("playlistItems", params)
            request_count += 1
            for item in data.get("items", []):
                video_id = item.get("contentDetails", {}).get("videoId") or item.get("snippet", {}).get(
                    "resourceId", {}
                ).get("videoId")
                if video_id:
                    video_ids.append(video_id)
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return video_ids, request_count

    def get_videos(self, video_ids: list[str]) -> list[dict[str, Any]]:
        videos, _ = self.get_videos_with_request_count(video_ids)
        return videos

    def get_videos_with_request_count(self, video_ids: list[str]) -> tuple[list[dict[str, Any]], int]:
        if not video_ids:
            return [], 0
        videos: list[dict[str, Any]] = []
        request_count = 0
        for start in range(0, len(video_ids), 50):
            chunk = video_ids[start : start + 50]
            data = self._get(
                "videos",
                {
                    "part": "snippet,statistics,contentDetails,status",
                    "id": ",".join(chunk),
                    "maxResults": 50,
                },
            )
            request_count += 1
            videos.extend(data.get("items", []))
        return videos, request_count