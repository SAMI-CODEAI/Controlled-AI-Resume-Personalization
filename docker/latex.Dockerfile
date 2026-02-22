FROM texlive/texlive:latest

RUN useradd -m -s /bin/bash latexuser

WORKDIR /output

# Create an entrypoint that compiles LaTeX with no shell escape
COPY docker/latex-entrypoint.sh /usr/local/bin/compile-latex.sh
RUN chmod +x /usr/local/bin/compile-latex.sh

USER latexuser

ENTRYPOINT ["tail", "-f", "/dev/null"]
