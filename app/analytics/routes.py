from fastapi import APIRouter, Request, Depends, Query
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, desc
from typing import Optional
from datetime import datetime, timedelta

from ..database.db import get_db
from ..auth.dependencies import get_current_user_api
from ..utils.flash import get_flash

# Import models at top level — no local imports needed
from ..models import Interview, InterviewEvaluation, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ─────────────────────────────────────────────────────────────────────────────
#  SCHEMA REMINDER (so the join logic below is easy to follow):
#
#  User         (user_id)
#    └─ Interview        (interview_id, user_id, interview_type, status, created_at)
#         └─ InterviewEvaluation  (evaluation_id, interview_id, score, created_at)
#
#  There is NO user_id on InterviewEvaluation.
#  To filter by user, we always join InterviewEvaluation → Interview on interview_id,
#  then filter Interview.user_id == current_user.user_id.
#
#  interview_type lives on Interview, NOT on InterviewEvaluation.
# ─────────────────────────────────────────────────────────────────────────────

TYPE_NAMES = {
    "dsa":    "Technical Interview (SWE)",
    "hr":     "HR & Behavioral",
    "ml":     "Data Science & ML",
    "sql":    "SQL Developer",
    "devops": "DevOps & SRE",
    "pm":     "Product Manager",
    "system": "System Design",
}


def _cutoff(days: int) -> datetime:
    return datetime.utcnow() - timedelta(days=days)


def _base_eval_query(db: Session, user_id: int, cutoff: datetime, interview_type: Optional[str] = None):
    """
    Returns a base SQLAlchemy query that already has the correct join and
    user/date filters applied.  All analytics queries build on this.

    JOIN:  InterviewEvaluation → Interview
    WHERE: Interview.user_id == user_id
           InterviewEvaluation.created_at >= cutoff
           (optionally) Interview.interview_type == interview_type
    """
    q = (
        db.query(InterviewEvaluation)
        .join(Interview, InterviewEvaluation.interview_id == Interview.interview_id)
        .filter(
            Interview.user_id == user_id,
            InterviewEvaluation.created_at >= cutoff,
        )
    )
    if interview_type:
        q = q.filter(Interview.interview_type == interview_type)
    return q


def _calc_trend(db: Session, user_id: int, interview_type: Optional[str] = None) -> int:
    """
    Improvement trend: compares avg score of the last 30 days vs the 30 days
    before that.  Returns an integer percentage (can be negative).

    Uses _base_eval_query so the join is handled consistently.
    """
    now        = datetime.utcnow()
    last_month = now - timedelta(days=30)
    prev_month = now - timedelta(days=60)

    def _avg(start: datetime, end: datetime) -> float:
        return (
            db.query(func.avg(InterviewEvaluation.score))
            .join(Interview, InterviewEvaluation.interview_id == Interview.interview_id)
            .filter(
                Interview.user_id == user_id,
                InterviewEvaluation.created_at >= start,
                InterviewEvaluation.created_at <  end,
            )
            .filter(
                *(  [Interview.interview_type == interview_type]
                    if interview_type else [] )
            )
            .scalar() or 0
        )

    recent_avg = _avg(last_month, now)
    prev_avg   = _avg(prev_month, last_month)

    if prev_avg == 0:
        return 0
    return int(((recent_avg - prev_avg) / prev_avg) * 100)


