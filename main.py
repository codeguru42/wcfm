import typer
import httpx

app = typer.Typer()


@app.command()
def main(url: str):
    response = httpx.get(url)
    typer.echo(f"Status Code: {response.status_code}")
    typer.echo(f"Content: {response.text[:200]}...")


if __name__ == "__main__":
    app()
