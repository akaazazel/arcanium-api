import random

import pytest
from app.core.exceptions import NoteNotFoundError
from app.models.models import *
from app.services.notes import (
    create_note,
    delete_note,
    get_note,
    get_notes,
    update_note,
)
from app.utils.notes import decrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_services.test_services_notes.fixtures import (
    db,
    init_db,
    insert_user_and_note_factory,
)
from tests.test_services.test_services_notes.utils import (
    add_to_db,
    get_note_model,
    get_user_model,
    note_factory,
    user_factory,
)


@pytest.mark.asyncio
async def test_create_notes(db: AsyncSession):
    user = get_user_model(user_factory("user01"))

    await add_to_db(db, [user])  # creates user

    note = note_factory(1)

    # test: Create a new note
    note_id = await create_note(note_data=note, user_id=user.id, db=db)

    # verify: Fetch created note
    result = await db.execute(select(Note).where(Note.id == note_id))
    fetched_note = result.scalar_one_or_none()

    assert fetched_note is not None
    assert decrypt(fetched_note.title) == note.title
    assert decrypt(fetched_note.content) == note.content
    assert fetched_note.owner == 1
    assert fetched_note.created_at is not None
    assert fetched_note.updated_at is not None
    assert fetched_note.updated_at == fetched_note.created_at


@pytest.mark.asyncio
async def test_create_notes_no_user(db: AsyncSession):
    note = note_factory(1)

    with pytest.raises(IntegrityError):
        await create_note(note_data=note, user_id=1, db=db)

    await db.rollback()


@pytest.mark.asyncio
async def test_get_note(db: AsyncSession, insert_user_and_note_factory):
    user_id = 1
    note_id = 1

    result = await insert_user_and_note_factory(user_id=user_id, note_id=note_id, db=db)
    note = result[1]

    fetched_note = await get_note(note_id=note.id, user_id=user_id, db=db)

    assert fetched_note is not None
    assert fetched_note.id == note.id
    assert decrypt(fetched_note.title) == decrypt(note.title)
    assert decrypt(fetched_note.content) == decrypt(note.content)
    assert fetched_note.owner == user_id
    assert fetched_note.created_at == fetched_note.updated_at


@pytest.mark.asyncio
async def test_get_note_not_exists(db: AsyncSession):

    with pytest.raises(NoteNotFoundError):
        await get_note(note_id=1, user_id=1, db=db)


@pytest.mark.asyncio
async def test_get_forbidden_note(db: AsyncSession, insert_user_and_note_factory):
    user_id_1 = 1
    user_id_2 = 2
    note_id = 1

    await insert_user_and_note_factory(user_id=user_id_1, note_id=note_id, db=db)

    fetched_note = await get_note(
        note_id=note_id, user_id=user_id_1, db=db
    )  # fetch note by original user

    assert fetched_note.id == note_id
    assert fetched_note.owner == user_id_1

    # if we access a note of different user
    with pytest.raises(NoteNotFoundError):
        await get_note(note_id=note_id, user_id=user_id_2, db=db)


@pytest.mark.asyncio
@pytest.mark.parametrize("sort", ["date_created", "date_updated"])
@pytest.mark.parametrize("order", ["asc", "desc"])
async def test_get_multiple_notes(db: AsyncSession, sort, order):
    user_id_1 = 1
    user1 = get_user_model(user_factory(), user_id_1)
    note_id_start = 1
    note_id_end = 5

    notes = []

    for i in range(note_id_start, note_id_end + 1):
        notes.append(get_note_model(note_factory(i), user_id_1, True, i, i))

    randomized_notes = notes.copy()
    random.shuffle(randomized_notes)

    await add_to_db(db=db, data=[user1])  # add user
    await add_to_db(db=db, data=randomized_notes)  # add notes

    fetched_notes = await get_notes(
        user_id=user_id_1,
        db=db,
        sort=sort,
        order=order,
        limit=10,
        offset_id=None,
        offset_date=None,
    )

    assert fetched_notes is not None

    is_asc = True if order == "asc" else False
    is_created_at = True if sort == "date_created" else False

    index = note_id_start - 1 if is_asc else note_id_end - 1
    for fetched_note in fetched_notes:
        assert (
            (fetched_note.created_at == notes[index].created_at)
            if is_created_at
            else (fetched_note.updated_at == notes[index].updated_at)
        )

        assert fetched_note.id == notes[index].id

        if is_asc:
            index += 1
        else:
            index -= 1


@pytest.mark.asyncio
@pytest.mark.parametrize("order", ["asc", "desc"])
async def test_get_notes_pagination(db: AsyncSession, order):

    user_id = 1
    user = get_user_model(user_factory(), user_id)

    note_id_start = 1
    note_id_end = 10
    total_notes = note_id_end + 1 - note_id_start

    notes_list = [
        get_note_model(
            note_factory(), owner=user_id, is_encrypt=True, id=i, time_delta_day=i
        )
        for i in range(note_id_start, note_id_end + 1)
    ]

    await add_to_db(db, [user])
    await add_to_db(db, notes_list)

    offset_date = None
    offset_id = None
    limit = 2
    fetched_notes = []
    for _ in range(note_id_start, int(total_notes / 2) + 1):

        result = await get_notes(
            user_id=user_id,
            db=db,
            sort="date_created",
            order=order,
            limit=limit,
            offset_date=offset_date,
            offset_id=offset_id,
        )

        fetched_notes.extend(result)

        offset_date = result[limit - 1].created_at
        offset_id = result[limit - 1].id

    assert len(fetched_notes) == total_notes

    index = 0
    notes_list.reverse() if order == "desc" else notes_list
    for fetched_note in fetched_notes:
        assert fetched_note.id == notes_list[index].id
        index += 1


@pytest.mark.asyncio
async def test_update_notes(db: AsyncSession, insert_user_and_note_factory):
    user_id = 1
    note_id = 1
    response = await insert_user_and_note_factory(user_id, note_id, db)

    new_note_data = note_factory(2)
    await update_note(user_id=user_id, note_id=note_id, note_data=new_note_data, db=db)

    result = await db.execute(select(Note).where(Note.id == note_id))
    fetched_note = result.scalar_one_or_none()

    assert fetched_note is not None
    assert fetched_note.id == note_id
    assert decrypt(fetched_note.title) == new_note_data.title
    assert decrypt(fetched_note.content) == new_note_data.content
    assert fetched_note.created_at < fetched_note.updated_at


@pytest.mark.asyncio
async def test_delete_note(db: AsyncSession, insert_user_and_note_factory):
    user_id = 1
    note_id = 1
    response = await insert_user_and_note_factory(user_id, note_id, db)

    await delete_note(note_id=note_id, user_id=user_id, db=db)

    result = await db.execute(select(Note).where(Note.id == note_id))
    fetched_note = result.scalar_one_or_none()

    assert fetched_note is None
