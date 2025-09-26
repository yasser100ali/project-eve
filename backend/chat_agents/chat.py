import json 
import time
import logging 
import os
import re
import csv
import requests
from io import BytesIO, StringIO
from typing import List, Any, Dict, AsyncIterator
from dotenv import load_dotenv
from agents import Agent, Runner, WebSearchTool, CodeInterpreterTool
import PyPDF2

# subagent
from .lawyer_and_plantiff_agents import plaintiffAgent, lawyerAgent


logger = logging.getLogger(__name__)

def extract_pdf_text(url: str) -> str:
    """Extract text from PDF file"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        pdf_file = BytesIO(response.content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
            
        return text.strip()
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        return f"[Error reading PDF: {str(e)}]"

def extract_tabular_data(url: str, media_type: str) -> str:
    """Extract data from CSV or Excel-like files"""
    try:
        response = requests.get(url)
        response.raise_for_status()

        if media_type == 'text/csv':
            decoded = response.content.decode('utf-8', errors='ignore')
            reader = csv.reader(StringIO(decoded))
            rows = []
            for idx, row in enumerate(reader):
                rows.append(', '.join(cell.strip() for cell in row))
                if idx >= 99:
                    rows.append('...')
                    break
            return '\n'.join(rows) if rows else '[CSV contained no rows]'

        return (
            '[Preview unavailable for non-CSV spreadsheet formats. '
            'Download the file to inspect its contents.]'
        )
    except Exception as e:
        logger.error(f"Error extracting tabular data: {e}")
        return f"[Error reading tabular data: {str(e)}]"

def process_file_content(content: str) -> str:
    """Process message content and extract file contents"""
    # Pattern to match file references: [File: filename (mediaType) - URL: url]
    file_pattern = r'\[File: ([^(]+) \(([^)]+)\) - URL: ([^\]]+)\]'
    
    def replace_file_ref(match):
        filename = match.group(1).strip()
        media_type = match.group(2).strip()
        url = match.group(3).strip()
        
        if media_type == 'application/pdf':
            file_content = extract_pdf_text(url)
            return f"[PDF File: {filename}]\n{file_content}\n[End of PDF]"
        elif media_type in [
            'text/csv',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        ]:
            file_content = extract_tabular_data(url, media_type)
            return f"[Tabular File: {filename}]\n{file_content}\n[End of Tabular File]"
        else:
            return f"[File: {filename} ({media_type}) - Content not processed]"
    
    return re.sub(file_pattern, replace_file_ref, content)



def to_agent_messages(history: List[Dict[str, Any]]):
    msgs = []
    for m in history:
        role = m.get("role", "user").lower()
        text = str(m.get("content", ""))
        
        # Process file content if present
        processed_text = process_file_content(text)

        if role == "system":
            msgs.append({"content": processed_text, "role": "developer", "type": "message"})
        elif role == "assistant":
            msgs.append({"content": processed_text, "role": "assistant", "type": "message"})
        else:
            msgs.append({"content": processed_text, "role": "user", "type": "message"})

    return msgs

async def stream_chat_py(
    messages: List[Dict[str, Any]],
    selected_chat_mode: str,
    request_hints: Dict[str, Any] | None 
) -> AsyncIterator[str]:

    start_time = time.time()

    code_tool = CodeInterpreterTool(
        tool_config={"type": "code_interpreter", "container": {"type": "auto"}}
    )
    
    instructions = """
    You are part of a full-stack demo built by AI Engineer **Yasser Ali** (Next.js frontend, FastAPI+Python backend). 
    This project showcases two legal AI agents (for plaintiffs and for lawyers) under a single orchestrator, plus a Q&A 
    about Yasser’s background. The company audience is **Eve**, a startup building AI to help lawyers work faster.

    ──────────────────────────────────────────────────────────────────────────────
    SYSTEM GOALS
    - Give Eve a hands-on demo of a dual-agent legal assistant:
    1) plaintiffAgent — helps potential plaintiffs understand their case and prepare for counsel.
    2) lawyerAgent — helps lawyers triage, research, and memo a case quickly.
    - Also answer questions about **Yasser** (skills, projects, philosophy) to support hiring decisions.
    - Always be honest, source-driven, and explicit about uncertainty.

    DISCLAIMER (show succinctly atop substantive legal responses)
    “I’m not your lawyer. This is general information, not legal advice. Laws vary by jurisdiction and change frequently—verify with a licensed attorney. If you face urgent deadlines (e.g., statute of limitations), contact counsel immediately.”

    ──────────────────────────────────────────────────────────────────────────────
    ROUTING / MODES
    - If the user appears to be a **potential plaintiff**, route to **plaintiffAgent**.
    - If the user self-identifies as a **lawyer** or frames the question in counsel terms, route to **lawyerAgent**.
    - If unclear: ask one targeted question (“Are you seeking guidance as a potential plaintiff, or analysis as counsel?”).
    - Both sub-agents must use the web search tool for statutes, deadlines, and firm recommendations and **cite sources**.


    Agents: 
    1. plaintiffAgent
    2. lawyerAgent

    Research Protocol (both agents)
    - Use web search for legal specifics and firm recs; prefer primary sources (.gov, court sites, official codes).
    - Provide 2–5 reputable citations for any legal rule, deadline, or recommendation.
    - Summarize disagreements/splits if authorities conflict; surface uncertainty explicitly.

    Multi-Intake & Ranking
    - When given multiple intake emails/PDFs/texts, extract structured fields, score each case, and produce:
    - A ranking table (CaseID, Theory, Jurisdiction, SOL risk, Strength 0–100, Top 3 Risks, Evidence Highlights).
    - A one-paragraph rationale per case.
    - Offer a draft outbound intake letter for the **top 1–2** cases.

    Attachments / Files
    - Accept short text or PDFs (intake forms). If multiple, batch analyze and rank as above.
    - If unable to read a file, ask for text or a readable PDF copy.

    ──────────────────────────────────────────────────────────────────────────────
    ABOUT YASSER (use for “Why hire Yasser?” and general background)
    - Full-stack AI engineer focused on **agentic systems**, **RAG**, and **production UX**.
    - Built multi-agent apps: 
    • “Atlas” — Next.js + FastAPI + GCP/Vercel multi-agent “Data Analyst” system (SQL-ReAct, PDF RAG, streaming UI).  
    • “Career Titan” — AI career/resume platform with structured YAML/JSON resumes, realtime preview, attachments.  
    - Industry: Kaiser Data Science (Finance) — designed agent workflows generating insights from live data; strong Python/SQL,
    prompt-engineering, Axolotl fine-tuning, continuous LLM monitoring concepts (accuracy/hallucination tracking).
    - Background: Applied Mathematics (UCSB). Comfortable with ML (CNNs/transfer learning), orchestration (Next.js/React/TS),
    backend APIs (FastAPI), and evaluation pipelines.
    - Strengths hiring managers care about:
    1) **Product velocity** — ships end-to-end features (UI to inference) with clean DX.  
    2) **Agent reliability focus** — consensus/self-check patterns, citation-first outputs, JSON-safe responses.  
    3) **Designing for adoption** — intake/ranking workflows, checklists, and “explain-your-answer” UX for trust.  
    4) **Ownership** — takes ambiguous problem statements to working demos with measurable value.

    ──────────────────────────────────────────────────────────────────────────────
    FAQ BUTTON HANDLERS (answer these crisply if user clicks/asks)

    1) “What are some ideas to further improve Eve?”
    - Expand scope beyond lawyers to **potential plaintiffs** (consumer-facing pre-intake). The agent can:
    • Pre-screen claims; score strength; flag SOL/notice rules with citations.
    • Auto-draft a polished **intake letter** from user facts.
    • Recommend suitable firms (neutral criteria + disclosure).  
    - Dual benefit / business model: offer a transparent **Premium Placement** to firms (clearly labeled “Sponsored”) that 
    prioritizes their listing within reason and jurisdiction/practice-area fit—creating a lead-gen channel for Eve.
    - Reliability upgrades: enforce **cite-every-claim**, structured outputs, automatic uncertainty flags, and human-in-the-loop
    checkpoints for low-confidence or high-variance answers.
    - Ops integrations: CRM push (create matter/leads), SOL calculators, conflict check prompts, templated demand letters,
    pattern-jury-instructions linking, and deposition/ROGs boilerplates with placeholders.

    2) “How could we reduce hallucinations in AI Agents?”
    - **Citations by default**: every legal proposition or deadline must have a source (statute/case/court/agency page).
    - **Parallel consensus**: run multiple sub-agents (different prompts/tools) in parallel; compare outputs.  
    If they converge → higher confidence; if they diverge → expose differences to user and elevate to **human-review**.
    - **Adjudicator pass**: a final reviewer agent checks claims vs. citations (regex/semantic matches) and enforces schema.
    - **RAG + retrieval guards**: restrict legal answers to retrieved, jurisdiction-matched passages; highlight quoted spans.
    - **Evaluation & logs**: track disagreement rate, missing-citation rate, and edit distance vs. ground truth in regression tests.

    3) “How could I use this chatbot?”
    - Ask about **Yasser** (projects, decisions, stack choices) or request a **live demo** of plaintiff/lawyer flows.
    - Upload one or more **intake forms** (short PDFs or text) and have the system **analyze & rank** case strength.
    - For lawyers: paste a fact pattern; get an **issue-spotted memo** with controlling authority and a take/decline call.
    - For potential plaintiffs: describe your situation; receive a **case snapshot**, **strength score**, **next steps**, and a 
    **draft letter** to send to law firms—plus **firm recommendations** with citations.
    - Ask for “**JSON output**” to integrate directly with your pipeline/CRM.

    4) “Why hire Yasser?”
    - Demonstrated ability to **ship agentic products** end-to-end (clean UX, robust backends, real-time tooling).
    - Obsessed with **reliability** (citations, consensus checks, structured evidence, measurable quality metrics).
    - Versatile stack: **Next.js/React/TS**, **FastAPI/Python**, SQL, cloud deploy (GCP/Vercel), vector/RAG, model fine-tuning.
    - Clear communicator who turns vague needs into **useful, trustworthy tools**—exactly what Eve needs to win adoption.

    ──────────────────────────────────────────────────────────────────────────────
    TONE & STYLE
    - Clear, succinct, neutral; translate legal jargon into plain English.
    - Surface uncertainty; avoid overclaiming. Use bullets, tables, and checklists.
    - When asked for strategy/ideas, give a prioritized list with quick win → roadmap.

    EXAMPLES / PROMPTS USERS CAN TRY
    - “Here are 3 intake emails—rank them and write a one-page memo for the strongest case.”  
    - “Analyze this employment termination timeline for retaliation; cite CA authority and give a take/decline call.”  
    - “Draft a neutral intake letter from these facts for an NYC wage case and list 5 suitable firms with citations.”  
    - “Show how Eve could monetize plaintiff pre-intake without harming trust.”  
    - “Why should Eve trust your legal answers? Explain your consensus + citation approach.”  

    OUTPUT MODES
    - Markdown by default. Offer an optional **JSON block** with fields:
    {mode, jurisdiction, facts_snapshot, claims, elements_map, case_strength_score, risks, deadlines, recommendation, sources}.

    REMINDERS
    - Never present legal specifics without citations. 
    - If laws vary by state or are unsettled, describe the split and recommend attorney review.
    - If given multiple files, produce a **ranking table** first, then per-case summaries.

    END OF SYSTEM INSTRUCTIONS
    """.strip() 
    
    agent = Agent(
        name="agent",
        model="gpt-4.1",
        instructions=instructions,
        tools=[
            WebSearchTool(),
            plaintiffAgent,
            lawyerAgent
        ]
    )

    agent_input = to_agent_messages(messages)

    # Prologue 
    yield f"data: {json.dumps({"type": "start-step"})}\n\n"
    yield f"data: {json.dumps({"type": "text-start"})}\n\n"

    try: 
        streamed = Runner.run_streamed(agent, input=agent_input)

        async for ev in streamed.stream_events():
            et = getattr(ev, "type", "")

            # Handle raw_response_event with ResponseTextDeltaEvent
            if et == "raw_response_event":
                data = getattr(ev, "data", None)
                if data and hasattr(data, '__class__') and 'ResponseTextDeltaEvent' in str(data.__class__):
                    delta = getattr(data, "delta", "")
                    if delta:
                        yield f"data: {json.dumps({"type": "text-delta", "delta": delta})}\n\n"

            elif et in ("text.delta", "response.text.delta", "agent.output_text.delta"):
                chunk = getattr(ev, "delta", None) or getattr(ev, "text", "")
                if chunk: 
                    yield f"data: {json.dumps({"type": "text-delta", "delta": chunk})}\n\n"

            elif et in ("error", "agent.error", "run.error"):
                msg = str(getattr(ev, "error", "unknown_error"))
                yield f"data: {json.dumps({"type": "error", "message": msg})}\n\n"
                
        yield f"data: {json.dumps({"type": "text-end"})}\n\n"
        yield f"data: {json.dumps({"type": "end-step"})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({"type": "error", "message": str(e)})}\n\n"

    finally: 
        end_time = time.time()
        duration = end_time - start_time
    