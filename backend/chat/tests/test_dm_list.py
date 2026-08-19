import pytest

from chat.models import Message


def _open_dm(client, user_id):
    return client.post("/api/dm/", {"user_id": user_id}, format="json").data


@pytest.mark.django_db
def test_list_dms_with_other_user_and_last_message(make_user, client_for):
    me = make_user("me@example.com")
    other = make_user("other@example.com")
    dm = _open_dm(client_for(me), other.id)
    client_for(me).post(
        "/api/messages/", {"channel": dm["id"], "content": "hey there"}, format="json"
    )
    listing = client_for(me).get("/api/dm/").data
    assert len(listing) == 1
    assert listing[0]["other_user"]["id"] == other.id
    assert listing[0]["last_message"]["content"] == "hey there"


@pytest.mark.django_db
def test_list_dms_ordered_by_recent_activity(make_user, client_for):
    me = make_user("me@example.com")
    a = make_user("a@example.com")
    b = make_user("b@example.com")
    client = client_for(me)
    dm_a = _open_dm(client, a.id)
    dm_b = _open_dm(client, b.id)
    # newest activity in dm_b
    client.post("/api/messages/", {"channel": dm_a["id"], "content": "old"}, format="json")
    client.post("/api/messages/", {"channel": dm_b["id"], "content": "new"}, format="json")
    ids = [d["id"] for d in client.get("/api/dm/").data]
    assert ids[0] == dm_b["id"]


@pytest.mark.django_db
def test_both_participants_can_message_in_dm(make_user, client_for):
    me = make_user("me@example.com")
    other = make_user("other@example.com")
    dm = _open_dm(client_for(me), other.id)
    r1 = client_for(me).post(
        "/api/messages/", {"channel": dm["id"], "content": "hi"}, format="json"
    )
    r2 = client_for(other).post(
        "/api/messages/", {"channel": dm["id"], "content": "hello"}, format="json"
    )
    assert r1.status_code == 201 and r2.status_code == 201
    contents = [
        m["content"]
        for m in client_for(other).get(f"/api/messages/?channel={dm['id']}").data["results"]
    ]
    assert set(contents) == {"hi", "hello"}


@pytest.mark.django_db
def test_non_participant_cannot_access_dm_messages(make_user, client_for):
    me = make_user("me@example.com")
    other = make_user("other@example.com")
    outsider = make_user("out@example.com")
    dm = _open_dm(client_for(me), other.id)
    response = client_for(outsider).get(f"/api/messages/?channel={dm['id']}")
    assert response.status_code == 404


@pytest.mark.django_db
def test_dm_channel_admin_routes_404(make_user, client_for):
    me = make_user("me@example.com")
    other = make_user("other@example.com")
    dm = _open_dm(client_for(me), other.id)
    cid = dm["id"]
    assert client_for(me).patch(f"/api/channels/{cid}/", {"name": "x"}, format="json").status_code == 404
    assert client_for(me).delete(f"/api/channels/{cid}/").status_code == 404
    assert client_for(me).post(f"/api/channels/{cid}/kick/", {"user_id": other.id}, format="json").status_code == 404
