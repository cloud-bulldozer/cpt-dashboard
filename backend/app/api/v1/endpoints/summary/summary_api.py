import asyncio
from dataclasses import dataclass
from typing import Annotated, Any, Callable, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.endpoints.ocp.summary import OcpSummary
from app.api.v1.endpoints.summary.summary import Summary

router = APIRouter()

"""Access product "release readiness" summary data.

AI assistance: Cursor is extremely insistant on generating suggested code
snippets along the way, some of which are annoyingly stupid and surprizingly
many of which are remarkably insightful. While most of this code is hand
generated as the relationships are tricky and difficult to describe to the AI,
Cursor has been extremely helpful as an "over the shoulder assistant" to
simplify routine coding tasks. (It excels at recognizing repeated change
patterns during refactoring, for example.)

Assisted-by: Cursor + claude-4-sonnet
"""

router = APIRouter()


@dataclass
class Product:
    summaryclass: type[Summary]
    configpath: str


@dataclass
class ProductContext:
    product: str
    instance: Summary


@dataclass
class ProductResults:
    product: str
    results: dict[str, Any]


PRODUCTS = {
    "ocp": Product(OcpSummary, "ocp.elasticsearch"),
}


def create(product: str) -> "Summary":
    """Create a summary service for a given product."""
    if product in PRODUCTS:
        c = PRODUCTS[product]
        return c.summaryclass(product, c.configpath)
    raise NotImplementedError("Not implemented")


async def summary_svc(products: str) -> dict[str, ProductContext]:
    """FastAPI Dependency to open & close ElasticService connections"""
    summaries: dict[str, ProductContext] = {}
    ps = Summary.break_list(products)
    try:
        summaries = {
            product: ProductContext(product, create(product)) for product in ps
        }
        yield summaries
    except Exception as e:
        print(f"Error opening {products} summary service: {e}")
        raise HTTPException(
            status_code=400, detail=f"Product {products} can't be opened: {str(e)!r}"
        )
    finally:
        if summaries:
            await asyncio.gather(
                *[summary.instance.close() for summary in summaries.values()]
            )


async def collect(
    products: str,
    context: list[ProductContext],
    method: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Launch multiple product queries concurrently and collect results

    Args:
        products: The products to get versions for (comma separated list)
        context: A dictionary of summary services for each product
        method: Name of the Summary class method to call
        start_date: The start date to filter the versions by
        end_date: The end date to filter the versions by
    """
    results = {}
    for p in Summary.break_list(products):
        try:
            c = context[p]
            summary = c.instance
            m = getattr(summary, method)
            if not isinstance(m, Callable):
                raise ValueError(f"{p} {method} is not callable")
            print(f"collect {method}: {start_date} - {end_date}")
            summary.set_date_filter(start_date, end_date)
            results[p] = m(**kwargs)
        except Exception as e:
            print(f"Error collecting {p} {method}: {e}")
    ret = {}
    for name, result in results.items():
        ret[name] = await result
    return ret


@router.get("/api/v1/summary/products")
async def products() -> list[str]:
    """Return a list of products that have testing data."""
    return list(PRODUCTS.keys())


@router.get("/api/v1/summary/versions")
async def versions(
    summaries: Annotated[Summary, Depends(summary_svc)],
    products: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict[str, dict[str, list[str]]]:
    """Return a list of versions that have been tested

    This report can be filtered to a date range.

    Args:
        summaries: A dictionary of summary services for each product
        products: The products to get versions for (comma separated list)
        start_date: The start date to filter the versions by
        end_date: The end date to filter the versions by
    """
    return await collect(
        products, summaries, "get_versions", start_date=start_date, end_date=end_date
    )


@router.get("/api/v1/summary/benchmarks")
async def configs(
    summaries: Annotated[Summary, Depends(summary_svc)],
    products: str,
    versions: Optional[str] = None,
    benchmarks: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict[str, Any]:
    """Return a list of benchmarks that have been tested

    This report can be filtered to a date range.

    Args:
        summaries: A dictionary of summary services for each product
        products: The products to get benchmarks for (comma separated list)
        versions: The versions to get benchmarks for (comma separated list)
        benchmarks: The benchmarks to get details for (comma separated list)
        start_date: The start date to filter the benchmarks by
        end_date: The end date to filter the benchmarks by
    """
    return await collect(
        products,
        summaries,
        "get_configs",
        start_date=start_date,
        end_date=end_date,
        versions=versions,
        benchmarks=benchmarks,
    )


@router.get("/api/v1/summary")
async def summary(
    summaries: Annotated[Summary, Depends(summary_svc)],
    products: str,
    versions: Optional[str] = None,
    benchmarks: Optional[str] = None,
    configs: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict[str, Any]:
    """Generate statistical summary data

    Args:
        summaries: A dictionary of summary services for each product
        products: The products to get benchmarks for (comma separated list)
        versions: The versions to get benchmarks for (comma separated list)
        benchmarks: The benchmarks to get details for (comma separated list)
        configs: The specific configuration(s) to find (comma separated list)
        start_date: The start date to filter the benchmarks by
        end_date: The end date to filter the benchmarks by
    """
    return await collect(
        products,
        summaries,
        "metric_aggregation",
        start_date=start_date,
        end_date=end_date,
        versions=versions,
        benchmarks=benchmarks,
        configs=configs,
    )
