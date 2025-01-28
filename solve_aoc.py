import subprocess
from pathlib import Path
from time import sleep

import anthropic
import httpx
import typer
from furl import furl

app = typer.Typer()


class SolutionGenerator:
    initial_prompt = """
        Write python code to solve the following problem. Use typer to take a filename as a
        command-line argument. Include appropriate tests in the code. If the tests pass print out 
        only the solution using the given file as input. If the tests fail, print a message and 
        return an exit code of 1. Also print a message in the event of any error.
    """
    messages: list = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": initial_prompt,
                }
            ],
        }
    ]

    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_solution(self, problem_description: str, problem_level: int):
        typer.echo("Generating solution... ")
        if problem_level == 2:
            self.messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Now write python code to solve Part 2.",
                        },
                    ],
                }
            )
        self.messages.append(
            {
                "role": "user",
                "content": [{"type": "text", "text": problem_description}],
            }
        )
        message = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0,
            system="You are an expert software engineer. Respond only with code without markdown formatting. Do not include any comments. Do not generate code to print any output unless directed.",
            messages=self.messages,
        )
        self.messages.append(
            {
                "role": "assistant",
                "content": [{"type": "text", "text": message.content[0].text}],
            }
        )
        return message.content[0].text


def fetch_problem(problem_url: furl) -> str:
    typer.echo(f"Fetching content from {problem_url} ... ", nl=False)
    response = httpx.get(problem_url.url)
    typer.echo(response.status_code)
    return response.text


def save(script_path: Path, script: str):
    typer.echo(f"Saving script to: {script_path}")
    script_path.parent.mkdir(parents=True, exist_ok=True)
    with open(script_path, "w") as f:
        f.write(script)


def download_input(problem_url: furl, input_path: Path, session_token: str):
    input_url = problem_url / "input"
    typer.echo(
        f"Downloading input from {input_url} and saving to {input_path} ... ", nl=False
    )
    response = httpx.get(input_url.url, cookies={"session": session_token})
    typer.echo(response.status_code)
    input_path.parent.mkdir(parents=True, exist_ok=True)
    with open(input_path, "w") as f:
        f.write(response.text)


def execute(python_path: Path, script_path: Path, *args) -> str:
    typer.echo(f"Executing {script_path} ... ", nl=False)
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
    typer.echo(f"Submitting solution to {aoc_url} ... ", nl=False)
    parsed_url = furl(aoc_url)
    answer_url = parsed_url / "answer"
    response = httpx.post(
        answer_url.url,
        data={"level": level, "answer": solution},
        cookies={"session": aoc_session_token},
    )
    typer.echo(response.status_code)


def solve_part(
    generator: SolutionGenerator,
    problem_url: str,
    python_path: Path,
    aoc_project_path: Path,
    aoc_session_token: str,
    input_path: Path,
    year: int,
    day: int,
    problem_level: int,
):
    problem_description = fetch_problem(problem_url)
    solution_script = generator.generate_solution(problem_description, problem_level)
    script_path = aoc_project_path / str(year) / f"day{day:02d}_part{problem_level}.py"
    save(script_path, solution_script)
    solution = execute(python_path, script_path, input_path)
    typer.echo(f"Solution to Part {problem_level}: {solution}")
    submit_solution(problem_url, aoc_session_token, solution, problem_level)


def solve(
    aoc_project_path: Path,
    aoc_session_token: str,
    api_key: str,
    python_path: Path,
    year: int,
    day: int,
):
    problem_url = furl(f"https://adventofcode.com/") / str(year) / "day" / str(day)
    input_path = aoc_project_path / str(year) / f"day{day:02d}.txt"
    download_input(problem_url, input_path, aoc_session_token)
    generator = SolutionGenerator(api_key)
    solve_part(
        generator,
        problem_url,
        python_path,
        aoc_project_path,
        aoc_session_token,
        input_path,
        year,
        day,
        1,
    )
    solve_part(
        generator,
        problem_url,
        python_path,
        aoc_project_path,
        aoc_session_token,
        input_path,
        year,
        day,
        2,
    )
    sleep(8.0)


@app.command()
def main(
    api_key: str,
    python_path: Path,
    aoc_project_path: Path,
    aoc_session_token: str,
):
    year = 2015
    for day in range(1, 26):
        solve(aoc_project_path, aoc_session_token, api_key, python_path, year, day)


if __name__ == "__main__":
    app()
