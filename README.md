# 🪵 TimberNest — Multi-Agent AI E-Commerce Support & Fraud Risk System

A production-grade, multi-agent artificial intelligence customer support platform built for **TimberNest**, a handcrafted wooden furniture brand. The system integrates **Django**, **Google Gemini GenAI**, **LangChain / LangGraph**, **ChromaDB Vector RAG**, and **Real-Time Server-Sent Events (SSE)** to deliver autonomous, hierarchical, and auditable customer support.

---

## 📌 Table of Contents

1. [Project Overview](#-project-overview)
2. [What is Inside This Project](#-what-is-inside-this-project)
3. [Key Topics & Concepts Covered](#-key-topics--concepts-covered)
4. [Multi-Agent Architecture](#-multi-agent-architecture)
5. [Directory & File Structure](#-directory--file-structure)
6. [Data Models & Database Schema](#-data-models--database-schema)
7. [Tools & Integrations](#-tools--integrations)
8. [Knowledge Base & Vector RAG (ChromaDB)](#-knowledge-base--vector-rag-chromadb)
9. [Real-Time Streaming & Admin Dashboard (SSE)](#-real-time-streaming--admin-dashboard-sse)
10. [Setup & Installation Guide](#-setup--installation-guide)
11. [Running Tests](#-running-tests)
12. [Environment Configuration](#-environment-configuration)

---

## 🚀 Project Overview

**TimberNest AI Wooden Support** is an intelligent customer service system engineered to handle complex e-commerce post-purchase operations such as:
- Order tracking and shipment status inquiries with mock logistics data.
- Policy-driven questions (warranty, returns, assembly, product FAQs) powered by semantic document retrieval (RAG).
- Multi-tier refund negotiation with human-like empathy and hard policy enforcement.
- Autonomous hierarchical escalation from customer-facing agents to managerial decision agents and fraud risk analysts.
- Real-time audit trails streaming live agent thoughts, tool invocations, and decisions to staff administrators via Server-Sent Events (SSE).

---

## 📦 What is Inside This Project

The project is structured into two core Django applications alongside LLM and Vector database pipelines:

### 1. `orders` App (Core E-Commerce Domain)
- **Product Catalog:** Model for wooden furniture (`Product`), tracking inventory status, pricing, categories, and descriptions.
- **Order Management:** Lifecycle tracking (`Order`) including carrier names, tracking numbers, shipping addresses, and status (`pending`, `dispatched`, `delivered`, `cancelled`).
- **Refund Management:** Customer refund submissions (`RefundRequest`) evaluated against return policies.
- **Customer Views & UI:** Order overview and interactive chat window where customers converse with AI agent **Shree**.

### 2. `supports` App (AI Agents, Orchestration & Real-time Dashboard)
- **Frontline Support Agent ("Shree"):** Handles conversational support, queries order and logistics data, retrieves company policies, and drafts concise, empathetic replies without exposing internal mechanics.
- **Senior Support Manager Agent:** Evaluates escalated refund requests using structured three-part decisions (`APPROVE`, `DENY`, `ESCALATE_TO_RISK`).
- **Fraud Risk Analyst Agent:** In-depth customer behavior analysis calculating refund ratios, repeat claim patterns, and assigning risk verdicts (`LOW`, `MEDIUM`, `HIGH`).
- **Dual Agent Engine Implementations:**
  - **Native Google GenAI SDK (`supports/agents.py`):** Low-level multi-turn loop, strict function schema declarations, tool result parsing, and error-tolerant fallback execution.
  - **LangChain & LangGraph (`supports/langchain_agents.py`, `supports/langchain_tools.py`):** Modern agentic implementation using `@tool` decorators, `ChatGoogleGenerativeAI`, and `InMemorySaver` checkpointers.
- **RAG & Knowledge Base (`supports/rag.py`):** Ingestion pipeline extracting PDF policies, text chunking, and embedding generation via ChromaDB vector database.
- **Event-Driven Streaming (`supports/event_queue.py`):** Thread-safe publisher-subscriber queue delivering live agent activity to admin frontends.
- **Staff Operations Dashboard:** Real-time visibility into all customer chats, displaying manager involvement and fraud risk indicators with real-time SSE updates.

---

## 🧠 Key Topics & Concepts Covered

This codebase serves as an enterprise reference implementation covering modern AI and full-stack software engineering disciplines:

| Domain | Topics & Applied Concepts |
|---|---|
| **Multi-Agent Systems** | Hierarchical delegation, inter-agent tool calls, autonomous manager escalations, fraud investigator subagents, and authoritative decision handoffs. |
| **Retrieval-Augmented Generation (RAG)** | PDF document ingestion (`pypdf`), text chunking strategies, local vector embeddings, ChromaDB persistent vector storage, and similarity search queries. |
| **Tool / Function Calling** | JSON Schema function declarations, structured schema validation, dynamic argument injection, and error encapsulation. |
| **Real-Time Streaming** | Server-Sent Events (SSE), HTTP `text/event-stream`, thread-safe pub/sub queues (`queue.Queue`), and frontend DOM stream consumption. |
| **Audit Logging & Observability** | Persistent event-driven execution logs (`AgentLog`), tracking every internal step: `tool_call`, `tool_result`, `manager`, `risk`, and `final`. |
| **Fraud Risk Detection** | Order-to-refund ratio calculation, 90-day velocity metrics, past denial tracking, and behavioral pattern evaluation. |
| **Django Enterprise Architecture** | Model properties, custom management commands (`loaddocuments`), fixtures, session authentication, and decorator-based role security (`@staff_member_required`, `@login_required`). |
| **Prompt Engineering** | Role grounding, personality constraints, line-length constraints, plain-text sanitization, and structured few-line response formats. |

---

## 🤖 Multi-Agent Architecture

The system uses a 3-tier hierarchical agent network:

```
                  ┌──────────────────────────────┐
                  │       Customer (User)        │
                  └──────────────┬───────────────┘
                                 │ Chat Message
                                 ▼
               ┌────────────────────────────────────┐
               │    Tier 1: Shree (Support Agent)   │
               │  - Direct order & tracking lookup  │
               │  - Company document RAG search     │
               └──────────────┬─────────────────────┘
                              │
               Customer asks for refund / compensation
                              │
                              ▼
               ┌────────────────────────────────────┐
               │ Tier 2: Senior Support Manager     │
               │  - Validates delivery vs policies  │
               │  - Checks refund history           │
               └──────────────┬─────────────────────┘
                              │
                 Suspicious claim / 3+ refunds
                              │
                              ▼
               ┌────────────────────────────────────┐
               │ Tier 3: Fraud Risk Analyst         │
               │  - Calculates risk profiles        │
               │  - Assesses refund-to-order ratio  │
               │  - Returns LOW / MEDIUM / HIGH     │
               └────────────────────────────────────┘
```

### Detailed Agent Roles

1. **Frontline Agent — Shree (`SUPPORT_SYSTEM_PROMPT`)**
   - **Tone:** Friendly, empathetic, concise, plain-text format (no raw markdown symbols like `**`).
   - **Available Tools:**
     - `get_order_details`: Accesses order info, delivery dates, carrier info.
     - `get_refund_history`: Checks user's past refund history.
     - `check_delivery_status`: Obtains real-time logistics tracking updates.
     - `search_knowledge_base`: Retrieves official company policies and FAQs.
     - `escalate_to_manager`: Hands off refund requests to the Senior Manager.

2. **Senior Support Manager (`MANAGER_SYSTEM_PROMPT`)**
   - **Objective:** Final verdict on refund claims (`APPROVE`, `DENY`, or `ESCALATE_TO_RISK`).
   - **Decision Rules:** Reviews facts objectively; if customer has 3+ refunds or shows suspicious activity, escalates to Risk Analyst.
   - **Available Tools:**
     - `get_refund_history`
     - `access_fraud_risk`

3. **Fraud Risk Analyst (`RISK_SYSTEM_PROMPT`)**
   - **Objective:** Evaluates customer fraud probability.
   - **Metrics Analyzed:** Total lifetime orders, refund count in past 90 days, approved vs denied ratio, refund-to-order ratio.
   - **Output:** Structured report: Risk Level (`LOW` / `MEDIUM` / `HIGH`), Key Signals, and Recommendations.

---

## 📁 Directory & File Structure

```text
ai_wooden_main/
│
├── ai_wooden_main/               # Django Project Configuration
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py              # Environment variables, database, installed apps
│   ├── urls.py                  # Global routing with root redirect to /orders/
│   └── wsgi.py
│
├── chroma_db/                    # ChromaDB Persistent Vector Database Storage
│   └── chroma.sqlite3
│
├── orders/                       # E-Commerce Core Application
│   ├── fixtures/
│   │   ├── demo_data.json       # Initial seed products, orders, refunds
│   │   └── fraud_test_data.json # Edge-case accounts with suspicious histories
│   ├── models.py                # Product, Order, RefundRequest models
│   ├── urls.py                  # /orders/ and /orders/<id>/
│   └── views.py                 # Customer order list & detail views
│
├── supports/                     # AI Multi-Agent & Operations Application
│   ├── documents/               # Official PDF Knowledge Base
│   │   ├── product_faq.pdf      # Assembly, care, material specs
│   │   ├── refund_policy.pdf    # Return window, non-refundable charges
│   │   └── warranty_policy.pdf  # 5-year structural warranty terms
│   ├── management/
│   │   └── commands/
│   │       └── loaddocuments.py # Django command: 'python manage.py loaddocuments'
│   ├── models.py                # Conversation, Message, AgentLog
│   ├── agents.py                # Gemini SDK agent orchestration & execution loops
│   ├── tools.py                 # Concrete tool logic & database query bridges
│   ├── tracking_data.py         # Mock courier shipment status dictionary
│   ├── rag.py                   # PyPDF loader, text chunker, ChromaDB vector store
│   ├── event_queue.py           # Thread-safe in-memory pub-sub event queue
│   ├── langchain_agents.py      # LangChain & LangGraph alternative agent pipeline
│   ├── langchain_tools.py       # LangChain @tool declarations
│   ├── tests.py                 # Test suite covering agents and schema integrity
│   ├── urls.py                  # /supports/chat/<id>/, /supports/dashboard/...
│   └── views.py                 # Customer chat API & real-time SSE stream views
│
├── static/ & staticfiles/        # Admin styles and dashboard CSS
│   └── css/support_dashboard_admin.css
│
├── templates/                    # HTML UI Templates
│   ├── login.html               # Staff & customer login interface
│   ├── orders_list.html         # Customer order history
│   ├── order_detail.html        # Order status & customer AI chat widget
│   └── supports/
│       ├── dashboard_base.html  # Admin navigation shell
│       ├── dashboard.html       # Support conversations monitor
│       └── conversation_details.html # Live dual-pane SSE transcript & activity feed
│
├── requirements.txt              # Pinned Python dependencies
├── manage.py                     # Django management script
├── Procfile                      # Deployment configuration for production WSGI
└── README.md                     # Project documentation
```

---

## 🗄️ Data Models & Database Schema

```
┌──────────────────┐            ┌──────────────────┐
│   auth.User      │ 1        * │      Order       │
│                  ├───────────►│                  │
└────────┬─────────┘            └────────┬─────────┘
         │                               │
         │ 1                             │ 1
         │                               │
         ▼ *                             ▼ *
┌──────────────────┐            ┌──────────────────┐
│   Conversation   │            │  RefundRequest   │
│  - manager_involve            │  - status        │
│  - risk_assessed │            │  - reason        │
└────────┬─────────┘            └──────────────────┘
         │
         ├───► 1:* Message  (role, content, timestamp)
         │
         └───► 1:* AgentLog (event_type, message, timestamp)
```

### Models Summary:
- **`Order`:** Connected to customer `User` and `Product`. Tracks price, status (`pending`, `dispatched`, `delivered`, `cancelled`), courier (`carrier`), tracking number, and delivery address.
- **`RefundRequest`:** Submissions referencing an order, including problem description and claim status (`pending`, `approved`, `denied`).
- **`Conversation`:** Single conversation per user-order pairing. Exposes dynamic properties:
  - `manager_involve`: Returns `True` if any `event_type="manager"` log exists.
  - `risk_assessed`: Returns `True` if any `event_type="risk"` log exists.
- **`AgentLog`:** Granular observability log capturing every step taken by AI agents:
  - `support`: Frontline thoughts or communications.
  - `tool_call`: Name and arguments passed to tools.
  - `tool_result`: Output returned by Python tools.
  - `manager`: Review notes, tool calls, and decisions by Manager Agent.
  - `risk`: Risk assessment starts, profile evaluations, and risk verdicts.
  - `final`: Final response sent to customer.

---

## 🛠️ Tools & Integrations

The agents have access to a suite of deterministic, sandboxed tools in `supports/tools.py`:

| Tool Function | Description | Source / Backing |
|---|---|---|
| `get_order_details(order_id)` | Fetches ordered item, delivery address, carrier, tracking ID, amount, and elapsed days since purchase. | SQLite `Order` table |
| `get_refund_history(order_id, user_id)` | Returns complete previous refund claims and statuses for this customer. | SQLite `RefundRequest` table |
| `check_delivery_status(tracking_number, carrier)` | Returns shipment whereabouts, delay reasons, and delivery estimates. | `supports/tracking_data.py` |
| `get_customer_risk_profile(user_id)` | Computes refund-to-order ratio, recent 90-day claims, and denied refunds count. | Database aggregation |
| `search_knowledge_base(query)` | Executes semantic vector similarity search against company policies. | ChromaDB vector collection |
| `escalate_to_manager(case_summary)` | Triggers the Senior Manager agent with a case brief. | `run_manager_agent` pipeline |
| `access_fraud_risk(user_id)` | Triggers the Fraud Risk agent for detailed evaluation. | `run_risk_agent` pipeline |

---

## 📚 Knowledge Base & Vector RAG (ChromaDB)

Company policies are stored as PDF documents in `supports/documents/`:
1. `refund_policy.pdf`: Standard 30-day window, 90-day damaged goods policy, non-refundable assembly fees.
2. `warranty_policy.pdf`: 5-year solid wood structural warranty, coverage criteria, warranty void conditions (e.g. unauthorized assembly).
3. `product_faq.pdf`: Wood care, cleaning instructions, assembly recommendations.

### Ingestion Pipeline (`supports/rag.py`)
- **Extraction:** Reads text page-by-page using `pypdf.PdfReader`.
- **Chunking (`chunk_text`):** Splits raw text into ~500-character semantic chunks while preserving word boundaries.
- **Vector Storage:** Stores chunks into local collection `timbernest_docs` using `collection.upsert(...)`.
- **Management Command:** Can be triggered anytime via:
  ```bash
  python manage.py loaddocuments
  ```

---

## ⚡ Real-Time Streaming & Admin Dashboard (SSE)

TimberNest provides customer support supervisors with a live control room:

```
[ Customer Chat Widget ]                  [ Staff Admin Dashboard ]
       │                                             │
       │ POST /supports/chat/<order_id>/             │ GET /supports/dashboard/stream/<id>/
       ▼                                             ▼
  Agents run tool calls ──► publish(event) ──► Server-Sent Events (SSE)
                                                     │
                                                     ▼
                                          Live Activity Feed Updates
                                          - "Calling tool check_delivery_status"
                                          - "Ekart returned: In Transit"
                                          - "Manager reviewing case..."
                                          - "Risk verdict: HIGH"
```

- **Publisher-Subscriber Architecture (`supports/event_queue.py`):**
  - Thread-safe queues per conversation ID.
  - Broadcasts events: `user_message`, `tool_call`, `tool_result`, `manager`, `risk`, `final`, `done`.
- **Admin Interface (`templates/supports/conversation_details.html`):**
  - **Left Pane:** Real-time customer/agent chat transcript.
  - **Right Pane:** Live agent activity logs with color-coded badges and animated state spinners.

---

## 💻 Setup & Installation Guide

### Prerequisites
- Python 3.11+
- Virtual Environment tool (`venv` or `virtualenv`)
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

### 1. Clone & Navigate
```bash
git clone <repository_url>
cd ai_wooden_main
```

### 2. Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### 5. Run Database Migrations
```bash
python manage.py migrate
```

### 6. Load Seed Data & Knowledge Base
```bash
# Load sample products, orders, and demo refund requests
python manage.py loaddata orders/fixtures/demo_data.json
python manage.py loaddata orders/fixtures/fraud_test_data.json

# Index company policy PDFs into ChromaDB
python manage.py loaddocuments
```

### 7. Create Superuser (Admin Access)
```bash
python manage.py createsuperuser
```

### 8. Start the Development Server
```bash
python manage.py runserver
```

Open your browser:
- **Customer Portal:** `http://localhost:8000/orders/`
- **Staff Live Dashboard:** `http://localhost:8000/supports/dashboard/`
- **Django Admin:** `http://localhost:8000/admin/`

---

## 🧪 Running Tests

The test suite validates agent behavior, schema integrity, and risk escalation logic:

```bash
python manage.py test supports
```

Tests verify:
- Safe fallback execution when tools are requested.
- Autonomous manager escalation to fraud analyst when suspicious patterns emerge.
- Validation that all tool parameter declarations match declared JSON properties.
- Prevention of duplicate risk evaluation executions.

---

## 🔒 Security & Best Practices

- **Role Separation:** Customer chat endpoints require `@login_required` while admin monitoring dashboards strictly enforce `@staff_member_required`.
- **System Prompt Guardrails:** System prompts prevent the AI from guessing tracking details, hallucinating orders, or approving refunds outside of manager authorization.
- **Fail-Safe Execution:** Tool invocations are wrapped in exception handlers that return polite explanations to the model rather than breaking the conversation loop.
- **Data Privacy:** Sensitive database credentials and AI API tokens are managed outside the repository using `python-decouple`.

---

## 📄 License
This project is proprietary and developed for TimberNest Handcrafted Wooden Furniture. All rights reserved.

A production-grade, multi-agent artificial intelligence customer support platform built for **TimberNest**, a handcrafted wooden furniture brand. The system integrates **Django**, **Google Gemini GenAI**, **LangChain / LangGraph**, **ChromaDB Vector RAG**, and **Real-Time Server-Sent Events (SSE)** to deliver autonomous, hierarchical, and auditable customer support.

---

## 📌 Table of Contents

1. [Project Overview](#-project-overview)
2. [What is Inside This Project](#-what-is-inside-this-project)
3. [Key Topics & Concepts Covered](#-key-topics--concepts-covered)
4. [Multi-Agent Architecture](#-multi-agent-architecture)
5. [Directory & File Structure](#-directory--file-structure)
6. [Data Models & Database Schema](#-data-models--database-schema)
7. [Tools & Integrations](#-tools--integrations)
8. [Knowledge Base & Vector RAG (ChromaDB)](#-knowledge-base--vector-rag-chromadb)
9. [Real-Time Streaming & Admin Dashboard (SSE)](#-real-time-streaming--admin-dashboard-sse)
10. [Setup & Installation Guide](#-setup--installation-guide)
11. [Running Tests](#-running-tests)
12. [Environment Configuration](#-environment-configuration)

---

## 🚀 Project Overview

**TimberNest AI Wooden Support** is an intelligent customer service system engineered to handle complex e-commerce post-purchase operations such as:
- Order tracking and shipment status inquiries with mock logistics data.
- Policy-driven questions (warranty, returns, assembly, product FAQs) powered by semantic document retrieval (RAG).
- Multi-tier refund negotiation with human-like empathy and hard policy enforcement.
- Autonomous hierarchical escalation from customer-facing agents to managerial decision agents and fraud risk analysts.
- Real-time audit trails streaming live agent thoughts, tool invocations, and decisions to staff administrators via Server-Sent Events (SSE).

---

## 📦 What is Inside This Project

The project is structured into two core Django applications alongside LLM and Vector database pipelines:

### 1. `orders` App (Core E-Commerce Domain)
- **Product Catalog:** Model for wooden furniture (`Product`), tracking inventory status, pricing, categories, and descriptions.
- **Order Management:** Lifecycle tracking (`Order`) including carrier names, tracking numbers, shipping addresses, and status (`pending`, `dispatched`, `delivered`, `cancelled`).
- **Refund Management:** Customer refund submissions (`RefundRequest`) evaluated against return policies.
- **Customer Views & UI:** Order overview and interactive chat window where customers converse with AI agent **Shree**.

### 2. `supports` App (AI Agents, Orchestration & Real-time Dashboard)
- **Frontline Support Agent ("Shree"):** Handles conversational support, queries order and logistics data, retrieves company policies, and drafts concise, empathetic replies without exposing internal mechanics.
- **Senior Support Manager Agent:** Evaluates escalated refund requests using structured three-part decisions (`APPROVE`, `DENY`, `ESCALATE_TO_RISK`).
- **Fraud Risk Analyst Agent:** In-depth customer behavior analysis calculating refund ratios, repeat claim patterns, and assigning risk verdicts (`LOW`, `MEDIUM`, `HIGH`).
- **Dual Agent Engine Implementations:**
  - **Native Google GenAI SDK (`supports/agents.py`):** Low-level multi-turn loop, strict function schema declarations, tool result parsing, and error-tolerant fallback execution.
  - **LangChain & LangGraph (`supports/langchain_agents.py`, `supports/langchain_tools.py`):** Modern agentic implementation using `@tool` decorators, `ChatGoogleGenerativeAI`, and `InMemorySaver` checkpointers.
- **RAG & Knowledge Base (`supports/rag.py`):** Ingestion pipeline extracting PDF policies, text chunking, and embedding generation via ChromaDB vector database.
- **Event-Driven Streaming (`supports/event_queue.py`):** Thread-safe publisher-subscriber queue delivering live agent activity to admin frontends.
- **Staff Operations Dashboard:** Real-time visibility into all customer chats, displaying manager involvement and fraud risk indicators with real-time SSE updates.

---

## 🧠 Key Topics & Concepts Covered

This codebase serves as an enterprise reference implementation covering modern AI and full-stack software engineering disciplines:

| Domain | Topics & Applied Concepts |
|---|---|
| **Multi-Agent Systems** | Hierarchical delegation, inter-agent tool calls, autonomous manager escalations, fraud investigator subagents, and authoritative decision handoffs. |
| **Retrieval-Augmented Generation (RAG)** | PDF document ingestion (`pypdf`), text chunking strategies, local vector embeddings, ChromaDB persistent vector storage, and similarity search queries. |
| **Tool / Function Calling** | JSON Schema function declarations, structured schema validation, dynamic argument injection, and error encapsulation. |
| **Real-Time Streaming** | Server-Sent Events (SSE), HTTP `text/event-stream`, thread-safe pub/sub queues (`queue.Queue`), and frontend DOM stream consumption. |
| **Audit Logging & Observability** | Persistent event-driven execution logs (`AgentLog`), tracking every internal step: `tool_call`, `tool_result`, `manager`, `risk`, and `final`. |
| **Fraud Risk Detection** | Order-to-refund ratio calculation, 90-day velocity metrics, past denial tracking, and behavioral pattern evaluation. |
| **Django Enterprise Architecture** | Model properties, custom management commands (`loaddocuments`), fixtures, session authentication, and decorator-based role security (`@staff_member_required`, `@login_required`). |
| **Prompt Engineering** | Role grounding, personality constraints, line-length constraints, plain-text sanitization, and structured few-line response formats. |

---

## 🤖 Multi-Agent Architecture

The system uses a 3-tier hierarchical agent network:

```
                  ┌──────────────────────────────┐
                  │       Customer (User)        │
                  └──────────────┬───────────────┘
                                 │ Chat Message
                                 ▼
               ┌────────────────────────────────────┐
               │    Tier 1: Shree (Support Agent)   │
               │  - Direct order & tracking lookup  │
               │  - Company document RAG search     │
               └──────────────┬─────────────────────┘
                              │
               Customer asks for refund / compensation
                              │
                              ▼
               ┌────────────────────────────────────┐
               │ Tier 2: Senior Support Manager     │
               │  - Validates delivery vs policies  │
               │  - Checks refund history           │
               └──────────────┬─────────────────────┘
                              │
                 Suspicious claim / 3+ refunds
                              │
                              ▼
               ┌────────────────────────────────────┐
               │ Tier 3: Fraud Risk Analyst         │
               │  - Calculates risk profiles        │
               │  - Assesses refund-to-order ratio  │
               │  - Returns LOW / MEDIUM / HIGH     │
               └────────────────────────────────────┘
```

### Detailed Agent Roles

1. **Frontline Agent — Shree (`SUPPORT_SYSTEM_PROMPT`)**
   - **Tone:** Friendly, empathetic, concise, plain-text format (no raw markdown symbols like `**`).
   - **Available Tools:**
     - `get_order_details`: Accesses order info, delivery dates, carrier info.
     - `get_refund_history`: Checks user's past refund history.
     - `check_delivery_status`: Obtains real-time logistics tracking updates.
     - `search_knowledge_base`: Retrieves official company policies and FAQs.
     - `escalate_to_manager`: Hands off refund requests to the Senior Manager.

2. **Senior Support Manager (`MANAGER_SYSTEM_PROMPT`)**
   - **Objective:** Final verdict on refund claims (`APPROVE`, `DENY`, or `ESCALATE_TO_RISK`).
   - **Decision Rules:** Reviews facts objectively; if customer has 3+ refunds or shows suspicious activity, escalates to Risk Analyst.
   - **Available Tools:**
     - `get_refund_history`
     - `access_fraud_risk`

3. **Fraud Risk Analyst (`RISK_SYSTEM_PROMPT`)**
   - **Objective:** Evaluates customer fraud probability.
   - **Metrics Analyzed:** Total lifetime orders, refund count in past 90 days, approved vs denied ratio, refund-to-order ratio.
   - **Output:** Structured report: Risk Level (`LOW` / `MEDIUM` / `HIGH`), Key Signals, and Recommendations.

---

## 📁 Directory & File Structure

```text
ai_wooden_main/
│
├── ai_wooden_main/               # Django Project Configuration
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py              # Environment variables, database, installed apps
│   ├── urls.py                  # Global routing with root redirect to /orders/
│   └── wsgi.py
│
├── chroma_db/                    # ChromaDB Persistent Vector Database Storage
│   └── chroma.sqlite3
│
├── orders/                       # E-Commerce Core Application
│   ├── fixtures/
│   │   ├── demo_data.json       # Initial seed products, orders, refunds
│   │   └── fraud_test_data.json # Edge-case accounts with suspicious histories
│   ├── models.py                # Product, Order, RefundRequest models
│   ├── urls.py                  # /orders/ and /orders/<id>/
│   └── views.py                 # Customer order list & detail views
│
├── supports/                     # AI Multi-Agent & Operations Application
│   ├── documents/               # Official PDF Knowledge Base
│   │   ├── product_faq.pdf      # Assembly, care, material specs
│   │   ├── refund_policy.pdf    # Return window, non-refundable charges
│   │   └── warranty_policy.pdf  # 5-year structural warranty terms
│   ├── management/
│   │   └── commands/
│   │       └── loaddocuments.py # Django command: 'python manage.py loaddocuments'
│   ├── models.py                # Conversation, Message, AgentLog
│   ├── agents.py                # Gemini SDK agent orchestration & execution loops
│   ├── tools.py                 # Concrete tool logic & database query bridges
│   ├── tracking_data.py         # Mock courier shipment status dictionary
│   ├── rag.py                   # PyPDF loader, text chunker, ChromaDB vector store
│   ├── event_queue.py           # Thread-safe in-memory pub-sub event queue
│   ├── langchain_agents.py      # LangChain & LangGraph alternative agent pipeline
│   ├── langchain_tools.py       # LangChain @tool declarations
│   ├── tests.py                 # Test suite covering agents and schema integrity
│   ├── urls.py                  # /supports/chat/<id>/, /supports/dashboard/...
│   └── views.py                 # Customer chat API & real-time SSE stream views
│
├── static/ & staticfiles/        # Admin styles and dashboard CSS
│   └── css/support_dashboard_admin.css
│
├── templates/                    # HTML UI Templates
│   ├── login.html               # Staff & customer login interface
│   ├── orders_list.html         # Customer order history
│   ├── order_detail.html        # Order status & customer AI chat widget
│   └── supports/
│       ├── dashboard_base.html  # Admin navigation shell
│       ├── dashboard.html       # Support conversations monitor
│       └── conversation_details.html # Live dual-pane SSE transcript & activity feed
│
├── requirements.txt              # Pinned Python dependencies
├── manage.py                     # Django management script
├── Procfile                      # Deployment configuration for production WSGI
└── README.md                     # Project documentation
```

---

## 🗄️ Data Models & Database Schema

```
┌──────────────────┐            ┌──────────────────┐
│   auth.User      │ 1        * │      Order       │
│                  ├───────────►│                  │
└────────┬─────────┘            └────────┬─────────┘
         │                               │
         │ 1                             │ 1
         │                               │
         ▼ *                             ▼ *
┌──────────────────┐            ┌──────────────────┐
│   Conversation   │            │  RefundRequest   │
│  - manager_involve            │  - status        │
│  - risk_assessed │            │  - reason        │
└────────┬─────────┘            └──────────────────┘
         │
         ├───► 1:* Message  (role, content, timestamp)
         │
         └───► 1:* AgentLog (event_type, message, timestamp)
```

### Models Summary:
- **`Order`:** Connected to customer `User` and `Product`. Tracks price, status (`pending`, `dispatched`, `delivered`, `cancelled`), courier (`carrier`), tracking number, and delivery address.
- **`RefundRequest`:** Submissions referencing an order, including problem description and claim status (`pending`, `approved`, `denied`).
- **`Conversation`:** Single conversation per user-order pairing. Exposes dynamic properties:
  - `manager_involve`: Returns `True` if any `event_type="manager"` log exists.
  - `risk_assessed`: Returns `True` if any `event_type="risk"` log exists.
- **`AgentLog`:** Granular observability log capturing every step taken by AI agents:
  - `support`: Frontline thoughts or communications.
  - `tool_call`: Name and arguments passed to tools.
  - `tool_result`: Output returned by Python tools.
  - `manager`: Review notes, tool calls, and decisions by Manager Agent.
  - `risk`: Risk assessment starts, profile evaluations, and risk verdicts.
  - `final`: Final response sent to customer.

---

## 🛠️ Tools & Integrations

The agents have access to a suite of deterministic, sandboxed tools in `supports/tools.py`:

| Tool Function | Description | Source / Backing |
|---|---|---|
| `get_order_details(order_id)` | Fetches ordered item, delivery address, carrier, tracking ID, amount, and elapsed days since purchase. | SQLite `Order` table |
| `get_refund_history(order_id, user_id)` | Returns complete previous refund claims and statuses for this customer. | SQLite `RefundRequest` table |
| `check_delivery_status(tracking_number, carrier)` | Returns shipment whereabouts, delay reasons, and delivery estimates. | `supports/tracking_data.py` |
| `get_customer_risk_profile(user_id)` | Computes refund-to-order ratio, recent 90-day claims, and denied refunds count. | Database aggregation |
| `search_knowledge_base(query)` | Executes semantic vector similarity search against company policies. | ChromaDB vector collection |
| `escalate_to_manager(case_summary)` | Triggers the Senior Manager agent with a case brief. | `run_manager_agent` pipeline |
| `access_fraud_risk(user_id)` | Triggers the Fraud Risk agent for detailed evaluation. | `run_risk_agent` pipeline |

---

## 📚 Knowledge Base & Vector RAG (ChromaDB)

Company policies are stored as PDF documents in `supports/documents/`:
1. `refund_policy.pdf`: Standard 30-day window, 90-day damaged goods policy, non-refundable assembly fees.
2. `warranty_policy.pdf`: 5-year solid wood structural warranty, coverage criteria, warranty void conditions (e.g. unauthorized assembly).
3. `product_faq.pdf`: Wood care, cleaning instructions, assembly recommendations.

### Ingestion Pipeline (`supports/rag.py`)
- **Extraction:** Reads text page-by-page using `pypdf.PdfReader`.
- **Chunking (`chunk_text`):** Splits raw text into ~500-character semantic chunks while preserving word boundaries.
- **Vector Storage:** Stores chunks into local collection `timbernest_docs` using `collection.upsert(...)`.
- **Management Command:** Can be triggered anytime via:
  ```bash
  python manage.py loaddocuments
  ```

---

## ⚡ Real-Time Streaming & Admin Dashboard (SSE)

TimberNest provides customer support supervisors with a live control room:

```
[ Customer Chat Widget ]                  [ Staff Admin Dashboard ]
       │                                             │
       │ POST /supports/chat/<order_id>/             │ GET /supports/dashboard/stream/<id>/
       ▼                                             ▼
  Agents run tool calls ──► publish(event) ──► Server-Sent Events (SSE)
                                                     │
                                                     ▼
                                          Live Activity Feed Updates
                                          - "Calling tool check_delivery_status"
                                          - "Ekart returned: In Transit"
                                          - "Manager reviewing case..."
                                          - "Risk verdict: HIGH"
```

- **Publisher-Subscriber Architecture (`supports/event_queue.py`):**
  - Thread-safe queues per conversation ID.
  - Broadcasts events: `user_message`, `tool_call`, `tool_result`, `manager`, `risk`, `final`, `done`.
- **Admin Interface (`templates/supports/conversation_details.html`):**
  - **Left Pane:** Real-time customer/agent chat transcript.
  - **Right Pane:** Live agent activity logs with color-coded badges and animated state spinners.

---

## 💻 Setup & Installation Guide

### Prerequisites
- Python 3.11+
- Virtual Environment tool (`venv` or `virtualenv`)
- Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

### 1. Clone & Navigate
```bash
git clone <repository_url>
cd ai_wooden_main
```

### 2. Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### 5. Run Database Migrations
```bash
python manage.py migrate
```

### 6. Load Seed Data & Knowledge Base
```bash
# Load sample products, orders, and demo refund requests
python manage.py loaddata orders/fixtures/demo_data.json
python manage.py loaddata orders/fixtures/fraud_test_data.json

# Index company policy PDFs into ChromaDB
python manage.py loaddocuments
```

### 7. Create Superuser (Admin Access)
```bash
python manage.py createsuperuser
```

### 8. Start the Development Server
```bash
python manage.py runserver
```

Open your browser:
- **Customer Portal:** `http://localhost:8000/orders/`
- **Staff Live Dashboard:** `http://localhost:8000/supports/dashboard/`
- **Django Admin:** `http://localhost:8000/admin/`

---

## 🧪 Running Tests

The test suite validates agent behavior, schema integrity, and risk escalation logic:

```bash
python manage.py test supports
```

Tests verify:
- Safe fallback execution when tools are requested.
- Autonomous manager escalation to fraud analyst when suspicious patterns emerge.
- Validation that all tool parameter declarations match declared JSON properties.
- Prevention of duplicate risk evaluation executions.

---

## 🔒 Security & Best Practices

- **Role Separation:** Customer chat endpoints require `@login_required` while admin monitoring dashboards strictly enforce `@staff_member_required`.
- **System Prompt Guardrails:** System prompts prevent the AI from guessing tracking details, hallucinating orders, or approving refunds outside of manager authorization.
- **Fail-Safe Execution:** Tool invocations are wrapped in exception handlers that return polite explanations to the model rather than breaking the conversation loop.
- **Data Privacy:** Sensitive database credentials and AI API tokens are managed outside the repository using `python-decouple`.

---

## 📄 License
This project is proprietary and developed for TimberNest Handcrafted Wooden Furniture. All rights reserved.

