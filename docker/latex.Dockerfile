FROM texlive/texlive:latest

# Install additional packages commonly used in modern resumes
# Note: texlive:latest is large but ensures maximum compatibility
RUN tlmgr update --self && \
    tlmgr install \
    enumitem \
    titlesec \
    xcolor \
    geometry \
    hyperref \
    fontawesome5 \
    sourcesanspro \
    tcolorbox \
    environ \
    trimspaces

RUN useradd -m -s /bin/bash latexuser

WORKDIR /output

# No entrypoint needed for 'tail -f' unless we want to keep it alive
USER latexuser

ENTRYPOINT ["tail", "-f", "/dev/null"]