# ─────────────────────────────────────────────────────────────────────────────
#  Progress page — initial render
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/progress")
def progress_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_api),
):
    user_id = current_user.user_id
    days    = 60
    cutoff  = _cutoff(days)

    # ── Summary: total interviews + avg score ─────────────────────────────────
    summary = (
        db.query(
            func.count(InterviewEvaluation.evaluation_id).label("total"),
            func.avg(InterviewEvaluation.score).label("avg_score"),
        )
        .join(Interview, InterviewEvaluation.interview_id == Interview.interview_id)
        .filter(
            Interview.user_id == user_id,
            InterviewEvaluation.created_at >= cutoff,
        )
        .first()
    )

    total_interviews  = summary.total or 0
    avg_score         = round(float(summary.avg_score or 0))
    improvement_trend = _calc_trend(db, user_id)   # raw int, template formats it

    # ── Timeline: avg score grouped by date ───────────────────────────────────
    timeline_rows = (
        db.query(
            func.date(InterviewEvaluation.created_at).label("date"),
            func.avg(InterviewEvaluation.score).label("avg_score"),
            func.count(InterviewEvaluation.evaluation_id).label("count"),
        )
        .join(Interview, InterviewEvaluation.interview_id == Interview.interview_id)
        .filter(
            Interview.user_id == user_id,
            InterviewEvaluation.created_at >= cutoff,
        )
        .group_by(func.date(InterviewEvaluation.created_at))
        .order_by(func.date(InterviewEvaluation.created_at))
        .all()
    )

    timeline_data = [
        {"date": str(r.date), "avgScore": round(float(r.avg_score), 1), "count": r.count}
        for r in timeline_rows
    ]

    # ── By-type: avg score grouped by interview_type (lives on Interview) ─────
    type_rows = (
        db.query(
            Interview.interview_type,
            func.avg(InterviewEvaluation.score).label("avg_score"),
            func.count(InterviewEvaluation.evaluation_id).label("count"),
        )
        .join(Interview, InterviewEvaluation.interview_id == Interview.interview_id)
        .filter(
            Interview.user_id == user_id,
            InterviewEvaluation.created_at >= cutoff,
        )
        .group_by(Interview.interview_type)
        .all()
    )

    by_type_data = {
        r.interview_type: {
            "typeName": TYPE_NAMES.get(r.interview_type, r.interview_type),
            "avgScore": round(float(r.avg_score), 1),
            "count":    r.count,
        }
        for r in type_rows
    }

    return templates.TemplateResponse(
        "progress.html",
        {
            "request":           request,
            "flash":             get_flash(request),
            "total_interviews":  total_interviews,
            "avg_score":         avg_score,
            "improvement_trend": improvement_trend,
            "timeline_data":     timeline_data,
            "by_type_data":      by_type_data,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Progress — JSON API endpoints (called by JS on filter change)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/api/analytics/summary")
def analytics_summary(
    request: Request,
    days: int = Query(60),
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_api),
):
    user_id = current_user.user_id
    cutoff  = _cutoff(days)

    q = (
        db.query(
            func.count(InterviewEvaluation.evaluation_id).label("total"),
            func.avg(InterviewEvaluation.score).label("avg_score"),
        )
        .join(Interview, InterviewEvaluation.interview_id == Interview.interview_id)
        .filter(
            Interview.user_id == user_id,
            InterviewEvaluation.created_at >= cutoff,
        )
    )
    if type:
        q = q.filter(Interview.interview_type == type)

    result = q.first()
    trend  = _calc_trend(db, user_id, type)

    return {
        "totalInterviews":  result.total or 0,
        "avgScore":         round(float(result.avg_score or 0)),
        "improvementTrend": trend,
    }


@router.get("/api/analytics/timeline")
def analytics_timeline(
    request: Request,
    days: int = Query(60),
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_api),
):
    user_id = current_user.user_id
    cutoff  = _cutoff(days)

    q = (
        db.query(
            func.date(InterviewEvaluation.created_at).label("date"),
            func.avg(InterviewEvaluation.score).label("avg_score"),
            func.count(InterviewEvaluation.evaluation_id).label("count"),
        )
        .join(Interview, InterviewEvaluation.interview_id == Interview.interview_id)
        .filter(
            Interview.user_id == user_id,
            InterviewEvaluation.created_at >= cutoff,
        )
    )
    if type:
        q = q.filter(Interview.interview_type == type)

    rows = (
        q.group_by(func.date(InterviewEvaluation.created_at))
         .order_by(func.date(InterviewEvaluation.created_at))
         .all()
    )

    return {
        "timeline": [
            {"date": str(r.date), "avgScore": round(float(r.avg_score), 1), "count": r.count}
            for r in rows
        ]
    }


@router.get("/api/analytics/by-type")
def analytics_by_type(
    request: Request,
    days: int = Query(60),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_api),
):
    user_id = current_user.user_id
    cutoff  = _cutoff(days)

    rows = (
        db.query(
            Interview.interview_type,
            func.avg(InterviewEvaluation.score).label("avg_score"),
            func.min(InterviewEvaluation.score).label("min_score"),
            func.max(InterviewEvaluation.score).label("max_score"),
            func.count(InterviewEvaluation.evaluation_id).label("count"),
        )
        .join(Interview, InterviewEvaluation.interview_id == Interview.interview_id)
        .filter(
            Interview.user_id == user_id,
            InterviewEvaluation.created_at >= cutoff,
        )
        .group_by(Interview.interview_type)
        .all()
    )

    return {
        "byType": {
            r.interview_type: {
                "typeName": TYPE_NAMES.get(r.interview_type, r.interview_type),
                "avgScore": round(float(r.avg_score), 1),
                "minScore": int(r.min_score),
                "maxScore": int(r.max_score),
                "count":    r.count,
            }
            for r in rows
        }
    }


# ─────────────────────────────────────────────────────────────────────────────
#  Ranking page — initial render
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/ranking")
def ranking_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_api),
):
    user_id        = current_user.user_id
    rankings       = _get_rankings(db, interview_type=None)
    user_rank_data = _get_user_rank(db, user_id, interview_type=None)

    return templates.TemplateResponse(
        "ranking.html",
        {
            "request":          request,
            "flash":            get_flash(request),
            "rankings":         rankings,
            "user_rank":        user_rank_data["globalRank"],
            "user_avg_score":   user_rank_data["avgScore"],
            "user_interviews":  user_rank_data["interviewCount"],
            "user_percentile":  user_rank_data["percentileRank"],
            "user_best_score":  user_rank_data["bestScore"],
            "user_improvement": ("+" if user_rank_data["trend"] >= 0 else "")
                                + str(user_rank_data["trend"]) + "%",
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Ranking — JSON API endpoints (called by JS on filter change)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/api/ranking/global")
def get_global_rankings(
    request: Request,
    type: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_api),
):
    return {"rankings": _get_rankings(db, interview_type=type, limit=limit)}


@router.get("/api/ranking/user-stats")
def get_user_ranking_stats(
    request: Request,
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_api),
):
    return {"ranking": _get_user_rank(db, current_user.user_id, interview_type=type)}


