FROM python:3.12-slim
COPY app/features/coding_test/sandbox.py /sandbox.py
USER 65534:65534
WORKDIR /tmp
CMD ["python", "-I", "/sandbox.py"]
