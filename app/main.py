from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, Integer, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from app.services.generator import ImageGenerator

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = DATA_DIR / "images"
DB_PATH = DATA_DIR / "sayings.db"
CONTEXT_PATH = BASE_DIR / "context.md"

DATA_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Saying(Base):
    __tablename__ = "sayings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    saying: Mapped[str] = mapped_column(Text, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


Base.metadata.create_all(engine)


class SayingCreate(BaseModel):
    saying: str = Field(min_length=1)
    prompt: str = Field(min_length=1)


class SayingUpdate(BaseModel):
    saying: str = Field(min_length=1)
    prompt: str = Field(min_length=1)


class SayingOut(BaseModel):
    id: int
    saying: str
    prompt: str
    image_path: str | None
    updated_at: datetime


class ImportExportItem(BaseModel):
    saying: str
    prompt: str


class ImportPayload(BaseModel):
    sayings: list[ImportExportItem]


class ExportPayload(BaseModel):
    sayings: list[ImportExportItem]


app = FastAPI(title="Sayings Image Generator", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

generator = ImageGenerator(images_dir=IMAGES_DIR)


def to_out(model: Saying) -> SayingOut:
    return SayingOut(
        id=model.id,
        saying=model.saying,
        prompt=model.prompt,
        image_path=model.image_path,
        updated_at=model.updated_at,
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(BASE_DIR / "app" / "static" / "index.html")


@app.get("/api/sayings", response_model=list[SayingOut])
def list_sayings() -> list[SayingOut]:
    with Session(engine) as session:
        rows = session.execute(select(Saying).order_by(Saying.id.asc())).scalars().all()
        return [to_out(r) for r in rows]


@app.post("/api/sayings", response_model=SayingOut, status_code=201)
def create_saying(payload: SayingCreate) -> SayingOut:
    now = datetime.utcnow()
    with Session(engine) as session:
        row = Saying(saying=payload.saying, prompt=payload.prompt, updated_at=now)
        session.add(row)
        session.commit()
        session.refresh(row)
        return to_out(row)


@app.put("/api/sayings/{saying_id}", response_model=SayingOut)
def update_saying(saying_id: int, payload: SayingUpdate) -> SayingOut:
    with Session(engine) as session:
        row = session.get(Saying, saying_id)
        if not row:
            raise HTTPException(status_code=404, detail="Saying not found")
        row.saying = payload.saying
        row.prompt = payload.prompt
        row.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(row)
        return to_out(row)


@app.delete("/api/sayings/{saying_id}", status_code=204, response_class=Response)
def delete_saying(saying_id: int) -> Response:
    with Session(engine) as session:
        row = session.get(Saying, saying_id)
        if not row:
            raise HTTPException(status_code=404, detail="Saying not found")
        if row.image_path:
            maybe_image = BASE_DIR / row.image_path.lstrip("/")
            if maybe_image.exists():
                maybe_image.unlink(missing_ok=True)
        session.delete(row)
        session.commit()
    return Response(status_code=204)


@app.post("/api/sayings/{saying_id}/generate", response_model=SayingOut)
def generate_saying_image(saying_id: int) -> SayingOut:
    context_md = CONTEXT_PATH.read_text(encoding="utf-8") if CONTEXT_PATH.exists() else ""

    with Session(engine) as session:
        row = session.get(Saying, saying_id)
        if not row:
            raise HTTPException(status_code=404, detail="Saying not found")

        final_prompt = f"{context_md}\n{row.prompt.replace('%1', row.saying)}".strip()
        try:
            new_image_path = generator.generate_image(saying_id=row.id, prompt=final_prompt)
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Image generation failed: {exc}") from exc
        row.image_path = f"/images/{new_image_path.name}"
        row.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(row)
        return to_out(row)


@app.get("/api/export", response_model=ExportPayload)
def export_sayings() -> ExportPayload:
    with Session(engine) as session:
        rows = session.execute(select(Saying).order_by(Saying.id.asc())).scalars().all()
        return ExportPayload(sayings=[ImportExportItem(saying=r.saying, prompt=r.prompt) for r in rows])


@app.post("/api/import", response_model=list[SayingOut])
def import_sayings(payload: ImportPayload) -> list[SayingOut]:
    imported: list[SayingOut] = []
    with Session(engine) as session:
        for item in payload.sayings:
            row = Saying(
                saying=item.saying,
                prompt=item.prompt,
                updated_at=datetime.utcnow(),
            )
            session.add(row)
            session.flush()
            imported.append(to_out(row))
        session.commit()
    return imported
