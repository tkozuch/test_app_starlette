import base64
import binascii

from starlette.applications import Starlette
from starlette.authentication import (AuthCredentials, AuthenticationBackend,
                                      AuthenticationError, SimpleUser,
                                      UnauthenticatedUser)
from starlette.endpoints import HTTPEndpoint
from starlette.middleware import Middleware
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.routing import Route
from starlette.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from sqlalchemy import select

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
            return RedirectResponse(url="dashboard")


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


class Dashboard(HTTPEndpoint):
    async def post(self, request):
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


class BasicAuthBackend(AuthenticationBackend):
    async def authenticate(self, request):
        if "Authorization" not in request.headers:
            return

        creds = request.auth
        query = users.select().where(users.c.username == creds["login"])
        user = await database.fetch_one(query)

        if user:
            if form["login"] == user.username and creds["password"] == user.password:
                return AuthCredentials(["authenticated"]), SimpleUser(user.username)

        return


app = Starlette(
    debug=True,
    routes=[
        Route("/", SignIn, name="signin"),
        Route("/signup", SignUp, name="signup"),
        Route("/dashboard", Dashboard, name="dashboard"),
    ],
    middleware=[Middleware(AuthenticationMiddleware, backend=BasicAuthBackend())],
    on_startup=[database.connect],
    on_shutdown=[database.disconnect]
)
