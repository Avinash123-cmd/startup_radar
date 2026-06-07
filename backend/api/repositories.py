from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import math
from database.db import get_db
from database.crud import get_repositories, get_repository_history, get_repository_languages
from database.schemas import PaginatedRepositories, RepositoryHistoryOut

router = APIRouter(tags=["Repositories"])

@router.get("/repositories", response_model=PaginatedRepositories)
def read_repositories(
    category_id: Optional[int] = Query(None, description="Filter by Category ID"),
    language: Optional[str] = Query(None, description="Filter by coding language"),
    search: Optional[str] = Query(None, description="Search term across name/desc"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("stars", description="Column to sort by"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db)
):
    skip = (page - 1) * limit
    items, total = get_repositories(
        db=db,
        category_id=category_id,
        language=language,
        search=search,
        skip=skip,
        limit=limit,
        sort_by=sort_by,
        order=order
    )
    
    pages = math.ceil(total / limit) if total > 0 else 1
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages
    }

@router.get("/repositories/{repo_id}/history", response_model=List[RepositoryHistoryOut])
def read_repo_history(repo_id: int, db: Session = Depends(get_db)):
    history = get_repository_history(db, repo_id=repo_id)
    if not history:
        raise HTTPException(status_code=404, detail="Star history not found for this repository")
    return history

@router.get("/repositories/languages", response_model=List[str])
def read_languages(db: Session = Depends(get_db)):
    return get_repository_languages(db)
