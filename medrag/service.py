from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .database import connect, log_run
from .providers import LLMProvider
from .retrieval import retrieve


def format_context(evidence: list[dict[str, Any]], max_chars: int = 18_000) -> str:
    blocks, used = [], 0
    for i, item in enumerate(evidence, 1):
        if item["kind"] == "edge":
            block = f"[E{i}: {item['title']} {item['locator']}] {item['source_name']} --{item['relation']}--> {item['target_name']}. Evidence: {item['evidence']}\nSource passage: {item['text']}"
        else:
            block = f"[E{i}: {item['title']} {item['locator']}] {item['text']}"
        if used + len(block) > max_chars:
            break
        blocks.append(block)
        used += len(block)
    return "\n\n---\n\n".join(blocks)


def answer(collection_dir: Path, provider: LLMProvider, query: str, mode: str, k: int = 8, allow_background: bool = True) -> dict[str, Any]:
    evidence = retrieve(collection_dir, query, mode, k)
    if not evidence:
        raise ValueError("no evidence was retrieved; index documents and, for graph mode, build the graph")
    background_rule = (
        "You may add established medical background knowledge, but label it explicitly as Background knowledge and never present it as document-supported."
        if allow_background else "Use only the supplied evidence. If it is insufficient, say so."
    )
    system = f"You are a careful medical education assistant. {background_rule} Cite document-supported claims with [E#]. Do not invent citations."
    prompt = f"QUESTION:\n{query}\n\nRETRIEVAL MODE: {mode}\nGRAPH SCHEMA: medivale_graph_v1 (concept nodes, directed typed edges, document-linked evidence passages)\n\nEVIDENCE:\n{format_context(evidence)}\n\nAnswer accurately and concisely."
    response = provider.generate(prompt, system, 0.1)
    conn = connect(collection_dir / "knowledge.sqlite3")
    run_id = log_run(conn, "answer", mode, provider.name, provider.model, {"query": query, "k": k, "allow_background": allow_background}, evidence, response)
    conn.close()
    return {"run_id": run_id, "mode": mode, "provider": provider.name, "model": provider.model, "answer": response, "evidence": evidence}


def generate_question(collection_dir: Path, provider: LLMProvider, topic: str, mode: str, question_format: str = "basic", k: int = 8) -> dict[str, Any]:
    evidence = retrieve(collection_dir, topic, mode, k)
    if not evidence:
        raise ValueError("no evidence was retrieved")
    system = """You write original, medically accurate one-best-answer assessment items for medical education.
Follow NBME item-writing principles and the supplied MedVale quality specification, but never copy or closely
paraphrase published NBME, USMLE, or UWorld questions. Return JSON only. The keyed answer and tested
relationship must be supported by the supplied evidence. Established background knowledge may add clinical
realism and explain distractors, but it must not contradict the evidence or create a second defensible answer."""
    prompt = f'''Create one {question_format} clinical multiple-choice question about: {topic}
Use retrieval mode: {mode}
Graph schema: medivale_graph_v1 (concept nodes, directed typed edges, document-linked evidence passages)
Return exactly {json.dumps({"stem": "100-150 word original clinical vignette", "lead_in": "focused closed question", "choices": [{"id": "A", "text": "short homogeneous option", "explanation": "why correct or incorrect"}, {"id": "B", "text": "...", "explanation": "..."}, {"id": "C", "text": "...", "explanation": "..."}, {"id": "D", "text": "...", "explanation": "..."}, {"id": "E", "text": "...", "explanation": "..."}], "correct_choice_id": "A", "explanation": "integrated correct-answer reasoning using key clues", "educational_objective": "one sentence", "clinical_task": "diagnosis|test|management|mechanism|prognosis", "reasoning_order": "first_order|second_order|third_order", "answer_choice_category": "diagnoses|tests|treatments|mechanisms|findings|complications", "common_trap": "the tempting error", "key_discriminator": "the clue that separates the best answer", "teacher_note": "brief mental model and exam trap", "evidence_ids": ["E1"]})}

Requirements:
- Test application of knowledge through a realistic patient vignette, generally 100-150 words, ordered as demographics/site, history, examination, studies, and treatment/course when relevant.
- Ask one important clinical decision. Use a focused, positive, closed lead-in that can be answered before viewing the options.
- Provide exactly five concise, parallel, homogeneous, clinically plausible choices with exactly one best answer.
- Avoid negative phrasing, trivia, vague frequency terms, absolute terms, option overlap, clang clues, convergence, grammatical cues, and a uniquely long keyed answer.
- Use multiple converging clues rather than one giveaway buzzword. Add only clinically useful or realistic details; avoid stereotypes and demographic cueing.
- Distinguish initial step, next best step, most accurate test, definitive treatment, prevention, and contraindication precisely.
- Explain why the keyed answer is best and give a specific explanation for every incorrect choice.
- Cite evidence IDs supporting the keyed answer and educational objective. Do not reveal the answer in the stem or lead-in.

EVIDENCE:
{format_context(evidence)}'''
    question = provider.generate_json(prompt, system, 0.1)
    if not isinstance(question, dict):
        raise ValueError("question response must be a JSON object")
    choices = question.get("choices")
    if not isinstance(choices, list) or len(choices) != 5 or not all(isinstance(choice, dict) for choice in choices):
        raise ValueError("question response must contain exactly five structured choices")
    choice_ids = {str(choice.get("id", "")).strip() for choice in choices}
    correct_id = str(question.get("correct_choice_id", "")).strip()
    required = ("stem", "lead_in", "explanation", "educational_objective", "teacher_note", "key_discriminator")
    if any(not str(question.get(field, "")).strip() for field in required):
        raise ValueError("question response is missing required NBME-style fields")
    if choice_ids != {"A", "B", "C", "D", "E"} or correct_id not in choice_ids or any(not str(choice.get("text", "")).strip() or not str(choice.get("explanation", "")).strip() for choice in choices):
        raise ValueError("question response has an invalid answer key or missing choice explanation")
    response_text = json.dumps(question, ensure_ascii=False)
    conn = connect(collection_dir / "knowledge.sqlite3")
    run_id = log_run(conn, "question", mode, provider.name, provider.model, {"topic": topic, "format": question_format, "k": k}, evidence, response_text)
    conn.close()
    return {"run_id": run_id, "mode": mode, "provider": provider.name, "model": provider.model, "question": question, "evidence": evidence}
