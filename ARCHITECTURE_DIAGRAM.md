# System Architecture Diagram

## Overview

This document contains the system architecture diagram for the UAE Social Support AI Platform in Mermaid format. You can render this in multiple ways:

1. **GitHub**: Paste the Mermaid code directly in a .md file - GitHub will render it automatically
2. **Online Renderer**: Visit https://mermaid.live and paste the code below
3. **VS Code**: Install "Markdown Preview Mermaid Support" extension
4. **Export to PNG/PDF**: Use mermaid-cli (`mmdc -i ARCHITECTURE_DIAGRAM.md -o architecture.png`)

---

## Full System Architecture

```mermaid
graph TB
    %% Styling
    classDef presentation fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef orchestration fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef agents fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef data fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef ml fill:#ffe0b2,stroke:#e65100,stroke-width:2px
    classDef observability fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    %% Presentation Layer
    subgraph Presentation["PRESENTATION LAYER"]
        UI[Streamlit Web Interface<br/>Applicant Portal + Admin Dashboard]
        API[FastAPI REST Backend<br/>29 Production Endpoints]
        UI <-->|HTTP/REST| API
    end

    %% Orchestration Layer
    subgraph Orchestration["ORCHESTRATION LAYER"]
        MO[Master Orchestrator<br/>LangGraph StateGraph • Typed State Management]
        MO --> Pipeline[6-Agent Processing Pipeline]
    end

    %% Agent Layer
    subgraph Agents["AGENT PROCESSING LAYER"]
        Pipeline --> Agent1[1. Data Extraction Agent<br/>OCR + PDF + Excel]
        Agent1 --> Agent2[2. Data Validation Agent<br/>Cross-Document Consistency]
        Agent2 --> Agent3[3. Eligibility Agent<br/>ML Model + Business Rules]
        Agent3 --> Agent4[4. Recommendation Agent<br/>Support Calculation + Programs]
        Agent4 --> Agent5[5. Explanation Agent<br/>Natural Language Justification]
        Agent5 --> Agent6[6. RAG Chatbot Agent<br/>Interactive Q&A]
    end

    %% Data Processing Layer
    subgraph DataProcessing["DATA PROCESSING LAYER"]
        OCR[Tesseract OCR<br/>Arabic + English]
        PDF[PyMuPDF<br/>PDF Parser]
        Excel[Pandas<br/>Excel Parser]
    end

    %% ML/AI Layer
    subgraph ML["MACHINE LEARNING LAYER"]
        XGBModel[XGBoost v4 Primary<br/>12 Features • 85% Accuracy]
        RFModel[Random Forest v3 Fallback<br/>12 Features • 83% Accuracy]
        Fallback[Model Fallback Chain<br/>XGBoost v4 → RF v3 → v2 → Rule-Based]
        LLM[Mistral-7B-Instruct-v0.2<br/>Ollama Local Hosting]
        Embeddings[Cohere embed-english-v3.0<br/>384-Dimensional Vectors]
        
        XGBModel --> Fallback
        RFModel --> Fallback
    end

    %% Database Layer
    subgraph Databases["DATA STORAGE LAYER - Hybrid 4-Database Architecture"]
        DB1[(SQLite<br/>ACID Compliance<br/>Application Records<br/>Audit Trails)]
        DB2[(TinyDB<br/>Document Cache<br/>TTL Expiration<br/>Session State)]
        DB3[(ChromaDB<br/>Vector Database<br/>Semantic Search<br/>RAG Backend)]
        DB4[(NetworkX<br/>Graph Database<br/>Relationships<br/>Program Networks)]
        
        DBManager[Unified Database Manager<br/>L1 Cache: Memory<br/>L2 Cache: TinyDB<br/>L3 Storage: SQLite]
        
        DBManager --> DB1
        DBManager --> DB2
        DBManager --> DB3
        DBManager --> DB4
    end

    %% Observability Layer
    subgraph Observability["OBSERVABILITY & GOVERNANCE LAYER"]
        Langfuse[Langfuse Tracing<br/>Token Usage • Cost Tracking]
        Audit[Audit Logger<br/>Complete Action Trail]
        Metrics[Performance Metrics<br/>Response Time • Error Rate]
        
        Langfuse --> AuditDB[(Audit Database<br/>Compliance Records)]
        Audit --> AuditDB
        Metrics --> AuditDB
    end

    %% Connections between layers
    API --> MO
    
    Agent1 --> OCR
    Agent1 --> PDF
    Agent1 --> Excel
    
    Agent3 --> XGBModel
    Agent3 --> RFModel
    Agent5 --> LLM
    Agent6 --> LLM
    Agent6 --> Embeddings
    Agent6 --> DB3
    
    MO --> DBManager
    Agents --> DBManager
    
    MO --> Langfuse
    Agents --> Audit
    API --> Metrics

    %% Apply styles
    class UI,API presentation
    class MO,Pipeline orchestration
    class Agent1,Agent2,Agent3,Agent4,Agent5,Agent6 agents
    class DB1,DB2,DB3,DB4,DBManager data
    class RFModel,Fallback,LLM,Embeddings,OCR,PDF,Excel ml
    class Langfuse,Audit,Metrics,AuditDB observability
```

