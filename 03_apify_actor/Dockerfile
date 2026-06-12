FROM apify/actor-python:3.13

COPY requirements.txt ./
RUN echo "Installing dependencies:" \
    && pip install -U pip \
    && pip install -r requirements.txt \
    && echo "All dependencies installed:" \
    && pip freeze

COPY . ./

CMD ["python", "-m", "src"]
