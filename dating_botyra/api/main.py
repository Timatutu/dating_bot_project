from fastapi import FastAPI

from api.routers import feed, like, match, profile, subscription

app = FastAPI(title="Dating Bot API", version="1.0.0")

app.include_router(profile.router, prefix="/api/profiles", tags=["profiles"])
app.include_router(feed.router, prefix="/api/feed", tags=["feed"])
app.include_router(like.router, prefix="/api/like", tags=["like"])
app.include_router(match.router, prefix="/api/matches", tags=["matches"])
app.include_router(subscription.router, prefix="/api/subscriptions", tags=["subscriptions"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