# ─────────────────────────────────────────────────────────────────────────────
#  Shared helpers — not exposed as routes
# ─────────────────────────────────────────────────────────────────────────────

def _get_rankings(
    db: Session,
    interview_type: Optional[str] = None,
    limit: int = 50,
) -> list:
    """
    Leaderboard query.

    JOIN chain:  InterviewEvaluation → Interview → User
    GROUP BY:    User.user_id, User.name, User.email
    ORDER BY:    avg(score) DESC
    LIMIT:       50

    Rank is assigned in Python from the ordered position (simpler than
    window functions in SQLAlchemy ORM).
    """
    cutoff = _cutoff(180)   # rank over last 6 months

    q = (
        db.query(
            User.user_id,
            User.name,
            User.email,
            func.avg(InterviewEvaluation.score).label("avg_score"),
            func.max(InterviewEvaluation.score).label("best_score"),
            func.count(InterviewEvaluation.evaluation_id).label("interview_count"),
        )
        .join(Interview, InterviewEvaluation.interview_id == Interview.interview_id)
        .join(User, Interview.user_id == User.user_id)
        .filter(InterviewEvaluation.created_at >= cutoff)
    )

    if interview_type:
        q = q.filter(Interview.interview_type == interview_type)

    rows = (
        q.group_by(User.user_id, User.name, User.email)
         .order_by(desc("avg_score"))
         .limit(limit)
         .all()
    )

    return [
        {
            "rank":           idx + 1,
            "userId":         r.user_id,
            "name":           r.name,
            "avgScore":       round(float(r.avg_score), 1),
            "interviewCount": r.interview_count,
            "bestScore":      int(r.best_score),
            "trend":          _calc_trend(db, r.user_id, interview_type),
        }
        for idx, r in enumerate(rows)
    ]


def _get_user_rank(
    db: Session,
    user_id: int,
    interview_type: Optional[str] = None,
) -> dict:
    """
    Gets the current user's rank by counting how many users have a strictly
    higher average score, then adds 1.

    Step 1 — get this user's avg score.
    Step 2 — subquery: avg score per user across all users.
    Step 3 — count how many users in that subquery are above this user.
    Step 4 — count total distinct users (for percentile).
    """
    cutoff = _cutoff(180)

    # ── Step 1: this user's own stats ─────────────────────────────────────────
    user_q = (
        db.query(
            func.avg(InterviewEvaluation.score).label("avg_score"),
            func.max(InterviewEvaluation.score).label("best_score"),
            func.count(InterviewEvaluation.evaluation_id).label("interview_count"),
        )
        .join(Interview, InterviewEvaluation.interview_id == Interview.interview_id)
        .filter(
            Interview.user_id == user_id,
            InterviewEvaluation.created_at >= cutoff,
        )
    )
    if interview_type:
        user_q = user_q.filter(Interview.interview_type == interview_type)

    user_stats      = user_q.first()
    avg_score       = round(float(user_stats.avg_score or 0), 1)
    best_score      = int(user_stats.best_score or 0)
    interview_count = user_stats.interview_count or 0

    # ── Step 2: per-user avg subquery across all users ────────────────────────
    per_user_q = (
        db.query(
            Interview.user_id.label("uid"),
            func.avg(InterviewEvaluation.score).label("u_avg"),
        )
        .join(Interview, InterviewEvaluation.interview_id == Interview.interview_id)
        .filter(InterviewEvaluation.created_at >= cutoff)
    )
    if interview_type:
        per_user_q = per_user_q.filter(Interview.interview_type == interview_type)

    per_user_sub = per_user_q.group_by(Interview.user_id).subquery()

    # ── Step 3: count users strictly above this user ──────────────────────────
    users_above = (
        db.query(func.count())
        .filter(per_user_sub.c.u_avg > avg_score)
        .scalar() or 0
    )
    rank = users_above + 1

    # ── Step 4: total distinct users ──────────────────────────────────────────
    total_users = (
        db.query(func.count(distinct(per_user_sub.c.uid)))
        .scalar() or 1
    )

    percentile = round((total_users - rank + 1) / total_users * 100)

    return {
        "globalRank":     rank,
        "totalUsers":     total_users,
        "percentileRank": f"Top {percentile}%",
        "avgScore":       avg_score,
        "interviewCount": interview_count,
        "bestScore":      best_score,
        "trend":          _calc_trend(db, user_id, interview_type),
        "percentile":     percentile,
    }