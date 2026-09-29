from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import agent
import auth
import chat_history
import database
import tools
from llm.claude_client import AuthError, ClaudeError
from models import ChatHistoryResponse, ChatHistoryTurn, ChatRequest, ChatResponse

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=database.DATA_DIR), name="media")


@app.get("/api/products")
def list_products():
    return database.list_products()


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    product = database.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/signup", status_code=201)
def signup(payload: SignupRequest):
    try:
        return auth.create_user(payload.first_name, payload.last_name, payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/auth/login")
def login(payload: LoginRequest):
    user = auth.authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return user


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    try:
        reply = agent.chat(payload.message, payload.history, user=payload.user, page_context=payload.page_context)
    except AuthError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ClaudeError as exc:
        raise HTTPException(status_code=502, detail=f"The shop assistant is unavailable: {exc}") from exc

    products = tools.get_products_by_ids(reply.product_ids)

    if payload.user is not None:
        chat_history.save_message(payload.user.id, "user", payload.message, [])
        chat_history.save_message(payload.user.id, "assistant", reply.reply, reply.product_ids)

    return ChatResponse(reply=reply.reply, products=products)


@app.get("/api/chat/history", response_model=ChatHistoryResponse)
def get_chat_history(user_id: int):
    turns = chat_history.load_history(user_id)
    messages = [
        ChatHistoryTurn(role=turn["role"], content=turn["content"], products=tools.get_products_by_ids(turn["product_ids"]))
        for turn in turns
    ]
    return ChatHistoryResponse(messages=messages)
