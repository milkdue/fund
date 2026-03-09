.PHONY: backend-install backend-run backend-test docker-up

backend-install:
	cd backend && pip3 install -r requirements.txt

backend-run:
	cd backend && uvicorn app.main:app --reload --port 8000

backend-test:
	cd backend && python3 -m pytest -q

docker-up:
	cd infra && docker compose up --build
