import os, json
from crewai import Agent, Task, Crew, Process
from langchain_ollama import ChatOllama

def get_llm(model="gemma2:2b", temp=0.3):
    return ChatOllama(model=model, base_url=os.getenv("OLLAMA_BASE_URL","http://host.docker.internal:11434"), temperature=temp, num_predict=2048)

def load_kb(path="/app/knowledge_base.json", max_items=12):
    try:
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)
        if isinstance(data, dict):
            out = []
            for k, v in data.items():
                if isinstance(v, list):
                    out.append(f"\n### {k.upper()} ###")
                    for item in v[:max_items//2]: out.append(f"• {json.dumps(item, ensure_ascii=False)}")
            return "\n".join(out)[:3000]
        return json.dumps(data, ensure_ascii=False)[:3000]
    except Exception as e: return f"Contexte indisponible: {e}"

def run(agent_role, agent_goal, prompt, model="gemma2:2b", temp=0.3):
    llm = get_llm(model, temp)
    agent = Agent(role=agent_role, goal=agent_goal, backstory="Expert TP France/Portugal", llm=llm, verbose=False, allow_delegation=False)
    task = Task(description=prompt, expected_output="Réponse structurée en français", agent=agent)
    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=False)
    return crew.kickoff().raw.strip()
