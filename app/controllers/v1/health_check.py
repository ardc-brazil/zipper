from fastapi import APIRouter

router = APIRouter(prefix="/health-check", tags=["health-check"])


# GET /api/v1/health-check
@router.get(path="/", description="Answers 200 while the process serves requests")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
