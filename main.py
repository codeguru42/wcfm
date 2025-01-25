import typer
import requests

app = typer.Typer()

@app.command()
def main(url: str):
    """
    Fetches the content of the given URL and prints the status code.
    """
    response = requests.get(url)
    typer.echo(f"Status Code: {response.status_code}")
    typer.echo(f"Content: {response.text[:200]}...")  # Print first 200 characters

if __name__ == "__main__":
    app()