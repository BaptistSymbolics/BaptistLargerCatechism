# Create the dist directory if it doesn't exist
mkdir -p dist

# Run the new Python script to generate LaTeX directly
python .github/scripts/toml_to_latex.py -s src -o dist/larger-catechism.tex

# First run of xelatex to generate initial PDF and auxiliary files
docker run --rm --volume "$(pwd):/data" --workdir /data texlive/texlive:latest \
  xelatex -interaction=nonstopmode -output-directory=dist dist/larger-catechism.tex

# Second run of xelatex to incorporate table of contents and references
docker run --rm --volume "$(pwd):/data" --workdir /data texlive/texlive:latest \
  xelatex -interaction=nonstopmode -output-directory=dist dist/larger-catechism.tex

cp dist/larger-catechism.pdf final/larger-catechism.pdf