---

## Data Flow Diagram - Application Processing Pipeline

```mermaid
flowchart TD
    Start([User Uploads Documents]) --> Upload[Document Upload<br/>PDF • JPEG • XLSX]
    
    Upload --> Extract[STAGE 1: EXTRACTION<br/>60 seconds<br/><br/>Multi-Modal Processing:<br/>OCR for scanned docs<br/>PDF parsing<br/>Excel analysis<br/>Confidence scoring]
    
    Extract --> Validate[STAGE 2: VALIDATION<br/>30 seconds<br/><br/>Cross-Document Checks:<br/>Identity verification 95% threshold<br/>Financial consistency<br/>Completeness assessment<br/>Issue ranking]
    
    Validate --> Eligible[STAGE 3: ELIGIBILITY<br/>45 seconds<br/><br/>ML Assessment:<br/>XGBoost v4 primary inference<br/>Random Forest v3 fallback<br/>12-feature extraction<br/>Confidence scoring<br/>Hybrid ML + rules]
    
    Eligible --> Recommend[STAGE 4: RECOMMENDATION<br/>30 seconds<br/><br/>Decision Generation:<br/>Support amount AED 500-5000<br/>Program matching 7 initiatives<br/>Priority ranking<br/>Decision category]
    
    Recommend --> Explain[STAGE 5: EXPLANATION<br/>45 seconds<br/><br/>Justification:<br/>Natural language generation<br/>Personalized guidance<br/>Appeals information<br/>Empathetic tone]
    
    Explain --> Decision{Decision<br/>Confidence}
    
    Decision -->|High > 70%| AutoApprove[Automated Decision<br/>APPROVED / CONDITIONAL / REJECTED]
    Decision -->|Low < 70%| HumanReview[Human Review Required<br/>Edge Case Handling]
    
    AutoApprove --> Results[Results Display<br/>Decision banner<br/>Support amount<br/>Recommended programs<br/>Reasoning]
    HumanReview --> Results
    
    Results --> Chat[INTERACTIVE SUPPORT<br/>RAG Chatbot<br/><br/>On-Demand Q&A:<br/>Semantic search<br/>Contextual responses<br/>Session management<br/>Audit trail]
    
    Chat --> End([Complete Process<br/>Total Time: 4-5 minutes])

    %% Styling
    classDef stage fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef decision fill:#fff3e0,stroke:#e65100,stroke-width:3px
    classDef endpoint fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    
    class Extract,Validate,Eligible,Recommend,Explain stage
    class Decision decision
    class Start,End,Results,Chat endpoint
```

---

## Database Architecture Diagram

