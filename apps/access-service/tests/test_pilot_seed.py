from access_service.application.pilot import PILOT_USERS, stable_user_id


def test_pilot_seed_contains_exact_role_counts_and_stable_ids() -> None:
    assert len(PILOT_USERS) == 12
    assert sum(role == "platform_admin" for _, _, role in PILOT_USERS) == 2
    assert sum(role == "project_manager" for _, _, role in PILOT_USERS) == 5
    assert sum(role == "employee" for _, _, role in PILOT_USERS) == 5
    ids = [stable_user_id(email) for email, _, _ in PILOT_USERS]
    assert len(set(ids)) == 12
    assert ids == [stable_user_id(email) for email, _, _ in PILOT_USERS]
