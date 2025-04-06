import cohere as co
from dotenv import load_dotenv


def main():
    prompt = """
    ## Instructions
    Generate an English passage that contains words or phrases that a native Spanish speaker would find challenging to
    pronounce. The passage should consist of between 2 and 5 sentences. The sentences in the passage should form a
    coherent story or conversation. Do not mention language learning or linguistics in the passage. Format the passage
    as a bulleted list of sentences. Each sentence should have a sublist that explains the challenging parts in the
    sentence.
    ## Example Output
    - The tornado from yesterday damaged the house quite a bit.
      - Consonant cluster with /ɹ/: tornado
      - Reduced word: "a" should reduce to [ə]
      - Short vowel: "bit" might be mispronounced as [bit] instead of [bɪt]
    - First, we need to fix the roof before the rain starts.
      - Final consonant cluster: "first", "fixed", "starts" may lose final sounds
      - /ɹ/ sound: "roof", "rain" → tricky for Spanish speakers (often too trilled or tapped)
      - Reduced words: "to", "the" should reduce to [tə], [ðə]
    - Then, we need to remove the debris from the backyard.
    - Do you think we can get this done within four days?
    """

    client = co.ClientV2()

    response = client.chat(
        model="command-a-03-2025",
        messages=[{"role": "user", "content": prompt}],
        seed=39,
    )

    print(response.message.content[0].text)


if __name__ == "__main__":
    load_dotenv()
    main()
