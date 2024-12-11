import pytest
from flask import url_for
from unittest.mock import patch, MagicMock


from app.modules.auth.services import AuthenticationService
from app.modules.auth.repositories import UserRepository
from app.modules.profile.repositories import UserProfileRepository
from app.modules.profile.services import UserProfileService


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """
    with test_client.application.app_context():
        # Add HERE new elements to the database that you want to exist in the test context.
        # DO NOT FORGET to use db.session.add(<element>) and db.session.commit() to save the data.
        pass

    yield test_client


def test_login_success(test_client):
    response = test_client.post(
        "/login",
        data=dict(email="test@example.com", password="test1234"),
        follow_redirects=True,
    )

    assert response.request.path != url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_email(test_client):
    response = test_client.post(
        "/login",
        data=dict(email="bademail@example.com", password="test1234"),
        follow_redirects=True,
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_login_unsuccessful_bad_password(test_client):
    response = test_client.post(
        "/login",
        data=dict(email="test@example.com", password="basspassword"),
        follow_redirects=True,
    )

    assert response.request.path == url_for("auth.login"), "Login was unsuccessful"

    test_client.get("/logout", follow_redirects=True)


def test_signup_user_no_name(test_client):
    response = test_client.post(
        "/signup",
        data=dict(surname="Foo", email="test@example.com", password="test1234"),
        follow_redirects=True,
    )
    assert response.request.path == url_for(
        "auth.show_signup_form"
    ), "Signup was unsuccessful"
    assert b"This field is required" in response.data, response.data


def test_signup_user_unsuccessful(test_client):
    email = "test@example.com"
    response = test_client.post(
        "/signup",
        data=dict(name="Test", surname="Foo", email=email, password="test1234"),
        follow_redirects=True,
    )
    assert response.request.path == url_for(
        "auth.show_signup_form"
    ), "Signup was unsuccessful"
    assert f"Email {email} in use".encode("utf-8") in response.data


def test_signup_user_successful(test_client):
    response = test_client.post(
        "/signup",
        data=dict(
            name="Foo", surname="Example", email="foo@example.com", password="foo1234"
        ),
        follow_redirects=True,
    )
    assert response.request.path == url_for("public.index"), "Signup was unsuccessful"


def test_service_create_with_profie_success(clean_database):
    data = {
        "name": "Test",
        "surname": "Foo",
        "email": "service_test@example.com",
        "password": "test1234",
    }

    AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 1
    assert UserProfileRepository().count() == 1


def test_service_create_with_profile_fail_no_email(clean_database):
    data = {"name": "Test", "surname": "Foo", "email": "", "password": "1234"}

    with pytest.raises(ValueError, match="Email is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


def test_service_create_with_profile_fail_no_password(clean_database):
    data = {
        "name": "Test",
        "surname": "Foo",
        "email": "test@example.com",
        "password": "",
    }

    with pytest.raises(ValueError, match="Password is required."):
        AuthenticationService().create_with_profile(**data)

    assert UserRepository().count() == 0
    assert UserProfileRepository().count() == 0


@pytest.fixture
def mock_form():
    """
    Crea un formulario simulado que puedes manipular en diferentes escenarios.
    """
    form = MagicMock()
    form.data = {"name": "Updated Name", "email": "updated@example.com"}
    return form


@pytest.fixture
def mock_service():
    """
    Crea una instancia simulada del servicio con el método `update` mockeado.
    """
    service = UserProfileService()
    service.update = MagicMock(
        return_value={"id": 1, "name": "Updated Name", "email": "updated@example.com"}
    )
    return service


def test_update_profile_success(mock_service, mock_form):
    mock_form.validate.return_value = True

    result, errors = mock_service.update_profile(user_profile_id=1, form=mock_form)

    mock_service.update.assert_called_once_with(1, **mock_form.data)
    assert result == {"id": 1, "name": "Updated Name", "email": "updated@example.com"}
    assert errors is None


def test_update_profile_invalid_form(mock_service, mock_form):
    mock_form.validate.return_value = False
    mock_form.errors = {"email": ["Invalid email format"]}

    result, errors = mock_service.update_profile(user_profile_id=1, form=mock_form)

    mock_service.update.assert_not_called()
    assert result is None
    assert errors == {"email": ["Invalid email format"]}


@pytest.fixture
def mock_authenticated_user():
    """
    Simula un usuario autenticado.
    """
    user = MagicMock()
    user.is_authenticated = True
    return user


@pytest.fixture
def mock_unauthenticated_user():
    """
    Simula un usuario no autenticado.
    """
    user = MagicMock()
    user.is_authenticated = False
    return user


def test_get_authenticated_user_authenticated(mock_authenticated_user):
    with patch("app.modules.auth.services.current_user", mock_authenticated_user):
        service = AuthenticationService()
        result = service.get_authenticated_user()

    assert result == mock_authenticated_user


def test_get_authenticated_user_unauthenticated(mock_unauthenticated_user):
    with patch("app.modules.auth.services.current_user", mock_unauthenticated_user):
        service = AuthenticationService()
        result = service.get_authenticated_user()

    assert result is None


@pytest.fixture
def mock_authenticated_user_with_profile():
    """
    Simula un usuario autenticado con un perfil asociado.
    """
    user = MagicMock()
    user.is_authenticated = True
    user.profile = {"id": 1, "name": "John Doe"}
    return user


@pytest.fixture
def mock_authenticated_user_without_profile():
    """
    Simula un usuario autenticado sin un perfil asociado.
    """
    user = MagicMock()
    user.is_authenticated = True
    user.profile = None
    return user


def test_get_authenticated_user_profile_with_profile(
    mock_authenticated_user_with_profile,
):
    with patch(
        "app.modules.auth.services.current_user", mock_authenticated_user_with_profile
    ):
        service = AuthenticationService()
        result = service.get_authenticated_user_profile()

    assert result == {"id": 1, "name": "John Doe"}


def test_get_authenticated_user_profile_without_profile(
    mock_authenticated_user_without_profile,
):
    with patch(
        "app.modules.auth.services.current_user",
        mock_authenticated_user_without_profile,
    ):
        service = AuthenticationService()
        result = service.get_authenticated_user_profile()

    assert result is None


def test_get_authenticated_user_profile_unauthenticated(mock_unauthenticated_user):
    with patch("app.modules.auth.services.current_user", mock_unauthenticated_user):
        service = AuthenticationService()
        result = service.get_authenticated_user_profile()

    assert result is None
