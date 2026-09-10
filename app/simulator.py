"""Independent Monte Carlo risk engine for research and CRE stress testing."""

import math
import random
from statistics import mean, median
from typing import Any, Dict, List, Mapping


def _drawdown(path: List[float]) -> float:
    peak, worst = path[0], 0.0
    for value in path:
        peak = max(peak, value)
        if peak: worst = max(worst, (peak - value) / peak)
    return worst


def _percentile(values: List[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered: return 0.0
    index = (len(ordered) - 1) * q
    lower, upper = math.floor(index), math.ceil(index)
    if lower == upper: return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def run_monte_carlo(initial_value: float = 100.0, horizon_steps: int = 60, paths: int = 5000, seed: int = 42, assumptions: List[str] | None = None) -> Dict[str, Any]:
    rng = random.Random(seed)
    specs = {"base": (.0005, .012, 0), "bull": (.0012, .014, 0), "bear": (-.001, .018, 0), "adversarial": (-.0015, .028, -.12), "tail_risk": (-.0025, .045, -.25)}
    summaries = []
    for scenario, (drift, vol, shock) in specs.items():
        terminals, drawdowns = [], []
        for _ in range(paths):
            value, path = initial_value, [initial_value]
            for step in range(horizon_steps):
                value *= math.exp(drift - .5 * vol**2 + rng.gauss(0, vol))
                if scenario in {"adversarial", "tail_risk"} and step == horizon_steps // 2: value *= 1 + shock
                path.append(value)
            terminals.append(value); drawdowns.append(_drawdown(path))
        summaries.append({"scenario": scenario, "mean_terminal": round(mean(terminals),4), "median_terminal": round(median(terminals),4), "p05_terminal": round(_percentile(terminals,.05),4), "p95_terminal": round(_percentile(terminals,.95),4), "probability_loss": round(sum(v < initial_value for v in terminals)/paths,4), "max_drawdown_mean": round(mean(drawdowns),4)})
    return {"engine": "AletheiaTelos Independent Monte Carlo Risk Engine v1", "independent_of_agents": True, "paths": paths, "horizon_steps": horizon_steps, "seed": seed, "scenarios": summaries, "assumptions": assumptions or []}


def _annual_debt_service(loan: float, rate: float, amortization_years: int | None, interest_only: bool = False) -> tuple[float, str]:
    if loan <= 0 or rate < 0: return 0.0, "none"
    if interest_only: return loan * rate, "interest_only"
    if amortization_years is None or amortization_years <= 0: return 0.0, "unknown"
    if rate == 0: return loan / amortization_years, "amortizing"
    r, n = rate / 12, amortization_years * 12
    return loan * r / (1 - (1 + r) ** -n) * 12, "amortizing"


def _remaining_balance(loan: float, rate: float, amortization_years: int | None, years: int, interest_only: bool = False) -> float:
    if loan <= 0 or interest_only or amortization_years is None or amortization_years <= 0: return max(0.0, loan)
    if rate == 0: return max(0.0, loan * (1 - years / amortization_years))
    r, n, k = rate / 12, amortization_years * 12, min(amortization_years * 12, years * 12)
    pmt = loan * r / (1 - (1 + r) ** -n)
    return max(0.0, loan * (1 + r) ** k - pmt * ((1 + r) ** k - 1) / r)


def _irr(cash_flows: List[float]) -> float | None:
    if not cash_flows or not (any(v > 0 for v in cash_flows) and any(v < 0 for v in cash_flows)): return None
    def npv(rate): return sum(v / (1 + rate) ** i for i, v in enumerate(cash_flows))
    low, high = -.9999, 10.0; low_value = npv(low)
    if low_value * npv(high) > 0: return None
    for _ in range(100):
        mid, value = (low + high) / 2, npv((low + high) / 2)
        if abs(value) < 1e-8: return mid
        if low_value * value <= 0: high = mid
        else: low, low_value = mid, value
    return (low + high) / 2


def _cre_path(purchase_price, noi, hold_period, rng, growth_mu, growth_vol, occupancy, exit_cap_rate, debt, debt_service, amortization_years, interest_rate, capital_expenditures, gross_rent, operating_expenses, expense_growth, vacancy, shock, selling_cost_rate, other_income=0.0, interest_only=False):
    current_noi = float(noi); equity_initial = purchase_price - debt; cash_flows=[]; equity_values=[equity_initial]; dscrs=[]
    for year in range(1, hold_period + 1):
        growth = rng.gauss(growth_mu, growth_vol)
        if gross_rent is not None and operating_expenses is not None:
            rent = gross_rent * (1 + growth) ** year
            occ = max(0.0, min(1.0, occupancy + rng.gauss(0, growth_vol)))
            vacancy_rate = vacancy if vacancy is not None else 1 - occ
            current_noi = rent * max(0, 1 - vacancy_rate) + other_income - operating_expenses * (1 + expense_growth) ** year
        else:
            current_noi = current_noi * (1 + growth) * max(0, min(1, occupancy))
        if shock and year == max(1, hold_period // 2): current_noi *= max(0, 1 + shock)
        cash_flows.append(current_noi - debt_service - capital_expenditures)
        if debt_service > 0: dscrs.append(current_noi / debt_service)
        equity_values.append(current_noi / exit_cap_rate - _remaining_balance(debt, interest_rate, amortization_years, year, interest_only))
    exit_value = current_noi / exit_cap_rate
    net_sale = exit_value * (1 - selling_cost_rate) - _remaining_balance(debt, interest_rate, amortization_years, hold_period, interest_only)
    total = sum(cash_flows) + net_sale
    return {"exit_value": exit_value, "net_sale_proceeds": net_sale, "equity_outcome": total, "equity_multiple": total / equity_initial if equity_initial > 0 else None, "irr": _irr([-equity_initial, *cash_flows[:-1], cash_flows[-1] + net_sale]) if equity_initial > 0 else None, "cash_on_cash": cash_flows[0] / equity_initial if equity_initial > 0 else None, "dscr": dscrs[-1] if dscrs else None, "minimum_dscr": min(dscrs) if dscrs else None, "debt_yield": noi / debt if debt > 0 else None, "equity_values": equity_values, "cash_flows": cash_flows}


def run_cre_monte_carlo(purchase_price, noi, hold_period=5, paths=5000, seed=42, occupancy=None, rent_growth=None, expense_growth=None, exit_cap_rate=None, interest_rate=None, loan_to_value=None, capital_expenditures=None, assumptions=None, gross_rent=None, operating_expenses=None, vacancy=None, amortization_years=None, selling_cost_rate=None, interest_only=False, closing_costs=None, other_income=None, scenario_overrides: Mapping[str, Mapping[str, float]] | None = None):
    required={"purchase_price":purchase_price,"noi":noi,"hold_period":hold_period,"exit_cap_rate":exit_cap_rate}; missing=tuple(k for k,v in required.items() if v is None or (isinstance(v,(int,float)) and v<=0))
    if missing: return {"engine":"AletheiaTelos Independent CRE Monte Carlo Risk Engine v2","independent_of_agents":True,"status":"INSUFFICIENT EVIDENCE","missing_inputs":missing,"scenarios":[],"assumptions":assumptions or []}
    if not 1<=hold_period<=100 or paths<1: raise ValueError("hold_period must be 1..100 and paths must be positive")
    if occupancy is not None and not 0<=occupancy<=1: raise ValueError("occupancy must be between 0 and 1")
    price, base_noi=float(purchase_price),float(noi); occ=occupancy if occupancy is not None else 1.0; growth=rent_growth if rent_growth is not None else 0.0; exp_growth=expense_growth if expense_growth is not None else 0.0; exit_cap=float(exit_cap_rate); ltv=float(loan_to_value or 0.0)
    if not 0<=ltv<1: raise ValueError("loan_to_value must be between 0 and 1")
    debt=price*ltv; rate=float(interest_rate or 0.0); ds,method=_annual_debt_service(debt,rate,amortization_years,interest_only); equity_initial=price+float(closing_costs or 0)-debt; capex=float(capital_expenditures or 0); sale_cost=float(selling_cost_rate or 0); scenario_overrides=scenario_overrides or {}
    defaults={"BASE":{"rent_growth_delta":0,"occupancy_delta":0,"exit_cap_delta":0,"shock":0,"growth_vol":.02},"BULL":{"rent_growth_delta":.015,"occupancy_delta":.03,"exit_cap_delta":-.005,"shock":0,"growth_vol":.01},"BEAR":{"rent_growth_delta":-.02,"occupancy_delta":-.08,"exit_cap_delta":.01,"shock":0,"growth_vol":.05},"ADVERSARIAL":{"rent_growth_delta":-.04,"occupancy_delta":-.15,"exit_cap_delta":.02,"shock":-.10,"growth_vol":.08},"TAIL RISK":{"rent_growth_delta":-.07,"occupancy_delta":-.25,"exit_cap_delta":.04,"shock":-.25,"growth_vol":.12}}
    summaries=[]
    for name,default in defaults.items():
        spec={**default,**scenario_overrides.get(name,{})}; g=growth+spec["rent_growth_delta"]; o=max(0,min(1,occ+spec["occupancy_delta"])); ec=max(.0001,exit_cap+spec["exit_cap_delta"]); rng=random.Random(seed+sum(map(ord,name))); outcomes=[]; exits=[]; dscrs=[]; mins=[]; cocs=[]; mults=[]; irrs=[]; dds=[]
        for _ in range(paths):
            p=_cre_path(price,base_noi,hold_period,rng,g,spec["growth_vol"],o,ec,debt,ds,amortization_years,rate,capex,gross_rent,operating_expenses,exp_growth,vacancy,spec["shock"],sale_cost,float(other_income or 0),interest_only); outcomes.append(p["equity_outcome"]); exits.append(p["exit_value"]); dds.append(_drawdown(p["equity_values"]));
            for key,target in (("dscr",dscrs),("minimum_dscr",mins),("cash_on_cash",cocs),("equity_multiple",mults),("irr",irrs)):
                if p[key] is not None: target.append(p[key])
        summaries.append({"scenario":name,"mean_equity_outcome":round(mean(outcomes),2),"median_equity_outcome":round(median(outcomes),2),"p05_equity_outcome":round(_percentile(outcomes,.05),2),"p95_equity_outcome":round(_percentile(outcomes,.95),2),"probability_loss":round(sum(v<equity_initial for v in outcomes)/paths,4) if equity_initial>0 else None,"max_drawdown_mean":round(mean(dds),4),"mean_exit_value":round(mean(exits),2),"mean_dscr":round(mean(dscrs),4) if dscrs else None,"minimum_dscr":round(min(mins),4) if mins else None,"mean_cash_on_cash":round(mean(cocs),4) if cocs else None,"mean_equity_multiple":round(mean(mults),4) if mults else None,"mean_irr":round(mean(irrs),4) if irrs else None,"scenario_assumptions":{"rent_growth":g,"occupancy":o,"exit_cap_rate":ec,"shock":spec["shock"],"growth_volatility":spec["growth_vol"]}})
    return {"engine":"AletheiaTelos Independent CRE Monte Carlo Risk Engine v2","independent_of_agents":True,"status":"SIMULATED","paths":paths,"hold_period":hold_period,"seed":seed,"initial_equity":equity_initial,"loan_amount":debt,"annual_debt_service":ds,"debt_service_method":method,"inputs":{"purchase_price":price,"noi":base_noi,"occupancy":occupancy,"gross_rent":gross_rent,"operating_expenses":operating_expenses,"rent_growth":rent_growth,"expense_growth":expense_growth,"interest_rate":interest_rate,"loan_to_value":loan_to_value,"amortization_years":amortization_years,"interest_only":interest_only,"exit_cap_rate":exit_cap_rate,"selling_cost_rate":selling_cost_rate,"capital_expenditures":capital_expenditures,"closing_costs":closing_costs,"other_income":other_income},"scenarios":summaries,"assumptions":assumptions or [],"scenario_assumptions_are_stresses_not_forecasts":True}


def cre_sensitivity(purchase_price, noi, hold_period=5, occupancy=None, rent_growth=None, interest_rate=None, loan_to_value=None, exit_cap_rate=None, expense_growth=None, operating_expenses=None, capital_expenditures=None, paths=1000, seed=42):
    """One-variable sensitivity using changes relative to supplied base assumptions."""
    base_cap=exit_cap_rate or noi/purchase_price
    base_kwargs=dict(occupancy=occupancy,rent_growth=rent_growth,interest_rate=interest_rate,loan_to_value=loan_to_value,exit_cap_rate=base_cap,expense_growth=expense_growth,operating_expenses=operating_expenses,capital_expenditures=capital_expenditures)
    base=run_cre_monte_carlo(purchase_price,noi,hold_period,paths,seed,**base_kwargs)
    cases={"rent_growth":[(-.02,"-2.0%"),(0,"0.0%"),(.02,"+2.0%")],"occupancy":[(.75,"75%"),(.90,"90%"),(.98,"98%")],"interest_rate":[(.05,"5.0%"),(.07,"7.0%"),(.09,"9.0%")],"exit_cap_rate":[(max(.0001,base_cap-.01),f"{max(.0001,base_cap-.01):.2%}"),(base_cap,f"{base_cap:.2%}"),(base_cap+.01,f"{base_cap+.01:.2%}")],"purchase_price":[(purchase_price*.9,"-10%"),(purchase_price,"Base"),(purchase_price*1.1,"+10%")],"operating_expenses":[(max(0,(operating_expenses or 0)*.9),"-10%"),(operating_expenses or 0,"Base"),(operating_expenses*1.1 if operating_expenses is not None else 0,"+10%")],"loan_to_value":[(.50,"50%"),(.65,"65%"),(.75,"75%")]}
    results={"base":base,"variables":{}}
    for variable,values in cases.items():
        rows=[]
        for value,label in values:
            kwargs=dict(base_kwargs); pp=purchase_price
            if variable=="purchase_price": pp=value
            else: kwargs[variable]=value
            sim=run_cre_monte_carlo(pp,noi,hold_period,paths,seed,**kwargs); row=next((s for s in sim.get("scenarios",[]) if s["scenario"]=="BASE"),None); rows.append({"value":label,"base_scenario":row})
        results["variables"][variable]=rows
    return results