```mermaid
graph TB
    subgraph Application["APPLICATION LAYER"]
        App[Agents + Orchestrator]
    end
    
    App --> UDM[Unified Database Manager<br/>Polyglot Persistence Coordinator]
    
    subgraph Cache["CACHE HIERARCHY"]
        L1[L1 Cache: In-Memory<br/>Hot Data • <1ms Access]
        L2[L2 Cache: TinyDB<br/>Session State • <20ms Access]
        L3[L3 Storage: SQLite<br/>Persistent Data • <10ms Access]
        
        L1 -->|Miss| L2
        L2 -->|Miss| L3
    end
    
    UDM --> L1
    
    subgraph Relational["RELATIONAL DATABASE"]
        SQLite[(SQLite<br/>━━━━━━━━━<br/>ACID Compliance<br/>━━━━━━━━━<br/>TABLES:<br/>applications<br/>documents<br/>decisions<br/>audit_log<br/>━━━━━━━━━<br/>FEATURES:<br/>WAL mode<br/>Foreign keys<br/>Transactions<br/>50KB/app)]
    end
    
    subgraph Document["DOCUMENT STORE"]
        TinyDB[(TinyDB<br/>━━━━━━━━━<br/>JSON Flexibility<br/>━━━━━━━━━<br/>COLLECTIONS:<br/>validation_reports<br/>session_cache<br/>temp_documents<br/>━━━━━━━━━<br/>FEATURES:<br/>TTL expiration<br/>Nested queries<br/>Schemaless<br/>20ms queries)]
    end
    
    subgraph Vector["VECTOR DATABASE"]
        ChromaDB[(ChromaDB<br/>━━━━━━━━━<br/>Semantic Search<br/>━━━━━━━━━<br/>COLLECTIONS:<br/>app_summaries<br/>decisions<br/>documents<br/>chat_context<br/>━━━━━━━━━<br/>FEATURES:<br/>384-dim vectors<br/>HNSW index<br/>Cosine similarity<br/><200ms retrieval)]
    end
    
    subgraph Graph["GRAPH DATABASE"]
        NetworkX[(NetworkX<br/>━━━━━━━━━<br/>Relationships<br/>━━━━━━━━━<br/>NODES:<br/>Applications<br/>Persons<br/>Programs<br/>Decisions<br/>━━━━━━━━━<br/>FEATURES:<br/>In-memory<br/>Path finding<br/>Neo4j export<br/><50ms queries)]
    end
    
    UDM --> SQLite
    UDM --> TinyDB
    UDM --> ChromaDB
    UDM --> NetworkX
    
    subgraph Performance["PERFORMANCE METRICS"]
        Perf[━━━━━━━━━━━━━━━━━━━<br/>Read Latency:<br/>L1 Cache: <1ms<br/>L2 Cache: <20ms<br/>SQLite: <10ms<br/>ChromaDB: <200ms<br/>━━━━━━━━━━━━━━━━━━━<br/>Write Latency:<br/>SQLite: <50ms<br/>TinyDB: <30ms<br/>━━━━━━━━━━━━━━━━━━━<br/>Storage:<br/>1GB per 1000 apps<br/>70%+ cache hit rate]
    end
    
    classDef db fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef cache fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef manager fill:#e1f5ff,stroke:#01579b,stroke-width:3px
    
    class SQLite,TinyDB,ChromaDB,NetworkX db
    class L1,L2,L3 cache
    class UDM manager
```

---

## Agent Interaction Diagram

