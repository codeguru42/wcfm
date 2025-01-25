import typer
import requests

app = typer.Typer()


@app.command()
def main(url: str):
    response = requests.get(url)
    typer.echo(f"Status Code: {response.status_code}")
    typer.echo(f"Content: {response.text[:200]}...")


if __name__ == "__main__":
    app()
