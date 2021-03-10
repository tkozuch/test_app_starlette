import base64
import binascii

from starlette.applications import Starlette
from starlette.authentication import (AuthCredentials, AuthenticationBackend,
                                      AuthenticationError, SimpleUser)
from starlette.endpoints import HTTPEndpoint
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.routing import Route
from starlette.templating import Jinja2Templates
from starlette.responses import RedirectResponse, PlainTextResponse

from db import users
from db import database


templates = Jinja2Templates(directory="templates")


class SignIn(HTTPEndpoint):
    async def get(self, request):
        return templates.TemplateResponse("signin.html", {"request": request})

    async def post(self, request):
        form = await request.form()
        query = users.select().where(users.c.username == form["login"])
        user = await database.fetch_one(query)
        if not user:
            return templates.TemplateResponse("user_not_found.html", {"request": request})
        else:
            # TODO: Here should be some actual logging evaluated on the user probably, but I don't
            #   know how to do this.
            return RedirectResponse(url="dashboard", headers={"Authorization": "true"})


class SignUp(HTTPEndpoint):
    async def get(self, request):
        return templates.TemplateResponse("signup.html", {"request": request})

    async def post(self, request):
        form = await request.form()
        query = users.select().where(users.c.username == form["login"])
        user = await database.fetch_one(query)
        if not user:
            query = users.insert().values(
                username=form["login"],
                password=form["password"]
            )
            await database.execute(query)
            return templates.TemplateResponse("after_signup.html", {"request": request,
                                                                    "message": "Register Success"})
        else:
            return templates.TemplateResponse("after_signup.html", {"request": request,
                                                                    "message": "Email Exists"})


async def dashboard(request):
    if request.user.is_authenticated:
        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "user": request.user}
        )
    else:
        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request},
            status_code=403
        )


async def logout(request):
    # TODO: Actually log out the user
    return PlainTextResponse("You have been logged out")


class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        # To be fixed somehow, for now don't know how to do this.
        if "Authorization" not in request.headers:
            return

        auth = request.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() != 'basic':
                return
            decoded = base64.b64decode(credentials).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error) as exc:
            raise AuthenticationError('Invalid basic auth credentials')

        username, _, password = decoded.partition(":")
        query = users.select().where(users.c.username == username)
        user = await database.fetch_one(query)

        if not user:
            raise AuthenticationError("User does not exist")
        elif user.password != password:
            raise AuthenticationError("Invalid password")

        return AuthCredentials(["authenticated"]), SimpleUser(username)


app = Starlette(
    debug=True,
    routes=[
        Route("/", SignIn, name="signin"),
        Route("/signup", SignUp, name="signup"),
        Route("/dashboard", dashboard, name="dashboard", methods=["POST", "GET"]),
        Route("/logout", logout, name="logout")
    ],
    middleware=[Middleware(AuthenticationMiddleware, backend=BasicAuthBackend())],
    on_startup=[database.connect],
    on_shutdown=[database.disconnect]
)
