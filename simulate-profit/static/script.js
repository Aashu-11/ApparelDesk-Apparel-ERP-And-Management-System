// ============================================================================
// PROFIT SIMULATION - INTERACTIVE JAVASCRIPT
// ============================================================================

// DOM Elements
const form = document.getElementById('simulationForm');
const submitBtn = document.getElementById('submitBtn');
const emptyState = document.getElementById('emptyState');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const resultsContent = document.getElementById('resultsContent');
const errorMessage = document.getElementById('errorMessage');

// API Configuration
const API_BASE = window.location.origin;

// ============================================================================
// FORM SUBMISSION HANDLER
// ============================================================================

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Get form data
    const formData = new FormData(form);
    const requestData = {
        product_id: parseInt(formData.get('product_id')),
        payment_term_id: parseInt(formData.get('payment_term_id')),
        quantity: parseFloat(formData.get('quantity')) || 1.0
    };
    
    // Add coupon code if provided
    const couponCode = formData.get('coupon_code');
    if (couponCode && couponCode.trim()) {
        requestData.coupon_code = couponCode.trim();
    }
    
    // Show loading state
    showLoading();
    
    try {
        // Call API
        const response = await fetch(`${API_BASE}/api/simulate-profit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Simulation failed');
        }
        
        const data = await response.json();
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        showError(error.message);
    }
});

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

function showLoading() {
    emptyState.style.display = 'none';
    errorState.style.display = 'none';
    resultsContent.style.display = 'none';
    loadingState.style.display = 'flex';
    submitBtn.disabled = true;
}

function showError(message) {
    emptyState.style.display = 'none';
    loadingState.style.display = 'none';
    resultsContent.style.display = 'none';
    errorState.style.display = 'flex';
    errorMessage.textContent = message;
    submitBtn.disabled = false;
}

function hideError() {
    errorState.style.display = 'none';
    emptyState.style.display = 'flex';
}

function showResults() {
    emptyState.style.display = 'none';
    loadingState.style.display = 'none';
    errorState.style.display = 'none';
    resultsContent.style.display = 'flex';
    submitBtn.disabled = false;
}

// ============================================================================
// RESULTS RENDERING
// ============================================================================

function displayResults(data) {
    // Render Product Info
    renderProductInfo(data.product_info);
    
    // Render Margin Analysis
    renderMarginAnalysis(data.margin_analysis);
    
    // Render Waterfall
    renderWaterfall(data.waterfall);
    
    // Render Scenarios
    renderScenarios(data.scenarios);
    
    // Show results
    showResults();
}

// ============================================================================
// PRODUCT INFO RENDERER
// ============================================================================

function renderProductInfo(productInfo) {
    const container = document.getElementById('productInfo');
    
    container.innerHTML = `
        <h3>📦 ${productInfo.product_name}</h3>
        <div class="product-details">
            <div class="product-detail">
                <span class="detail-label">Product Code</span>
                <span class="detail-value">${productInfo.product_code}</span>
            </div>
            <div class="product-detail">
                <span class="detail-label">Quantity</span>
                <span class="detail-value">${productInfo.quantity_simulated}</span>
            </div>
            <div class="product-detail">
                <span class="detail-label">Current Stock</span>
                <span class="detail-value">${productInfo.current_stock} units</span>
            </div>
            <div class="product-detail">
                <span class="detail-label">Payment Term</span>
                <span class="detail-value">${productInfo.payment_term}</span>
            </div>
            ${productInfo.coupon_applied ? `
                <div class="product-detail">
                    <span class="detail-label">Coupon Applied</span>
                    <span class="detail-value">${productInfo.coupon_applied}</span>
                </div>
                <div class="product-detail">
                    <span class="detail-label">Discount</span>
                    <span class="detail-value">${productInfo.discount_percentage}%</span>
                </div>
            ` : ''}
        </div>
    `;
}

// ============================================================================
// MARGIN ANALYSIS RENDERER
// ============================================================================

function renderMarginAnalysis(analysis) {
    const container = document.getElementById('marginAnalysis');
    
    // Determine health class
    const healthClass = analysis.health_status;
    
    // Get emoji for status
    const statusEmoji = {
        'healthy': '✅',
        'warning': '⚠️',
        'critical': '🚨'
    }[healthClass] || '📊';
    
    container.className = `margin-analysis ${healthClass}`;
    
    container.innerHTML = `
        <div class="margin-header">
            <div>
                <h3>${statusEmoji} Margin Analysis</h3>
                <p style="opacity: 0.9; margin: 0;">${analysis.health_status.toUpperCase()}</p>
            </div>
            <div class="margin-score">${parseFloat(analysis.health_score).toFixed(2)}%</div>
        </div>
        <div class="recommendation">${analysis.recommendation}</div>
        ${analysis.risk_factors.length > 0 ? `
            <div class="risk-factors">
                ${analysis.risk_factors.map(risk => `
                    <span class="risk-tag">⚡ ${risk}</span>
                `).join('')}
            </div>
        ` : ''}
    `;
}

// ============================================================================
// WATERFALL RENDERER
// ============================================================================

function renderWaterfall(waterfall) {
    const container = document.getElementById('waterfallItems');
    
    const items = [
        { label: 'Gross Revenue', value: waterfall.gross_revenue, type: 'positive' },
        { label: 'Discount Amount', value: -waterfall.discount_amount, type: 'negative' },
        { label: 'Net Revenue', value: waterfall.net_revenue, type: 'neutral' },
        { label: 'Cost of Goods Sold (COGS)', value: -waterfall.cogs, type: 'negative' },
        { label: 'Sales Tax', value: -waterfall.sales_tax, type: 'negative' },
        { label: 'Early Payment Discount', value: -waterfall.early_payment_discount, type: 'negative' },
        { label: 'Operational Fees', value: -waterfall.operational_fees, type: 'negative' },
        { label: 'Total Costs', value: -waterfall.total_costs, type: 'negative' },
        { label: 'Net Profit', value: waterfall.net_profit, type: waterfall.net_profit >= 0 ? 'positive' : 'negative' }
    ];
    
    container.innerHTML = items.map(item => `
        <div class="waterfall-item">
            <span class="waterfall-label">${item.label}</span>
            <span class="waterfall-value ${item.type}">
                ${formatCurrency(item.value)}
            </span>
        </div>
    `).join('');
}

// ============================================================================
// SCENARIOS RENDERER
// ============================================================================

function renderScenarios(scenarios) {
    const container = document.getElementById('scenariosGrid');
    
    container.innerHTML = scenarios.map(scenario => `
        <div class="scenario-card ${scenario.is_profitable ? 'profitable' : 'unprofitable'}">
            <div class="scenario-name">${scenario.scenario_name}</div>
            <div class="scenario-metrics">
                <div class="scenario-metric">
                    <span class="metric-label">Discount</span>
                    <span class="metric-value">${parseFloat(scenario.discount_percentage).toFixed(2)}%</span>
                </div>
                <div class="scenario-metric">
                    <span class="metric-label">Net Profit</span>
                    <span class="metric-value ${scenario.net_profit >= 0 ? 'positive' : 'negative'}">
                        ${formatCurrency(scenario.net_profit)}
                    </span>
                </div>
                <div class="scenario-metric">
                    <span class="metric-label">Margin</span>
                    <span class="metric-value">${parseFloat(scenario.profit_margin).toFixed(2)}%</span>
                </div>
                <div class="scenario-metric">
                    <span class="metric-label">Status</span>
                    <span class="metric-value">
                        ${scenario.is_profitable ? '✅ Profitable' : '❌ Loss'}
                    </span>
                </div>
            </div>
        </div>
    `).join('');
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function formatCurrency(value) {
    const num = parseFloat(value);
    const formatted = Math.abs(num).toFixed(2);
    const sign = num >= 0 ? '' : '-';
    return `${sign}₹${formatted}`;
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Profit Simulation Engine Initialized');
    
    // Add smooth scroll behavior
    document.documentElement.style.scrollBehavior = 'smooth';
    
    // Add input animations
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            input.parentElement.style.transform = 'scale(1.02)';
        });
        
        input.addEventListener('blur', () => {
            input.parentElement.style.transform = 'scale(1)';
        });
    });
});
