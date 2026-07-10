from app.schemas import Episode, ShowDetail

SHOW_ID = 169


def make_fake_show():
    """A show with a mix of aired and unaired episodes, so list_my_shows
    has to correctly split them rather than discarding the unaired ones."""
    return ShowDetail(
        id=SHOW_ID,
        name="Breaking Bad",
        premiered="2008-01-20",
        status="Running",
        image="https://example.test/poster.jpg",
        summary="<p>Chemistry teacher turns to crime.</p>",
        episodes=[
            Episode(
                id=1,
                season=1,
                number=1,
                name="Pilot",
                airdate="2008-01-20",
                airstamp="2008-01-20T02:00:00+00:00",
                image=None,
            ),
            Episode(
                id=2,
                season=1,
                number=2,
                name="Cat's in the Bag...",
                airdate="2008-01-27",
                airstamp="2008-01-27T02:00:00+00:00",
                image=None,
            ),
            Episode(
                id=3,
                season=2,
                number=1,
                name="Future Episode",
                airdate="2099-01-01",
                airstamp="2099-01-01T02:00:00+00:00",
                image=None,
            ),
            Episode(
                id=4,
                season=2,
                number=2,
                name="Further Future Episode",
                airdate="2099-02-01",
                airstamp="2099-02-01T02:00:00+00:00",
                image=None,
            ),
        ],
    )


async def fake_get_show(show_id):
    assert show_id == SHOW_ID
    return make_fake_show()


def test_my_shows_reports_status_and_next_unaired_episode(client, test_user, mocker):
    mocker.patch("app.routers.tracking.tvmaze.get_show", side_effect=fake_get_show)
    headers = test_user["auth_headers"]

    track_resp = client.post(
        "/tracking/shows", json={"tvmaze_show_id": SHOW_ID}, headers=headers
    )
    assert track_resp.status_code == 201

    resp = client.get("/tracking/shows", headers=headers)
    assert resp.status_code == 200
    shows = resp.json()
    assert len(shows) == 1

    show = shows[0]
    assert show["status"] == "Running"
    assert show["total_aired_count"] == 2
    assert show["watched_count"] == 0
    assert show["next_episode"]["id"] == 1
    assert show["next_unaired_episode"]["id"] == 3
    assert show["next_unaired_episode"]["airdate"] == "2099-01-01"


def test_next_unaired_episode_is_none_when_no_future_episodes_scheduled(
    client, test_user, mocker
):
    def get_show_with_only_aired_episodes(show_id):
        show = make_fake_show()
        show.episodes = [ep for ep in show.episodes if ep.id in (1, 2)]
        return show

    async def fake(show_id):
        return get_show_with_only_aired_episodes(show_id)

    mocker.patch("app.routers.tracking.tvmaze.get_show", side_effect=fake)
    headers = test_user["auth_headers"]

    client.post("/tracking/shows", json={"tvmaze_show_id": SHOW_ID}, headers=headers)
    resp = client.get("/tracking/shows", headers=headers)
    show = resp.json()[0]

    assert show["next_unaired_episode"] is None


def test_next_episode_is_none_but_next_unaired_episode_is_set_when_caught_up(
    client, test_user, mocker
):
    mocker.patch("app.routers.tracking.tvmaze.get_show", side_effect=fake_get_show)
    headers = test_user["auth_headers"]

    client.post("/tracking/shows", json={"tvmaze_show_id": SHOW_ID}, headers=headers)
    client.post(
        "/tracking/episodes/bulk",
        json={"tvmaze_show_id": SHOW_ID, "tvmaze_episode_ids": [1, 2]},
        headers=headers,
    )

    resp = client.get("/tracking/shows", headers=headers)
    show = resp.json()[0]

    assert show["next_episode"] is None
    assert show["watched_count"] == 2
    assert show["next_unaired_episode"]["id"] == 3
