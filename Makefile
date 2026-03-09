# ============================================================================
# Makefile - NLP Practice 개발 자동화
# Python 3.12+ 프로젝트용
# ============================================================================
# 사용법:
#   make help           - 사용 가능한 명령어 목록
#   make install-dev    - 개발 환경 설치 (권장)
#   make lint           - 코드 품질 검사
#   make format         - 코드 자동 포매팅
#   make check          - 전체 검사
#   make commit         - 대화형 커밋 생성
# ============================================================================

COLOR_RESET  := \033[0m
COLOR_BOLD   := \033[1m
COLOR_GREEN  := \033[32m
COLOR_YELLOW := \033[33m
COLOR_BLUE   := \033[34m
COLOR_CYAN   := \033[36m

VENV         := .venv
VENV_BIN     := $(VENV)/bin
PIP          := $(VENV_BIN)/pip
PYTHON_VENV  := $(VENV_BIN)/python

SRC_DIR      := src
ALL_DIRS     := $(SRC_DIR)

RUFF         := $(VENV_BIN)/ruff
PRE_COMMIT   := $(VENV_BIN)/pre-commit
COMMITIZEN   := $(VENV_BIN)/cz

.DEFAULT_GOAL := help

.PHONY: help install install-dev install-hooks clean lint format \
        check commit bump-version pre-commit run-all update-hooks

# ============================================================================
help:
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)사용 가능한 Make 명령어:$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_GREEN)설치 관련:$(COLOR_RESET)"
	@echo "  make install         - 프로덕션 환경 설치"
	@echo "  make install-dev     - 개발 환경 전체 설치 (권장)"
	@echo "  make install-hooks   - Git 훅 설치"
	@echo "  make clean           - 임시 파일 및 캐시 삭제"
	@echo ""
	@echo "$(COLOR_GREEN)코드 품질:$(COLOR_RESET)"
	@echo "  make lint            - 코드 품질 검사 (자동 수정)"
	@echo "  make format          - 코드 포매팅 (자동 정리)"
	@echo ""
	@echo "$(COLOR_GREEN)통합 명령어:$(COLOR_RESET)"
	@echo "  make check           - 전체 검사 (lint+format)"
	@echo "  make pre-commit      - pre-commit 훅 수동 실행"
	@echo "  make run-all         - 모든 파일에 pre-commit 실행"
	@echo ""
	@echo "$(COLOR_GREEN)Git 관련:$(COLOR_RESET)"
	@echo "  make commit          - 대화형 커밋 생성 (Conventional Commits)"
	@echo "  make bump-version    - 버전 자동 증가 및 태그 생성"
	@echo ""
	@echo "$(COLOR_GREEN)유지보수:$(COLOR_RESET)"
	@echo "  make update-hooks    - pre-commit 훅 업데이트"
	@echo ""

# ============================================================================
install:
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)프로덕션 환경 설치 중...$(COLOR_RESET)"
	@test -d $(VENV) || $(PYTHON_VENV) -m venv $(VENV)
	@$(PIP) install --upgrade pip setuptools wheel
	@$(PIP) install -e .
	@echo "$(COLOR_GREEN)✓ 설치 완료$(COLOR_RESET)"

# ============================================================================
install-dev:
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)개발 환경 설치 중...$(COLOR_RESET)"
	@$(PIP) install --upgrade pip setuptools wheel
	@$(PIP) install -e ".[dev]"
	@$(MAKE) install-hooks
	@echo "$(COLOR_GREEN)✓ 개발 환경 설치 완료$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)환경 활성화: source $(VENV)/bin/activate$(COLOR_RESET)"

# ============================================================================
install-hooks:
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)Git 훅 설치 중...$(COLOR_RESET)"
	@$(PRE_COMMIT) install
	@$(PRE_COMMIT) install --hook-type commit-msg
	@echo "$(COLOR_GREEN)✓ Git 훅 설치 완료$(COLOR_RESET)"

# ============================================================================
clean:
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)임시 파일 삭제 중...$(COLOR_RESET)"
	@find . -type d -name "__pycache__" -not -path "./.venv/*" -not -path "./python_template/*" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -not -path "./.venv/*" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache .ruff_cache build dist 2>/dev/null || true
	@echo "$(COLOR_GREEN)✓ 정리 완료$(COLOR_RESET)"

# ============================================================================
lint:
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)코드 품질 검사 중...$(COLOR_RESET)"
	@$(RUFF) check $(ALL_DIRS) --fix
	@echo "$(COLOR_GREEN)✓ 린트 검사 완료$(COLOR_RESET)"

# ============================================================================
format:
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)코드 포매팅 중...$(COLOR_RESET)"
	@$(RUFF) format $(ALL_DIRS)
	@echo "$(COLOR_GREEN)✓ 포매팅 완료$(COLOR_RESET)"

# ============================================================================
check: lint format
	@echo ""
	@echo "$(COLOR_BOLD)$(COLOR_GREEN)========================================$(COLOR_RESET)"
	@echo "$(COLOR_BOLD)$(COLOR_GREEN)  ✓ 모든 검사 통과!$(COLOR_RESET)"
	@echo "$(COLOR_BOLD)$(COLOR_GREEN)========================================$(COLOR_RESET)"
	@echo ""

# ============================================================================
pre-commit:
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)Pre-commit 훅 실행 중...$(COLOR_RESET)"
	@$(PRE_COMMIT) run

# ============================================================================
run-all:
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)모든 파일에 Pre-commit 실행 중...$(COLOR_RESET)"
	@$(PRE_COMMIT) run --all-files

# ============================================================================
commit:
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)대화형 커밋 생성...$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_YELLOW)커밋 타입: feat / fix / docs / refactor / perf / chore$(COLOR_RESET)"
	@echo ""
	@$(COMMITIZEN) commit

# ============================================================================
bump-version:
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)버전 자동 증가 중...$(COLOR_RESET)"
	@$(COMMITIZEN) bump --yes
	@echo "$(COLOR_GREEN)✓ 버전 업데이트 완료$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)푸시: git push --follow-tags$(COLOR_RESET)"

# ============================================================================
update-hooks:
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)Pre-commit 훅 업데이트 중...$(COLOR_RESET)"
	@$(PRE_COMMIT) autoupdate
	@echo "$(COLOR_GREEN)✓ 훅 업데이트 완료$(COLOR_RESET)"
