import pytest

from app import db
from app.modules.conftest import login, logout
from app.modules.auth.models import User
from app.modules.profile.models import UserProfile


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    for module testing (por example, new users)
    """
    with test_client.application.app_context():
        user_test = User(email="user@example.com", password="test1234")
        db.session.add(user_test)
        db.session.commit()

        user_test1 = User(email="user1@example.com", password="test1234")
        db.session.add(user_test1)
        db.session.commit()

        user_test2 = User(email="user2@example.com", password="test1234")
        db.session.add(user_test2)
        db.session.commit()

        profile = UserProfile(user_id=user_test.id, name="Name", surname="Surname")
        db.session.add(profile)
        db.session.commit()

        profile1 = UserProfile(user_id=user_test1.id, name="Name1", surname="Surname1", public_data=True)
        db.session.add(profile1)
        db.session.commit()

        profile2 = UserProfile(user_id=user_test2.id, name="Name2", surname="Surname2", public_data=False)
        db.session.add(profile2)
        db.session.commit()

    yield test_client


def test_edit_profile_page_get(test_client):
    """
    Tests access to the profile editing page via a GET request.
    """
    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200, "Login was unsuccessful."

    response = test_client.get("/profile/edit")
    assert (
        response.status_code == 200
    ), "The profile editing page could not be accessed."
    assert (
        b"Edit profile" in response.data
    ), "The expected content is not present on the page"

    logout(test_client)


def test_view_profile_authenticated_public_data_true(test_client):
    """
    Authenticated user access to a profile with public data.
    """
    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200

    response = test_client.get("/profile/3")
    assert response.status_code == 200
    assert "User profile" in response.get_data(as_text=True)

    logout(test_client)


def test_view_profile_authenticated_public_data_false(test_client):
    """
    Authenticated user access to a profile with no public data.
    """
    login_response = login(test_client, "user@example.com", "test1234")
    assert login_response.status_code == 200

    response = test_client.get("/profile/4", follow_redirects=True)
    assert response.status_code == 200
    assert "User data is not public" in response.get_data(as_text=True)

    logout(test_client)


def test_view_profile_unauthenticated_public_data_true(test_client):
    """
    Unauthenticated user access to a profile with public data.
    """
    response = test_client.get("/profile/3")
    assert response.status_code == 200
    assert "User profile" in response.get_data(as_text=True)


def test_view_profile_unauthenticated_public_data_false(test_client):
    """
    Unauthenticated user access to a profile with no public data.
    """
    response = test_client.get("/profile/4", follow_redirects=True)
    assert response.status_code == 200
    assert "User data is not public" in response.get_data(as_text=True)


def test_view_my_profile_authenticated_public_data_true(test_client):
    """
    Authenticated user access to his profile with public data.
    """
    login_response = login(test_client, "user1@example.com", "test1234")
    assert login_response.status_code == 200

    response = test_client.get("/profile/3")
    assert response.status_code == 200
    assert "User profile" in response.get_data(as_text=True)

    logout(test_client)


def test_view_my_profile_authenticated_public_data_false(test_client):
    """
    Authenticated user access to his profile with no public data.
    """
    login_response = login(test_client, "user2@example.com", "test1234")
    assert login_response.status_code == 200

    response = test_client.get("/profile/4")
    assert response.status_code == 200
    assert "User profile" in response.get_data(as_text=True)

    logout(test_client)
