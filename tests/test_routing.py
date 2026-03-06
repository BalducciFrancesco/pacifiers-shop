from pacifiershop.routing import ToolChoice, choose_tool


def test_spotify_track_routes_to_spotdl() -> None:
    result = choose_tool("https://open.spotify.com/track/123")
    assert result.tool == ToolChoice.SPOTDL


def test_spotify_playlist_routes_to_spotdl() -> None:
    result = choose_tool("https://open.spotify.com/playlist/abc")
    assert result.tool == ToolChoice.SPOTDL


def test_youtube_video_routes_to_ytdlp() -> None:
    result = choose_tool("https://www.youtube.com/watch?v=xyz")
    assert result.tool == ToolChoice.YTDLP


def test_youtube_playlist_routes_to_ytdlp() -> None:
    result = choose_tool("https://www.youtube.com/playlist?list=PL123")
    assert result.tool == ToolChoice.YTDLP