```mermaid
sequenceDiagram
    participant User
    participant API as FastAPI Backend
    participant Orch as Master Orchestrator
    participant Extract as Extraction Agent
    participant Valid as Validation Agent
    participant Elig as Eligibility Agent
    participant Rec as Recommendation Agent
    participant Exp as Explanation Agent
    participant DB as Database Layer
    participant LF as Langfuse Tracing

    User->>API: POST /api/applications/{id}/process
    API->>LF: Start trace
    API->>Orch: Process application
    
    Orch->>LF: Span: Extraction
    Orch->>Extract: Extract documents
    Extract->>DB: Store extracted data
    Extract->>Orch: ExtractedData + confidence
    
    Orch->>LF: Span: Validation
    Orch->>Valid: Validate data
    Valid->>DB: Query for consistency checks
    Valid->>Orch: ValidationReport + issues
    
    Orch->>LF: Span: Eligibility
    Orch->>Elig: Assess eligibility
    Elig->>DB: Load ML model
    Elig->>Orch: EligibilityResult + confidence
    
    alt High Confidence >= 70%
        Orch->>LF: Span: Recommendation
        Orch->>Rec: Generate recommendation
        Rec->>DB: Query program catalog
        Rec->>Orch: Recommendation + programs
        
        Orch->>LF: Span: Explanation
        Orch->>Exp: Generate explanation
        Exp->>DB: Store decision
        Exp->>Orch: Explanation text
    else Low Confidence < 70%
        Orch->>Orch: Flag for human review
    end
    
    Orch->>DB: Save complete results
    Orch->>LF: End trace
    Orch->>API: Processing complete
    API->>User: 200 OK + application_id
    
    User->>API: GET /api/applications/{id}/results
    API->>DB: Query results
    DB->>API: Complete assessment
    API->>User: Decision + reasoning + programs
    
    Note over User,LF: Interactive Chatbot (Optional)
    User->>API: POST /api/applications/{id}/chat
    API->>DB: Query ChromaDB for context
    DB->>API: Similar cases + application data
    API->>Exp: Generate response (RAG)
    Exp->>API: Contextual answer
    API->>User: Chatbot response
```

---

## Technology Stack Diagram

```mermaid
mindmap
  root((UAE Social Support<br/>AI Platform))
    Programming
      Python 3.11+
        Async/Await
        Type Hints
        Error Handling
    
    AI/ML
      Local LLM
        Mistral-7B-Instruct-v0.2
        Ollama Hosting
        Data Sovereignty
      
      Embeddings
        Cohere embed-english-v3.0
        384 Dimensions
        Semantic Search
      
      ML Model
        XGBoost v4 Primary
        Random Forest v3 Fallback
        12 Features
        85% Accuracy XGBoost
        83% Accuracy RF
        Fallback Chain
    
    Backend
      FastAPI 0.104+
        29 Endpoints
        Async REST
        Auto Documentation
        Pydantic Validation
      
      Orchestration
        LangGraph StateGraph
        Typed State Management
        Conditional Routing
        Error Recovery
    
    Databases
      Relational
        SQLite
        ACID Compliance
        WAL Mode
      
      Document
        TinyDB
        JSON Storage
        TTL Cache
      
      Vector
        ChromaDB
        Semantic Search
        HNSW Index
      
      Graph
        NetworkX
        Relationships
        Neo4j Compatible
    
    Frontend
      Streamlit 1.28+
        Interactive UI
        Real-time Updates
        Multi-page App
        Plotly Charts
    
    Observability
      Langfuse
        Distributed Tracing
        Token Tracking
        Cost Management
      
      Audit Logging
        Complete Trail
        Compliance Ready
        Performance Metrics
```

---

## Deployment Architecture (Future State)

