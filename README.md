# Lab 16 — Reflexion Agent Scaffold

Repo này cung cấp một khung sườn (scaffold) để xây dựng và đánh giá **Reflexion Agent**.

## 1. Mục tiêu của Repo
- Repo hiện tại có chế độ **Mock** (`mock_runtime.py`) để giả lập phản hồi từ LLM.
- Phiên bản hoàn thiện cần chạy được với **LLM thật** (OpenAI hoặc backend tương thích).
- Mục đích giúp học viên hiểu rõ flow, các bước loop, cơ chế reflection và cách benchmark/evaluation.

## 2. Nhiệm vụ của Học viên
1. **Xây dựng Agent thật**: Thay mock bằng LLM runtime thật.
2. **Chạy Benchmark thực tế**: Chạy đánh giá trên ít nhất **100 mẫu dữ liệu thật** từ HotpotQA.
3. **Định dạng báo cáo**: Xuất `report.json` và `report.md` đúng format.
4. **Token thực tế**: Lấy token usage thật từ phản hồi API.

## 3. Cách chạy
```bash
# Cài môi trường
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Cấu hình OpenAI
cat > .env << 'ENV'
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
OPENAI_BASE_URL=https://api.openai.com/v1
ENV

# (Khuyến nghị) tải 100 mẫu HotpotQA thật
python data/prepare_hotpot_subset.py --size 100 --out data/hotpot_100.json

# Chạy benchmark với OpenAI runtime
python run_benchmark.py --dataset data/hotpot_100.json --runtime-mode openai --max-examples 100 --out-dir outputs/hotpot_openai

# Chạy benchmark nhanh bằng mini dataset (debug)
python run_benchmark.py --dataset data/hotpot_mini.json --runtime-mode openai --max-examples 8 --out-dir outputs/mini_openai

# Chấm điểm tự động
python autograde.py --report-path outputs/hotpot_openai/report.json
```

## 4. Tiêu chí chấm điểm (Rubric)
- **80 điểm**: Đúng flow Reflexion Agent, benchmark đủ dữ liệu, report đúng schema.
- **20 điểm bonus**: Extension phù hợp (`structured_evaluator`, `reflection_memory`, `adaptive_max_attempts`, ...).

## Thành phần mã nguồn
- `src/reflexion_lab/schemas.py`: Kiểu dữ liệu trace/record.
- `src/reflexion_lab/prompts.py`: Prompt cho Actor/Evaluator/Reflector.
- `src/reflexion_lab/mock_runtime.py`: Runtime mock cho debug.
- `src/reflexion_lab/llm_runtime.py`: Runtime OpenAI thật.
- `src/reflexion_lab/agents.py`: Logic ReAct và Reflexion loop.
- `src/reflexion_lab/reporting.py`: Tổng hợp benchmark và xuất report.
- `run_benchmark.py`: Script chạy benchmark.
- `autograde.py`: Script chấm điểm report.
