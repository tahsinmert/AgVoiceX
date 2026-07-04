from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.prompts import PromptCreate, PromptRead, PromptUpdate
from app.services.prompts import PromptService

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("", response_model=list[PromptRead])
def list_prompts(organization_id: int | None = None, db: Session = Depends(get_db)) -> list[PromptRead]:
    return PromptService(db).list(organization_id)


@router.post("", response_model=PromptRead, status_code=201)
def create_prompt(payload: PromptCreate, db: Session = Depends(get_db)) -> PromptRead:
    try:
        prompt = PromptService(db).create(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(prompt)
    return prompt


@router.patch("/{prompt_id}", response_model=PromptRead)
def update_prompt(prompt_id: int, payload: PromptUpdate, db: Session = Depends(get_db)) -> PromptRead:
    prompt = PromptService(db).update(prompt_id, payload)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")
    db.commit()
    db.refresh(prompt)
    return prompt
