from pydantic import BaseModel


class EmojiSuggestion(BaseModel):
    emoji: str
    reason: str


class EmojiResult(BaseModel):
    topic: str
    official: list[EmojiSuggestion]
    """Emojis whose official Unicode name/description matches the topic."""
    creative: list[EmojiSuggestion]
    """Emojis commonly used for this topic despite a different official meaning."""
    from_subset: list[EmojiSuggestion]
    """Best matches from the user-supplied or default subset."""
