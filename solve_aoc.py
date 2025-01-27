import subprocess
from pathlib import Path

import anthropic
import httpx
import typer
from anthropic.types import Message
from furl import furl

app = typer.Typer()


def fetch_problem(url: str) -> str:
    response = httpx.get(url)
    typer.echo(f"Status Code for URL: {response.status_code}")
    content = response.text
    typer.echo(f"Content from URL: {content[:200]}...")
    return content


def submit(content: str, api_key: str):
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        temperature=0,
        system="You are an expert software engineer. Respond only with code without markdown formatting. Do not include any comments.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """
                            Write python code to solve the following problem. Use typer to take a filename as a
                            command-line argument. Include appropriate tests in the code. If the tests pass print out 
                            only the solution using the given file as input. If the tests fail, print a message and 
                            return an exit code of 1. Also print a message in the event of any error.
                        """,
                    }
                ],
            },
            {"role": "user", "content": [{"type": "text", "text": content}]},
        ],
    )
    return message


def save(script_path: Path, result: Message):
    script_path.parent.mkdir(parents=True, exist_ok=True)
    with open(script_path, "w") as f:
        f.write(result.content[0].text)
        
def download_input(problem_url: str, input_path: Path, session_token: str):
    input_url = furl(problem_url) / "input"
    response = httpx.get(input_url.url, cookies={"session": session_token})
    input_path.parent.mkdir(parents=True, exist_ok=True)
    with open(input_path, "w") as f:
        f.write(response.text)


def execute(python_path: Path, script_path: Path, *args):
    subprocess.run([python_path, script_path, *args])


def parse_url(url: str) -> tuple[int, int]:
    parsed_url = furl(url)
    year = parsed_url.path.segments[0]
    day = parsed_url.path.segments[2]
    return int(year), int(day)


@app.command()
def main(url: str, api_key: str, python_path: Path, aoc_project_path: Path, aoc_session_token: str):
    content = fetch_problem(url)
    result = submit(content, api_key)
    year, day = parse_url(url)
    script_path = aoc_project_path / str(year) / f"day{day:02d}.py"
    save(script_path, result)
    input_path = aoc_project_path / str(year) / f"day{day:02d}.txt"
    download_input(url, input_path, aoc_session_token)
    execute(python_path, script_path, input_path)


if __name__ == "__main__":
    app()
