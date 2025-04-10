import json
from typing import Final

import cohere as co
from decouple import config

from texts.enums import GeneratedTextDifficulty

GENERATE_PASSAGE_INSTRUCTION: Final[str] = (
    "Generate an English passage that contains words or phrases that a native Spanish "
    "speaker would find challenging to pronounce. "
    "The passage should consist of between 2 and 5 sentences. "
    "The sentences in the passage should form a coherent story or conversation. "
    "Do not mention language learning or linguistics in the passage. "
    "Format the passage as a bulleted list of sentences. "
    "Each sentence should have a sublist that explains the challenging parts in the "
    "sentence."
)

EXAMPLE_GENERATED_PASSAGE: Final[str] = """
- The tornado from yesterday damaged the house quite a bit.
  - Consonant cluster with /ɹ/: "tornado"
  - Reduced word: "a" should reduce to [ə]
  - Short vowel: "bit" might be mispronounced as [bit] instead of [bɪt]
- First, we need to fix the roof before the rain starts.
  - Final consonant cluster: "first", "fixed", "starts" may lose final sounds
  - /ɹ/ sound: "roof", "rain" → tricky for Spanish speakers (often too trilled or tapped)
  - Reduced words: "to", "the" should reduce to [tə], [ðə]
- Then, we need to remove the debris from the backyard.
- Do you think we can get this done within four days?
"""


class CohereGenerationError(Exception):
    pass


def generate_passage(
    description: str, difficulty: GeneratedTextDifficulty
) -> list[str]:
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
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "justification": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["sentence", "justification"],
                },
            },
        },
    )

    if response.finish_reason != "COMPLETE":
        raise CohereGenerationError("Failed to complete passage generation")

    return [
        sentence["text"] for sentence in json.loads(response.message.content[0].text)
    ]
