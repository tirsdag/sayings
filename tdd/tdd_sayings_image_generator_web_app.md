```markdown
# Technical Design Document (TDD)
## Project: Sayings Image Generator Web Application

## 1. Overview
This project is a web-based application for managing a list of sayings (CRUD) and generating images based on each saying using an AI image generation prompt. Each saying has an editable prompt, and the saying text must be injected into the prompt when generating an image.

The application must be easy to deploy and run inside a Docker container. A generated Markdown deployment guide must be included.

---

## 2. Functional Requirements

### 2.1 Sayings Management (CRUD)
- Create, read, update, and delete sayings.
- Each saying record must contain:
  - `saying` (string)
  - `prompt` (string, must support placeholder `%1` for the saying text)
  - `image_url` or `image_path` (string, generated file reference)

### 2.2 Image Generation
- A **Generate** action triggers image creation for a specific saying.
- The system must replace `%1` in the prompt with the saying text before sending to the image generator.
- Generated images must be stored and linked to the saying.
- Users must be able to preview and download the latest generated image.

### 2.3 Context Markdown File
- A markdown file (`context.md`) must contain global instructions for image generation (style, constraints, formatting rules).
- The generation pipeline must prepend this context to the saying prompt.

### 2.4 API Format
The system must support importing/exporting sayings in the following JSON structure:

```json
{
  "sayings": [
    {
      "saying": "Håber er løsegrønt",
      "prompt": "dsfiuodo %1"
    },
    {
      "saying": "Det er helt naturligt",
      "prompt": "dsdsdsfiuodo %1"
    }
  ]
}
```

---

## 3. Non-Functional Requirements
- Easy to deploy with Docker.
- Minimal dependencies.
- Runs as a single container.
- REST API + simple web UI.
- Image generation should be pluggable (OpenAI, Stable Diffusion, local API, etc.).

---

## 4. Architecture

### 4.1 Components
1. **Frontend**: Simple React or vanilla HTML/JS UI.
2. **Backend API**: Node.js (Express) or Python (FastAPI).
3. **Storage**:
   - SQLite database for sayings metadata.
   - File system storage for generated images.
4. **Image Generation Service**:
   - Wrapper module calling an AI image generation API.
5. **Docker Runtime**.

### 4.2 Data Flow
1. User edits saying and prompt.
2. User clicks Generate.
3. Backend loads `context.md`.
4. Backend replaces `%1` with saying text.
5. Backend sends final prompt to image generator.
6. Image is saved and linked to the saying.

---

## 5. Database Schema

### Table: `sayings`
| Field | Type | Description |
|--------|------|-------------|
| id | integer | Primary key |
| saying | text | The saying text |
| prompt | text | Prompt template |
| image_path | text | Path to latest generated image |
| updated_at | datetime | Last update timestamp |

---

## 6. Backend API Endpoints

### Sayings CRUD
- `GET /api/sayings`
- `POST /api/sayings`
- `PUT /api/sayings/{id}`
- `DELETE /api/sayings/{id}`

### Image Generation
- `POST /api/sayings/{id}/generate`

### File Serving
- `GET /images/{filename}`

---

## 7. Prompt Construction Logic

```text
final_prompt = context_md + "\n" + prompt.replace("%1", saying)
```

---

## 8. Docker Design

### 8.1 Dockerfile (Backend Example: Python FastAPI)
```Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 8.2 Docker Compose (Optional)
```yaml
version: "3.9"
services:
  app:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
```

---

## 9. Deployment Guide (Generated Markdown)

### 9.1 Build Image
```bash
docker build -t sayings-app .
```

### 9.2 Run Container
```bash
docker run -p 8080:8080 -v $(pwd)/data:/app/data sayings-app
```

### 9.3 Access Application
- Web UI: `http://localhost:8080`
- API Docs: `http://localhost:8080/docs`

---

## 10. Security & Configuration
- Store API keys in environment variables.
- `.env` file for local development.

---

## 11. Future Enhancements
- Versioned image history per saying.
- Bulk import/export JSON.
- Prompt templates library.
- Authentication.

---

## 12. Deliverables
- Source code repository.
- Dockerfile and docker-compose.yml.
- context.md file.
- Deployment markdown guide.
- Sample JSON dataset.

```

