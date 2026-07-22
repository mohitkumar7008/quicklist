# --- QuickList, containerized ---
# Every line explained in the Day 8 deck -- this file is deliberately short.

FROM python:3.11-slim
# The EXACT Python version this app was built and tested with, guaranteed --
# not "whatever Python happens to be on this machine."

WORKDIR /app
# Everything from here on happens inside /app in the container.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Dependencies copied and installed BEFORE the rest of the code, on purpose:
# Docker caches each layer, so re-running a build after only editing app.py
# skips reinstalling Flask every time -- much faster rebuilds.

COPY . .
# Now the rest of the app: app.py, templates/, etc.

EXPOSE 5000
# Documents which port the app listens on -- doesn't publish it by itself,
# that's still --publish/-p on `docker run`.

CMD ["python", "app.py"]
# The command that runs when the container starts.
