"""Tests for the markdown transcript parser."""

from app.services.parser import parse_markdown_transcript


def test_basic_speaker_pattern():
    content = """
**Interviewer:** Tell me about your experience.
**Participant:** I've been using the product for about three months.
**Interviewer:** And what was your first impression?
**Participant:** It was confusing at first, I didn't know where to start.
"""
    turns = parse_markdown_transcript(content)
    assert len(turns) == 4
    assert turns[0].speaker == "Interviewer"
    assert turns[0].is_interviewer is True
    assert turns[1].speaker == "Participant"
    assert turns[1].is_interviewer is False
    assert "three months" in turns[1].text


def test_timestamped_turns():
    content = """
[00:00:12] Interviewer: Let's get started.
[00:00:30] Sarah: Sure, thanks for having me.
[00:01:15] Interviewer: Can you walk me through a typical day?
[00:01:45] Sarah: I usually start by opening the dashboard.
"""
    turns = parse_markdown_transcript(content)
    assert len(turns) == 4
    assert turns[0].timestamp == "00:00:12"
    assert turns[1].speaker == "Sarah"
    assert turns[1].timestamp == "00:00:30"
    assert turns[3].timestamp == "00:01:45"


def test_multiline_response():
    content = """
Interviewer: Tell me more.
Participant: Well, it started when I first logged in.
I didn't really know what to do.
So I just clicked around randomly.

Interviewer: What happened next?
"""
    turns = parse_markdown_transcript(content)
    assert len(turns) == 3
    # Participant turn should accumulate multiline text
    assert "clicked around randomly" in turns[1].text
    assert "I didn't really know" in turns[1].text


def test_standalone_timestamp():
    content = """
0:05
Moderator: How would you describe the experience?
0:12
Participant: It was frustrating.
"""
    turns = parse_markdown_transcript(content)
    assert len(turns) == 2
    assert turns[0].timestamp == "00:00:05"
    assert turns[0].is_interviewer is True  # moderator
    assert turns[1].timestamp == "00:00:12"


def test_empty_input():
    assert parse_markdown_transcript("") == []
    assert parse_markdown_transcript("# Header\n---\n") == []


def test_skips_markdown_headers():
    content = """
# Session 3 Transcript

---

Interviewer: Hello.
Participant: Hi there.
"""
    turns = parse_markdown_transcript(content)
    assert len(turns) == 2
