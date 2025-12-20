"""
ApparelDesk High-Precision Discount & Profitability Engine
===========================================================

A FastAPI-based financial simulation service that calculates net profit with 
decimal precision and provides intelligent business advisory insights.

Author: Senior Financial Systems Architect
Version: 1.1.0 (Production Ready)
"""

import os
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum
import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables from a .env file (for local development)
load_dotenv()

# ============================================================================
# CONFIGURATION & DATABASE CONNECTION (SECURE)
# ============================================================================

def get_db_config():
    """Parses DATABASE_URL from environment variables for secure connection."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Fallback for local testing if env var is missing (NOT for production)
        return {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "appareldesk",
            "charset": "utf8mb4"
        }
    
    # Parse the Railway/Render connection URL
    # Format: mysql://user:password@host:port/database
    url = urlparse(db_url)
    return {
        "host": url.hostname,
        "user": url.username,
        "password": url.password,
        "database": url.path[1:],  # Removes the leading slash
        "port": url.port or 3306,
        "charset": "utf8mb4"
    }

@contextmanager
def get_db_connection():
    """Context manager for database connections with automatic cleanup."""
    connection = None
    try:
        config = get_db_config()
        connection = mysql.connector.connect(**config)
        yield connection
    except Error as e:
        print(f"Database Error: {e}") # Log error to console
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
    finally:
        if connection and connection.is_connected():
            connection.close()


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class MarginHealthStatus(str, Enum):
    """Margin health classification thresholds."""
    CRITICAL = "critical"  # < 5%
    WARNING = "warning"    # 5-15%
    HEALTHY = "healthy"    # > 15%


class StrategyInsight(str, Enum):
    """Business strategy recommendations."""
    LOSS_TRANSACTION = "loss_transaction"
    LIQUIDATION_ACCEPTABLE = "liquidation_acceptable"
    OPTIMAL_MARGIN = "optimal_margin"
    PREMIUM_PRICING = "premium_pricing"


# Operational overhead percentage (configurable)
OPERATIONAL_FEE_PERCENTAGE = Decimal("2.5")  # 2.5% of revenue
STOCK_LIQUIDATION_THRESHOLD = Decimal("50.0")  # High stock threshold


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class SimulationRequest(BaseModel):
    """Request model for profit simulation."""
    product_id: int = Field(..., gt=0, description="Product ID from products table")
    coupon_code: Optional[str] = Field(None, description="Optional coupon code")
    payment_term_id: int = Field(..., gt=0, description="Payment term ID")
    quantity: Decimal = Field(Decimal("1.0"), gt=0, description="Quantity to simulate")

    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than zero')
        return v.quantize(Decimal("0.001"))


class MoneyWaterfall(BaseModel):
    """Detailed breakdown of profit calculation."""
    gross_revenue: Decimal = Field(..., description="Base revenue (price × quantity)")
    discount_amount: Decimal = Field(..., description="Total discount applied")
    net_revenue: Decimal = Field(..., description="Revenue after discount")
    cogs: Decimal = Field(..., description="Cost of Goods Sold")
    sales_tax: Decimal = Field(..., description="Sales tax amount")
    early_payment_discount: Decimal = Field(..., description="Early payment discount cost")
    operational_fees: Decimal = Field(..., description="Estimated operational overhead")
    total_costs: Decimal = Field(..., description="Sum of all costs")
    net_profit: Decimal = Field(..., description="Final profit/loss")
    profit_margin_percentage: Decimal = Field(..., description="Profit as % of net revenue")


class MarginAnalysis(BaseModel):
    """Intelligent margin health assessment."""
    health_status: MarginHealthStatus
    health_score: Decimal = Field(..., description="Numeric margin percentage")
    strategy_insight: StrategyInsight
    recommendation: str = Field(..., description="Human-readable advisory")
    risk_factors: List[str] = Field(default_factory=list)


class ScenarioComparison(BaseModel):
    """What-if analysis comparing multiple scenarios."""
    scenario_name: str
    discount_percentage: Decimal
    net_profit: Decimal
    profit_margin: Decimal
    is_profitable: bool


class SimulationResponse(BaseModel):
    """Complete simulation response with all analysis."""
    product_info: Dict[str, Any]
    waterfall: MoneyWaterfall
    margin_analysis: MarginAnalysis
    scenarios: List[ScenarioComparison]
    timestamp: datetime


# ============================================================================
# DATA ACCESS LAYER
# ============================================================================

class ProductRepository:
    """Repository for product-related database operations."""
    
    @staticmethod
    def get_product_details(connection, product_id: int) -> Optional[Dict]:
        """Fetch complete product details including pricing and stock."""
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT 
                product_id,
                product_name,
                product_code,
                sales_price,
                purchase_price,
                sales_tax_percentage,
                current_stock,
                minimum_stock,
                is_active
            FROM products
            WHERE product_id = %s AND is_active = TRUE
        """
        cursor.execute(query, (product_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            # Convert to Decimal for precision
            result['sales_price'] = Decimal(str(result['sales_price']))
            result['purchase_price'] = Decimal(str(result['purchase_price']))
            result['sales_tax_percentage'] = Decimal(str(result['sales_tax_percentage']))
            result['current_stock'] = Decimal(str(result['current_stock']))
            result['minimum_stock'] = Decimal(str(result['minimum_stock']))
        
        return result


class DiscountRepository:
    """Repository for discount and coupon operations."""
    
    @staticmethod
    def get_coupon_discount(connection, coupon_code: str) -> Optional[Decimal]:
        """Fetch active discount percentage for a coupon code."""
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT 
                do.discount_percentage
            FROM coupon_codes cc
            JOIN discount_offers do ON cc.discount_offer_id = do.discount_offer_id
            WHERE 
                cc.coupon_code = %s 
                AND cc.is_active = TRUE
                AND cc.coupon_status = 'unused'
                AND do.is_active = TRUE
                AND CURDATE() BETWEEN do.start_date AND do.end_date
        """
        cursor.execute(query, (coupon_code,))
        result = cursor.fetchone()
        cursor.close()
        
        return Decimal(str(result['discount_percentage'])) if result else None


class PaymentTermRepository:
    """Repository for payment term operations."""
    
    @staticmethod
    def get_payment_term_details(connection, payment_term_id: int) -> Optional[Dict]:
        """Fetch payment term including early payment discount details."""
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT 
                payment_term_id,
                term_name,
                net_days,
                early_payment_discount,
                discount_percentage,
                discount_days,
                early_pay_discount_computation
            FROM payment_terms
            WHERE payment_term_id = %s AND is_active = TRUE
        """
        cursor.execute(query, (payment_term_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if result and result['discount_percentage']:
            result['discount_percentage'] = Decimal(str(result['discount_percentage']))
        
        return result


# ============================================================================
# PROFIT CALCULATION ENGINE
# ============================================================================

class ProfitCalculator:
    """High-precision profit calculation engine using Decimal arithmetic."""
    
    @staticmethod
    def quantize(value: Decimal, places: str = "0.01") -> Decimal:
        """Round decimal to specified precision."""
        return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)
    
    def calculate_waterfall(
        self,
        product: Dict,
        quantity: Decimal,
        discount_pct: Decimal,
        payment_term: Dict
    ) -> MoneyWaterfall:
        """
        Calculate complete profit waterfall with all cost components.
        """
        # Step 1: Gross Revenue
        gross_revenue = self.quantize(product['sales_price'] * quantity)
        
        # Step 2: Discount Amount
        discount_amount = self.quantize(
            gross_revenue * (discount_pct / Decimal("100"))
        )
        
        # Step 3: Net Revenue (after discount)
        net_revenue = gross_revenue - discount_amount
        
        # Step 4: Cost of Goods Sold
        cogs = self.quantize(product['purchase_price'] * quantity)
        
        # Step 5: Sales Tax (on post-discount price)
        sales_tax = self.quantize(
            net_revenue * (product['sales_tax_percentage'] / Decimal("100"))
        )
        
        # Step 6: Early Payment Discount Cost (if applicable)
        early_payment_discount = Decimal("0.00")
        if payment_term and payment_term.get('early_payment_discount'):
            base_amount = (
                net_revenue if payment_term['early_pay_discount_computation'] == 'base_amount'
                else net_revenue + sales_tax
            )
            early_payment_discount = self.quantize(
                base_amount * (payment_term['discount_percentage'] / Decimal("100"))
            )
        
        # Step 7: Operational Fees
        operational_fees = self.quantize(
            gross_revenue * (OPERATIONAL_FEE_PERCENTAGE / Decimal("100"))
        )
        
        # Step 8: Total Costs
        total_costs = cogs + sales_tax + early_payment_discount + operational_fees
        
        # Step 9: Net Profit
        net_profit = net_revenue - total_costs
        
        # Step 10: Profit Margin Percentage
        profit_margin_pct = (
            self.quantize((net_profit / net_revenue) * Decimal("100"), "0.01")
            if net_revenue > 0 else Decimal("0.00")
        )
        
        return MoneyWaterfall(
            gross_revenue=gross_revenue,
            discount_amount=discount_amount,
            net_revenue=net_revenue,
            cogs=cogs,
            sales_tax=sales_tax,
            early_payment_discount=early_payment_discount,
            operational_fees=operational_fees,
            total_costs=total_costs,
            net_profit=net_profit,
            profit_margin_percentage=profit_margin_pct
        )
    
    def calculate_breakeven_discount(
        self,
        product: Dict,
        quantity: Decimal,
        payment_term: Dict
    ) -> Decimal:
        """
        Calculate maximum discount percentage that results in zero profit.
        Uses binary search to find the breakeven point.
        """
        low, high = Decimal("0"), Decimal("100")
        tolerance = Decimal("0.01")
        
        for _ in range(100):  # Max iterations
            mid = (low + high) / Decimal("2")
            waterfall = self.calculate_waterfall(product, quantity, mid, payment_term)
            
            if abs(waterfall.net_profit) < tolerance:
                return self.quantize(mid, "0.01")
            
            if waterfall.net_profit > 0:
                low = mid
            else:
                high = mid
        
        return self.quantize(low, "0.01")


# ============================================================================
# BUSINESS INTELLIGENCE ADVISOR
# ============================================================================

class ProfitAdvisor:
    """Intelligent business advisory component for margin analysis."""
    
    @staticmethod
    def analyze_margin(
        waterfall: MoneyWaterfall,
        product: Dict,
        discount_pct: Decimal
    ) -> MarginAnalysis:
        """
        Analyze profit margin and provide strategic insights.
        """
        margin_pct = waterfall.profit_margin_percentage
        current_stock = product['current_stock']
        risk_factors = []
        
        # Determine health status
        if margin_pct < Decimal("5"):
            health_status = MarginHealthStatus.CRITICAL
        elif margin_pct < Decimal("15"):
            health_status = MarginHealthStatus.WARNING
        else:
            health_status = MarginHealthStatus.HEALTHY
        
        # Determine strategy insight
        if margin_pct < Decimal("0"):
            strategy_insight = StrategyInsight.LOSS_TRANSACTION
            recommendation = (
                f"🚨 REJECT: This transaction results in a loss of "
                f"₹{abs(waterfall.net_profit)}. Consider reducing discount or "
                f"rejecting the sale."
            )
            risk_factors.append("Negative profit margin")
            
        elif margin_pct < Decimal("5"):
            if current_stock > STOCK_LIQUIDATION_THRESHOLD:
                strategy_insight = StrategyInsight.LIQUIDATION_ACCEPTABLE
                recommendation = (
                    f"⚠️ CAUTION: Minimal {margin_pct}% margin, but acceptable "
                    f"for inventory liquidation (stock: {current_stock} units). "
                    f"Approve for clearance purposes only."
                )
                risk_factors.append("Critical margin but high inventory")
            else:
                strategy_insight = StrategyInsight.LOSS_TRANSACTION
                recommendation = (
                    f"🚨 REJECT: Critical {margin_pct}% margin with low stock "
                    f"({current_stock} units). This is a loss transaction - "
                    f"reduce discount or increase price."
                )
                risk_factors.append("Critical margin with low inventory")
                
        elif margin_pct < Decimal("15"):
            strategy_insight = StrategyInsight.OPTIMAL_MARGIN
            recommendation = (
                f"✅ APPROVE: Acceptable {margin_pct}% margin. Transaction is "
                f"profitable but monitor closely for volume opportunities."
            )
            if current_stock < product['minimum_stock']:
                risk_factors.append("Stock below minimum threshold")
                
        else:
            strategy_insight = StrategyInsight.PREMIUM_PRICING
            recommendation = (
                f"✅ EXCELLENT: Strong {margin_pct}% margin. Premium pricing "
                f"achieved. Consider this as a benchmark for future pricing."
            )
        
        # Additional risk factors
        if discount_pct > Decimal("30"):
            risk_factors.append(f"High discount applied: {discount_pct}%")
        
        if waterfall.early_payment_discount > Decimal("0"):
            risk_factors.append(
                f"Early payment discount cost: ₹{waterfall.early_payment_discount}"
            )
        
        return MarginAnalysis(
            health_status=health_status,
            health_score=margin_pct,
            strategy_insight=strategy_insight,
            recommendation=recommendation,
            risk_factors=risk_factors
        )


# ============================================================================
# SCENARIO ANALYSIS ENGINE
# ============================================================================

class ScenarioAnalyzer:
    """What-if analysis for comparing multiple pricing scenarios."""
    
    def __init__(self, calculator: ProfitCalculator):
        self.calculator = calculator
    
    def compare_scenarios(
        self,
        product: Dict,
        quantity: Decimal,
        current_discount: Decimal,
        payment_term: Dict
    ) -> List[ScenarioComparison]:
        """
        Generate three scenario comparisons:
        1. No discount (full margin)
        2. Current discount applied
        3. Breakeven discount (zero profit threshold)
        """
        scenarios = []
        
        # Scenario 1: No Discount
        waterfall_no_disc = self.calculator.calculate_waterfall(
            product, quantity, Decimal("0"), payment_term
        )
        scenarios.append(ScenarioComparison(
            scenario_name="No Discount (Full Margin)",
            discount_percentage=Decimal("0.00"),
            net_profit=waterfall_no_disc.net_profit,
            profit_margin=waterfall_no_disc.profit_margin_percentage,
            is_profitable=waterfall_no_disc.net_profit > 0
        ))
        
        # Scenario 2: Current Discount
        waterfall_current = self.calculator.calculate_waterfall(
            product, quantity, current_discount, payment_term
        )
        scenarios.append(ScenarioComparison(
            scenario_name="Current Discount Applied",
            discount_percentage=current_discount,
            net_profit=waterfall_current.net_profit,
            profit_margin=waterfall_current.profit_margin_percentage,
            is_profitable=waterfall_current.net_profit > 0
        ))
        
        # Scenario 3: Breakeven Discount
        breakeven_discount = self.calculator.calculate_breakeven_discount(
            product, quantity, payment_term
        )
        waterfall_breakeven = self.calculator.calculate_waterfall(
            product, quantity, breakeven_discount, payment_term
        )
        scenarios.append(ScenarioComparison(
            scenario_name="Maximum Breakeven Discount",
            discount_percentage=breakeven_discount,
            net_profit=waterfall_breakeven.net_profit,
            profit_margin=waterfall_breakeven.profit_margin_percentage,
            is_profitable=waterfall_breakeven.net_profit >= 0
        ))
        
        return scenarios


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="ApparelDesk Profit Simulation Engine",
    description="High-precision financial simulation with intelligent advisory",
    version="1.0.0"
)

# ADDED: CORS Middleware to allow frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (change to specific domain in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/simulate-profit", response_model=SimulationResponse)
async def simulate_profit(request: SimulationRequest):
    """
    Simulate profit for a transaction with detailed waterfall analysis.
    """
    with get_db_connection() as connection:
        # Fetch product details
        product = ProductRepository.get_product_details(connection, request.product_id)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product ID {request.product_id} not found or inactive"
            )
        
        # Fetch discount percentage if coupon provided
        discount_pct = Decimal("0.00")
        if request.coupon_code:
            discount_pct = DiscountRepository.get_coupon_discount(
                connection, request.coupon_code
            )
            if discount_pct is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Coupon '{request.coupon_code}' not found or expired"
                )
        
        # Fetch payment term details
        payment_term = PaymentTermRepository.get_payment_term_details(
            connection, request.payment_term_id
        )
        if not payment_term:
            raise HTTPException(
                status_code=404,
                detail=f"Payment term ID {request.payment_term_id} not found"
            )
        
        # Initialize calculation engines
        calculator = ProfitCalculator()
        advisor = ProfitAdvisor()
        scenario_analyzer = ScenarioAnalyzer(calculator)
        
        # Calculate profit waterfall
        waterfall = calculator.calculate_waterfall(
            product, request.quantity, discount_pct, payment_term
        )
        
        # Generate margin analysis
        margin_analysis = advisor.analyze_margin(waterfall, product, discount_pct)
        
        # Generate scenario comparisons
        scenarios = scenario_analyzer.compare_scenarios(
            product, request.quantity, discount_pct, payment_term
        )
        
        # Build response
        return SimulationResponse(
            product_info={
                "product_id": product['product_id'],
                "product_name": product['product_name'],
                "product_code": product['product_code'],
                "current_stock": float(product['current_stock']),
                "quantity_simulated": float(request.quantity),
                "coupon_applied": request.coupon_code,
                "discount_percentage": float(discount_pct),
                "payment_term": payment_term['term_name']
            },
            waterfall=waterfall,
            margin_analysis=margin_analysis,
            scenarios=scenarios,
            timestamp=datetime.now()
        )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "ApparelDesk Profit Engine",
        "version": "1.0.0"
    }


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  ApparelDesk High-Precision Profit Simulation Engine           ║
    ║  Starting FastAPI server...                                    ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    # Run securely with default host/port
    uvicorn.run(app, host="0.0.0.0", port=8000)