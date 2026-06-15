# from fastapi import APIRouter
# from services.vectordb import get_stats

# router = APIRouter()

# @router.get("/health")
# def health():
#     stats = get_stats()
#     return {"status": "ok", **stats}


from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    try:
        from services.vectordb import get_stats
        stats = get_stats()
        return {"status": "ok", **stats}
    except Exception as e:
        return {"status": "error", "detail": str(e)}