import anthropic
import typer
import httpx

app = typer.Typer()

DEFAULT_GITHUB_COPILOT_URL = "https://api.github.com/copilot/submit"


def fetch_url(url: str) -> str:
    response = httpx.get(url)
    typer.echo(f"Status Code for URL: {response.status_code}")
    content = response.text
    typer.echo(f"Content from URL: {content[:200]}...")
    return content


def submit(content: str, github_copilot_url: str, api_key: str):
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        temperature=0,
        system="You are a export software engineer. Respond only with code without markdown formatting.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Write python code to solve the following problem",
                    }
                ],
            },
            {"role": "user", "content": [{"type": "text", "text": content}]},
        ],
    )
    return message


def save(filename, result):
    with open(filename, "w") as f:
        f.write(result.content[0].text)


@app.command()
def main(
    url: str, llm_url: str = DEFAULT_GITHUB_COPILOT_URL, api_key: str = typer.Argument()
):
    content = fetch_url(url)
    result = submit(content, llm_url, api_key)
    save("aoc.py", result)


if __name__ == "__main__":
    app()
