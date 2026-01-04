# Kontrakt MAS (Definition of Done) — new_design

Ten dokument definiuje, co znaczy:  
**„new_design ma funkcjonalność MAS jak blueprint”** w ramach tego repo.

## 1. Słownik pojęć

- **Agent** — komponent realizujący rolę (np. WeatherAgent, PlannerAgent).
- **Coordinator (meta-agent)** — agent decydujący o kolejnych krokach i delegujący zadania do innych agentów.
- **Runda (round)** — pojedynczy cykl: decyzja koordynatora → wykonanie przez agenta → zapis śladu → (opcjonalnie) krytyka jakości.
- **team_conversation (team trace)** — wewnętrzny zapis pracy zespołu agentów (zdarzenia, decyzje, wywołania narzędzi, obserwacje).
- **Tool** — narzędzie/akcja (np. API), uruchamiane jako część planu.
- **QC** — quality control: walidacja formatów + retry + krytyk (critic) jako bramka jakości.

---

## 2. Definition of Done (DoD)

### 2.1 Role (min. coordinator + 2 agentów)
**Warunek spełnienia:**
1) W systemie istnieje `CoordinatorAgent` (meta-agent), który wybiera następnego agenta.
2) Oprócz koordynatora są co najmniej **dwaj** agenci roboczy (np. `PlannerAgent` i `WeatherAgent`).
3) Każdy agent ma deklarowany opis roli / kompetencji (capabilities), który koordynator używa do wyboru.

**Dowód w repo:**
- Implementacje klas agentów + rejestracja w `AgentRegistry`.
- Test: koordynator wybiera różne agenty dla różnych intencji.

---

### 2.2 Pętla rund (iteracje do stop-condition)
**Warunek spełnienia:**
1) Orchestrator wspiera tryb iteracyjny: wykonuje kolejne rundy.
2) Zatrzymanie jest kontrolowane przez:
   - `stop=true` od koordynatora **lub**
   - osiągnięcie celu (np. gotowa odpowiedź) **lub**
   - limit rund (safety) / detektor braku postępu.

**Dowód w repo:**
- Metoda typu `run_loop(...)` / `handle_iterative(...)`.
- Test: 2+ rundy dla złożonego zadania, zatrzymanie w poprawnym momencie.

---

### 2.3 Wspólna pamięć zespołu (team_conversation)
**Warunek spełnienia:**
1) System gromadzi `team_conversation` jako listę zdarzeń (np. `TraceEvent`).
2) Zdarzenia obejmują minimum:
   - routing/wybór agenta,
   - odpowiedź agenta,
   - (docelowo) wywołania tooli + obserwacje,
   - (docelowo) krytykę QC.
3) `team_conversation` jest dostępne dla koordynatora jako kontekst.

**Dowód w repo:**
- Zdarzenia są zapisywane w runtime.
- Można je wyeksportować jako JSONL.

---

### 2.4 Narzędzia (tools) jako akcje agentów
**Warunek spełnienia:**
1) Wywołanie toola jest modelowane jako akcja: `tool_call → observation`.
2) Każde wywołanie toola jest logowane w `team_conversation` (trace).
3) Plan i wykonanie rozdzielone (Planner/Executor albo jeden agent w dwóch fazach).

**Dowód w repo:**
- Narzędzia są wołane przez wspólny runner (np. `call_tool_with_trace` + retry).
- Test: tool_call generuje trace event.

---

### 2.5 Kontrola jakości (walidacja + retry + critic)
**Warunek spełnienia:**
1) Kluczowe wyjścia mają format strukturalny (np. JSON) i są walidowane.
2) Jeśli walidacja nie przechodzi → retry/repair loop.
3) Critic ocenia wynik i może wymusić kolejną rundę.

**Dowód w repo:**
- Walidator + retry policy.
- Critic agent z checklistą.
- Test: błędny format → naprawa → poprawny format.

---

## 3. Minimalny przykład trace (1 zadanie)

Przykład: użytkownik pyta „pogoda w Warszawie jutro”.

Poniżej przykładowe zdarzenia (JSONL) w `team_conversation`:

```json
{"actor":"orchestrator","action":"route","target":"coordinator","params":{"text":"pogoda w Warszawie jutro"},"outcome":"ok","error":null,"timestamp":"2026-01-04T10:00:00Z","correlation_id":"CID-123"}
{"actor":"coordinator","action":"decide","target":"weather","params":{"task":"pobierz prognozę"},"outcome":"ok","error":null,"timestamp":"2026-01-04T10:00:01Z","correlation_id":"CID-123"}
{"actor":"tool_runner","action":"tool_call","target":"open_meteo","params":{"location":"Warszawa","date":"tomorrow"},"outcome":"ok","error":null,"timestamp":"2026-01-04T10:00:02Z","correlation_id":"CID-123"}
{"actor":"weather","action":"respond","target":"user","params":{"content":"Pogoda dla Warszawy..."},"outcome":"ok","error":null,"timestamp":"2026-01-04T10:00:03Z","correlation_id":"CID-123"}
{"actor":"critic","action":"review","target":"answer","params":{"verdict":"pass","notes":[]},"outcome":"ok","error":null,"timestamp":"2026-01-04T10:00:04Z","correlation_id":"CID-123"}
