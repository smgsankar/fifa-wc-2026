# Dev server orchestration for the FIFA WC 2026 app.
#
#   make            # start both servers (alias for `make dev`)
#   make dev        # start backend + frontend together (parallel)
#   make backend    # start only the FastAPI backend
#   make frontend   # start only the Vite frontend
#
# Each server target first frees its port, killing any stale process
# still listening there, so you never hit "address already in use".

BACKEND_PORT  ?= 8000
FRONTEND_PORT ?= 5173
BACKEND_DIR   ?= backend
FRONTEND_DIR  ?= frontend

.DEFAULT_GOAL := dev
.PHONY: dev backend frontend

# Start both dev servers in parallel. Each server runs in the foreground
# forever, so we recurse with `-j2` to run the two independent targets
# concurrently (plain prerequisites would run serially and block).
dev:
	@$(MAKE) -j2 backend frontend

backend:
	@PIDS=$$(lsof -ti tcp:$(BACKEND_PORT)); \
	if [ -n "$$PIDS" ]; then \
		echo "Freeing port $(BACKEND_PORT) (PID $$PIDS)"; \
		kill -9 $$PIDS; \
	fi
	cd $(BACKEND_DIR) && .venv/bin/uvicorn main:app --reload --port $(BACKEND_PORT)

frontend:
	@PIDS=$$(lsof -ti tcp:$(FRONTEND_PORT)); \
	if [ -n "$$PIDS" ]; then \
		echo "Freeing port $(FRONTEND_PORT) (PID $$PIDS)"; \
		kill -9 $$PIDS; \
	fi
	cd $(FRONTEND_DIR) && npm run dev -- --port $(FRONTEND_PORT) --strictPort
