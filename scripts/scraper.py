from itertools import chain
import os

from typing import List
from googleapiclient.discovery import build
from datetime import datetime, timedelta


def split_batches(N: int, X: int) -> List[int]:
    """
    Splits N into batches of size X.

    Args:
        N (int): Total size
        X (int): Batch size

    Returns:
        List[int]: List of batch sizes
    """
    quotient, remainder = divmod(N, X)
    return [X] * quotient + ([remainder] if remainder else [])


class YoutubeService:
    def __init__(self, api_key: str):
        self.service = self.build_youtube_service(api_key)

    def build_youtube_service(self, api_key: str):
        """
        Build the YouTube service for API interactions.

        Args:
            api_key (str): API Key

        Returns:
            Resource : Google YouTube Resource object.
        """
        return build("youtube", "v3", developerKey=api_key)

    def search_videos(
        self,
        subject: str,
        maxResults: int,
        publishedAfter: str,
        pageToken: str = None,
    ):
        """
        Search for videos on Youtube.

        Args:
            subject (str): Search term
            maxResults (int): Number of results
            publishedAfter (str): Published after date
            pageToken (str, optional): Page token. Defaults to None.

        Returns:
            Tuple[dict, str]: A tuple of search response and the next page token
        """

        request = self.service.search().list(
            part="snippet",
            maxResults=maxResults,
            q=subject,
            publishedAfter=publishedAfter,
            pageToken=pageToken,
        )

        search_response = request.execute()
        next_page_token = search_response.get("nextPageToken")

        return search_response, next_page_token


def parse_youtube_response(response: dict) -> dict:
    """
    Parse and flatten Youtube response.

    Args:
        response (dict): The Youtube search response.

    Returns:
        dict: The parsed and flattened Youtube response.
    """
    # Base data
    data = response.get("snippet", {})

    # Additional fields
    etag = response.get("etag")
    kind = response.get("kind")
    videoId = response.get("id", {}).get("videoId")
    channelId = data.get("channelId")

    # Flatten the dictionary
    flattened_data = {
        "etag": etag,
        "kind": kind,
        "videoId": videoId,
        "channelId": channelId,
        "publishedAt": data.get("publishedAt"),
        "title": data.get("title"),
        "description": data.get("description"),
        "thumbnails": data.get("thumbnails"),
        "channelTitle": data.get("channelTitle"),
        "liveBroadcastContent": data.get("liveBroadcastContent"),
        "publishTime": data.get("publishTime"),
    }

    # Filter out any keys with None values
    flattened_data = {k: v for k, v in flattened_data.items() if v is not None}

    return flattened_data


def search_youtube(
    subject: str, video_list_size: int, amount_weeks: int
) -> List[dict]:
    """
    Search for videos on Youtube over a certain time period.

    Args:
        subject (str): Search term
        video_list_size (int): Number of videos to retrieve
        amount_weeks (int): Number of weeks back to search

    Returns:
        List[dict]: List of search responses
    """
    week_ago_dt = datetime.now() - timedelta(weeks=amount_weeks)
    week_ago_formatted = week_ago_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    MAX_YOUTUBE_API_RESULTS = 50
    batch_sizes = split_batches(video_list_size, MAX_YOUTUBE_API_RESULTS)

    search_results = []
    youtube_service = YoutubeService(os.getenv("GOOGLE_YOUTUBE_API_KEY"))
    page_token = None

    # Max results per request is 50
    for batch_size in batch_sizes:
        search_response, page_token = youtube_service.search_videos(
            subject, batch_size, week_ago_formatted, page_token
        )
        search_results.append(
            [parse_youtube_response(i) for i in search_response["items"]]
        )

    # Flatten results
    return list(chain(*search_results))
