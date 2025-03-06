# Create the dist directory if it doesn't exist
mkdir -p dist

# Run the new Python script to generate LaTeX directly to the dist folder
python .github/scripts/toml_to_latex.py -s src -o dist/larger-catechism.tex

# Use a Docker image with a LaTeX distribution to compile the TEX file to PDF
docker run --rm --volume "$(pwd):/data" --workdir /data texlive/texlive:latest \
  xelatex -interaction=nonstopmode -output-directory=dist dist/larger-catechism.tex