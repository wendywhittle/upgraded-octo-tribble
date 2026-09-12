"""API boundary for transparent CRE underwriting."""

from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.cre_underwriting import CREUnderwritingRequest, underwrite_cre


class CREUnderwritingRequestModel(BaseModel):
    purchase_price: Optional[float] = Field(default=None, gt=0)
    annual_effective_gross_income: Optional[float] = Field(default=None)
    annual_operating_expenses: Optional[float] = Field(default=None)
    closing_costs: float = Field(default=0.0, ge=0)
    capex: float = Field(default=0.0, ge=0)
    ltv: Optional[float] = Field(default=None, ge=0, lt=1)
    interest_rate: Optional[float] = Field(default=None, ge=0, lt=1)
    amortization_years: Optional[int] = Field(default=None, ge=1, le=50)
    hold_years: Optional[int] = Field(default=None, ge=1, le=50)
    annual_income_growth: float = Field(default=0.0, gt=-1)
    annual_expense_growth: float = Field(default=0.0, gt=-1)
    exit_cap_rate: Optional[float] = Field(default=None, gt=0, lt=1)
    selling_cost_rate: float = Field(default=0.0, ge=0, lt=1)


def build_cre_router() -> APIRouter:
    router = APIRouter(prefix="/cre", tags=["cre-underwriting"])

    @router.get("/manifest")
    def manifest() -> Dict[str, Any]:
        return {
            "domain": "asset",
            "subsystem": "cre_underwriting",
            "metrics": [
                "noi", "cap_rate", "loan_amount", "initial_equity", "annual_debt_service",
                "dscr", "annual_cash_flow", "cash_on_cash", "exit_value", "irr", "equity_multiple",
            ],
            "research_only": True,
            "investment_authority": False,
        }

    @router.post("/underwrite")
    def underwrite(request: CREUnderwritingRequestModel) -> Dict[str, Any]:
        return underwrite_cre(CREUnderwritingRequest(**request.model_dump()))

    return router
