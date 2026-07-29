from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ShowList, ShowListItem, User
from ..schemas import (
    AddShowToListRequest,
    CreateListRequest,
    ListedShow,
    RenameListRequest,
    ShowListDetailOut,
    ShowListOut,
)
from ..security import get_current_user
from ..services import tvmaze

router = APIRouter(prefix="/lists", tags=["lists"])


def _get_owned_list(db: Session, user: User, list_id: int) -> ShowList:
    show_list = (
        db.query(ShowList).filter_by(id=list_id, user_id=user.id).first()
    )
    if not show_list:
        raise HTTPException(status_code=404, detail="List not found")
    return show_list


@router.post("", response_model=ShowListOut, status_code=201)
def create_list(
    payload: CreateListRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    show_list = ShowList(user_id=user.id, name=payload.name)
    db.add(show_list)
    db.commit()
    db.refresh(show_list)
    return show_list


@router.get("", response_model=list[ShowListOut])
def list_lists(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return db.query(ShowList).filter_by(user_id=user.id).all()


@router.get("/{list_id}", response_model=ShowListDetailOut)
async def get_list(
    list_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    show_list = _get_owned_list(db, user, list_id)
    items = (
        db.query(ShowListItem)
        .filter_by(list_id=show_list.id)
        .order_by(ShowListItem.added_at)
        .all()
    )

    shows = []
    for item in items:
        show = await tvmaze.get_show(item.tvmaze_show_id)
        shows.append(
            ListedShow(
                tvmaze_show_id=show.id,
                name=show.name,
                image=show.image,
                status=show.status,
                added_at=item.added_at,
            )
        )

    return ShowListDetailOut(
        id=show_list.id,
        name=show_list.name,
        created_at=show_list.created_at,
        is_public=show_list.is_public,
        shows=shows,
    )


@router.put("/{list_id}", response_model=ShowListOut)
def rename_list(
    list_id: int,
    payload: RenameListRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    show_list = _get_owned_list(db, user, list_id)
    show_list.name = payload.name
    db.commit()
    db.refresh(show_list)
    return show_list


@router.delete("/{list_id}", status_code=204)
def delete_list(
    list_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    show_list = _get_owned_list(db, user, list_id)
    db.delete(show_list)
    db.commit()


@router.post("/{list_id}/shows", status_code=201)
def add_show_to_list(
    list_id: int,
    payload: AddShowToListRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    show_list = _get_owned_list(db, user, list_id)

    existing = (
        db.query(ShowListItem)
        .filter_by(list_id=show_list.id, tvmaze_show_id=payload.tvmaze_show_id)
        .first()
    )
    if existing:
        return {"tvmaze_show_id": existing.tvmaze_show_id, "added_at": existing.added_at}

    item = ShowListItem(list_id=show_list.id, tvmaze_show_id=payload.tvmaze_show_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"tvmaze_show_id": item.tvmaze_show_id, "added_at": item.added_at}


@router.delete("/{list_id}/shows/{tvmaze_show_id}", status_code=204)
def remove_show_from_list(
    list_id: int,
    tvmaze_show_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    show_list = _get_owned_list(db, user, list_id)
    db.query(ShowListItem).filter_by(
        list_id=show_list.id, tvmaze_show_id=tvmaze_show_id
    ).delete()
    db.commit()
