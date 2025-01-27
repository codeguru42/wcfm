import subprocess
from pathlib import Path

import anthropic
import httpx
import typer
from furl import furl

app = typer.Typer()


def fetch_problem(url: str) -> str:
    typer.echo(f"Fetching content from {url} ...", nl=False)
    response = httpx.get(url)
    typer.echo(response.status_code)
    return response.text


def generate_solution(content: str, api_key: str):
    typer.echo("Generating solution...")
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
    return message.content[0].text


def save(script_path: Path, script: str):
    typer.echo(f"Saving script to: {script_path}")
    script_path.parent.mkdir(parents=True, exist_ok=True)
    with open(script_path, "w") as f:
        f.write(script)


def download_input(problem_url: str, input_path: Path, session_token: str):
    input_url = furl(problem_url) / "input"
    typer.echo(
        f"Downloading input from {input_url} and saving to {input_path} ...", nl=False
    )
    response = httpx.get(input_url.url, cookies={"session": session_token})
    typer.echo(response.status_code)
    input_path.parent.mkdir(parents=True, exist_ok=True)
    with open(input_path, "w") as f:
        f.write(response.text)


def execute(python_path: Path, script_path: Path, *args) -> str:
    typer.echo(f"Executing {script_path} ...", nl=False)
    result = subprocess.run(
        [python_path, script_path, *args], capture_output=True, text=True
    )
    typer.echo(result.returncode)
    if result.returncode != 0:
        typer.echo(result.stderr)
    return result.stdout


def parse_url(url: str) -> tuple[int, int]:
    parsed_url = furl(url)
    year = parsed_url.path.segments[0]
    day = parsed_url.path.segments[2]
    return int(year), int(day)


def submit_solution(aoc_url: str, aoc_session_token: str, solution: str, level: int):
    typer.echo(f"Submitting solution to {aoc_url} ...", nl=False)
    parsed_url = furl(aoc_url)
    answer_url = parsed_url / "answer"
    response = httpx.post(
        answer_url.url,
        data={"level": level, "answer": solution},
        cookies={"session": aoc_session_token},
    )
    typer.echo(response.status_code)


@app.command()
def main(
    url: str,
    api_key: str,
    python_path: Path,
    aoc_project_path: Path,
    aoc_session_token: str,
):
    content = fetch_problem(url)
    solution_script = generate_solution(content, api_key)
    year, day = parse_url(url)
    script_path = aoc_project_path / str(year) / f"day{day:02d}.py"
    save(script_path, solution_script)
    input_path = aoc_project_path / str(year) / f"day{day:02d}.txt"
    download_input(url, input_path, aoc_session_token)
    solution = execute(python_path, script_path, input_path)
    typer.echo(f"Solution: {solution}")
    submit_solution(url, aoc_session_token, solution, 1)


if __name__ == "__main__":
    app()
