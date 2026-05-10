export interface YTVideo {
  videoId: string;
  title: string;
  channel: string;
  thumbnail: string;
  url: string;
}

export async function searchYouTube(query: string): Promise<YTVideo | null> {
  const key = process.env.NEXT_PUBLIC_YOUTUBE_API_KEY;
  if (!key) return null;

  const params = new URLSearchParams({
    part: "snippet",
    q: `${query} explained`,
    type: "video",
    videoDuration: "medium",
    maxResults: "1",
    key,
  });

  try {
    const res = await fetch(`https://www.googleapis.com/youtube/v3/search?${params}`);
    if (!res.ok) return null;
    const data = await res.json();
    const item = data.items?.[0];
    if (!item) return null;
    const videoId = item.id.videoId;
    return {
      videoId,
      title: item.snippet.title,
      channel: item.snippet.channelTitle,
      thumbnail: item.snippet.thumbnails.medium?.url ?? item.snippet.thumbnails.default?.url,
      url: `https://www.youtube.com/watch?v=${videoId}`,
    };
  } catch {
    return null;
  }
}
