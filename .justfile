set dotenv-load

set windows-shell := ["cmd.exe", "/c"]
set shell := ["bash", "-c"]


recipe-name:
  echo 'This is a recipe!'

# this is a comment
another-recipe:
  @echo 'This is another recipe.'

build:
    docker compose build

[linux]
printenv:
    echo foobar $GDAL_LIBRARY_PATH

[windows]
printenv:
    @echo bla %GDAL_LIBRARY_PATH%

[working-directory: "backend"]
scrape:
    python manage.py run_scraper

[working-directory: "backend"]
geocode:
    python manage.py geocode