```mermaid
graph TB
    subgraph Internet["INTERNET"]
        Users[End Users<br/>Applicants + Admins]
    end
    
    subgraph CDN["CONTENT DELIVERY NETWORK"]
        CF[CloudFront<br/>Static Assets]
    end
    
    subgraph LoadBalancer["LOAD BALANCING"]
        ALB[Application Load Balancer<br/>SSL Termination<br/>Health Checks]
    end
    
    subgraph K8S["KUBERNETES CLUSTER"]
        subgraph Frontend["Frontend Pods"]
            ST1[Streamlit Pod 1]
            ST2[Streamlit Pod 2]
            ST3[Streamlit Pod 3]
        end
        
        subgraph Backend["Backend Pods"]
            API1[FastAPI Pod 1]
            API2[FastAPI Pod 2]
            API3[FastAPI Pod 3]
        end
        
        subgraph Workers["Worker Pods"]
            W1[Celery Worker 1<br/>Document Processing]
            W2[Celery Worker 2<br/>ML Inference]
            W3[Celery Worker 3<br/>Report Generation]
        end
    end
    
    subgraph Cache["CACHING LAYER"]
        Redis[Redis Cluster<br/>Session State<br/>Query Cache<br/>Rate Limiting]
    end
    
    subgraph Queue["MESSAGE QUEUE"]
        RabbitMQ[RabbitMQ<br/>Task Queue<br/>Event Stream]
    end
    
    subgraph Database["DATABASE LAYER"]
        PG[(PostgreSQL<br/>Primary + Replica<br/>Application Data)]
        Chroma[(ChromaDB<br/>Vector Search)]
        Neo4j[(Neo4j<br/>Graph Analytics)]
    end
    
    subgraph Storage["OBJECT STORAGE"]
        S3[S3 Buckets<br/>Documents<br/>Models<br/>Backups]
    end
    
    subgraph Monitoring["MONITORING & OBSERVABILITY"]
        Prom[Prometheus<br/>Metrics Collection]
        Graf[Grafana<br/>Dashboards]
        ELK[ELK Stack<br/>Log Aggregation]
    end
    
    Users --> CF
    Users --> ALB
    CF --> ALB
    
    ALB --> ST1
    ALB --> ST2
    ALB --> ST3
    
    ST1 & ST2 & ST3 --> API1 & API2 & API3
    
    API1 & API2 & API3 --> Redis
    API1 & API2 & API3 --> RabbitMQ
    API1 & API2 & API3 --> PG
    API1 & API2 & API3 --> Chroma
    
    RabbitMQ --> W1 & W2 & W3
    W1 & W2 & W3 --> PG
    W1 & W2 & W3 --> S3
    W1 & W2 & W3 --> Neo4j
    
    K8S --> Prom
    Prom --> Graf
    K8S --> ELK
    
    classDef infra fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef data fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef monitor fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    
    class ALB,CF,K8S,Redis,RabbitMQ,S3 infra
    class PG,Chroma,Neo4j data
    class Prom,Graf,ELK monitor
```

---

## How to Use These Diagrams

### Option 1: Render in GitHub
1. Create a file `ARCHITECTURE_DIAGRAM.md` in your repository
2. Copy the Mermaid code blocks above
3. Push to GitHub - it will render automatically

### Option 2: Export to PNG/PDF
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Export to PNG
mmdc -i ARCHITECTURE_DIAGRAM.md -o architecture.png -w 2400

# Export to PDF
mmdc -i ARCHITECTURE_DIAGRAM.md -o architecture.pdf -w 2400
```

### Option 3: Use Online Renderer
1. Visit https://mermaid.live
2. Paste the Mermaid code
3. Download as SVG, PNG, or PDF
4. Customize styling and colors as needed

### Option 4: VS Code Preview
1. Install "Markdown Preview Mermaid Support" extension
2. Open this file in VS Code
3. Press `Ctrl+Shift+V` (Windows/Linux) or `Cmd+Shift+V` (Mac)
4. View rendered diagrams in preview pane

---

## Diagram Descriptions

**Full System Architecture**: Complete 6-layer architecture showing all components and their interactions

**Data Flow Diagram**: Step-by-step processing pipeline from document upload to final decision

**Database Architecture**: Detailed view of the 4-database hybrid strategy with cache hierarchy

**Agent Interaction Diagram**: Sequence diagram showing agent coordination and message passing

**Technology Stack Diagram**: Mind map of all technologies organized by category

**Deployment Architecture**: Future-state production deployment with Kubernetes and cloud services

---



