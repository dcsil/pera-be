import json
from typing import Final

import cohere as co
from decouple import config

GENERATE_PASSAGE_INSTRUCTION: Final[str] = (
    "Generate a JSON that contains an English passage between 2 and 5 sentences in "
    "length. "
    "The passage should contains words and phrases that a native Spanish speaker would "
    "find challenging to pronounce. "
    "The passage should form a coherent story or conversation that is related to the "
    "below passage description. "
    "Set the difficulty of the passage according to the below numerical difficulty"
    "value, where 0 means minimal difficulty and 10 means extremely difficult. "
    "Do not mention language learning or linguistics in the passage. "
    "Format the passage as a list of sentences, and explain why parts of each sentence "
    "would be difficult to pronounce for a native Spanish speaker."
)

EXAMPLE_GENERATED_PASSAGE: Final[str] = """
[{
    "text": "The tornado from yesterday damaged the house quite a bit.",
    "justification": [
        "Consonant cluster with /ɹ/: 'tornado'",
        "Reduced word: 'a' should reduce to [ə]",
        "Short vowel: 'bit' might be mispronounced as [bit] instead of [bɪt]"
    ]
},
{
    "text": "First, we need to fix the roof before the rain starts.",
    "justification": [
        "Final consonant cluster: 'first', 'fixed', 'starts' may lose final sounds",
        "/ɹ/ sound: 'roof', 'rain' → tricky for Spanish speakers (often too trilled or tapped)",
        "Reduced words: 'to', 'the' should reduce to [tə], [ðə]"
    ]
}]
"""


class CohereGenerationError(Exception):
    pass


def generate_passage(description: str, difficulty: int) -> str:
    client = co.ClientV2(api_key=config("CO_API_KEY"))

    prompt = f"""
    ## Instructions
    {GENERATE_PASSAGE_INSTRUCTION}
    ## Example Output
    {EXAMPLE_GENERATED_PASSAGE}
    ## Passage Description
    {description}
    ## Difficulty
    {str(difficulty)}
    """

    response = client.chat(
        model="command-a-03-2025",
        messages=[{"role": "user", "content": prompt}],
        response_format={
            "type": "json_object",
            "schema": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "justification": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": ["text", "justification"],
                        },
                    }
                },
                "required": ["content"],
            },
        },
        safety_mode="STRICT",
    )

    if response.finish_reason != "COMPLETE":
        raise CohereGenerationError("Failed to complete passage generation")

    return " ".join(
        sentence["text"].strip()
        for sentence in json.loads(response.message.content[0].text)["content"]
    )
