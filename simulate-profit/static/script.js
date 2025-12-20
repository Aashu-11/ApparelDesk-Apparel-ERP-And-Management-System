const { useState, useEffect } = React;

const ProfitSimulation = () => {
    // State
    const [formData, setFormData] = useState({
        product_id: '',
        coupon_code: '',
        payment_term_id: '',
        quantity: '1.000'
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);

    // Handlers
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const requestData = {
                product_id: parseInt(formData.product_id),
                payment_term_id: parseInt(formData.payment_term_id),
                quantity: parseFloat(formData.quantity) || 1.0
            };

            if (formData.coupon_code && formData.coupon_code.trim()) {
                requestData.coupon_code = formData.coupon_code.trim();
            }

            const response = await fetch('/api/simulate-profit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Simulation failed');
            }

            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (val) => {
        const num = parseFloat(val);
        const sign = num >= 0 ? '' : '-';
        return `${sign}₹${Math.abs(num).toFixed(2)}`;
    };

    // Render Helpers
    const renderWaterfall = (waterfall) => {
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

        return (
            <div className="waterfall-items">
                {items.map((item, idx) => (
                    <div key={idx} className="waterfall-item">
                        <span className="waterfall-label">{item.label}</span>
                        <span className={`waterfall-value ${item.type}`}>
                            {formatCurrency(item.value)}
                        </span>
                    </div>
                ))}
            </div>
        );
    };

    return (
        <React.Fragment>
            <div className="container">
                <div className="collection-label">SIMULATION 01</div>
                <h1 className="main-title">PROFIT SIMULATION</h1>
                <p className="subtitle">
                    Redefining financial intelligence with our high-precision simulation engine. 
                    Impeccable accuracy meets contemporary analysis.
                </p>

                <form onSubmit={handleSubmit} className="simulation-form">
                    <div className="form-group">
                        <label htmlFor="productId">Coupon ID</label>
                        <input 
                            type="number" 
                            id="productId" 
                            name="product_id" 
                            required 
                            min="1"
                            placeholder="Enter coupon ID"
                            value={formData.product_id}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="couponCode">Coupon Code (Optional)</label>
                        <input 
                            type="text" 
                            id="couponCode" 
                            name="coupon_code" 
                            placeholder="e.g., SUMMER2024"
                            value={formData.coupon_code}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="paymentTermId">Payment Term ID</label>
                        <input 
                            type="number" 
                            id="paymentTermId" 
                            name="payment_term_id" 
                            required 
                            min="1"
                            placeholder="Enter payment term ID"
                            value={formData.payment_term_id}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="quantity">Quantity</label>
                        <input 
                            type="number" 
                            id="quantity" 
                            name="quantity" 
                            required 
                            min="0.001"
                            step="0.001"
                            placeholder="1.000"
                            value={formData.quantity}
                            onChange={handleChange}
                        />
                    </div>

                    <button type="submit" className="submit-btn" disabled={loading}>
                        {loading ? 'CALCULATING...' : 'START SIMULATION'}
                        {!loading && <span>→</span>}
                    </button>
                </form>

                {/* Results Section */}
                {result && (
                    <div className="results-container">
                        <div className="results-header">
                            <h2>ANALYSIS RESULTS</h2>
                            <p>{result.product_info.product_name}</p>
                        </div>

                        <div className="kpi-grid">
                            <div className="kpi-card">
                                <div className="kpi-label">Net Revenue</div>
                                <div className="kpi-value">{formatCurrency(result.waterfall.net_revenue)}</div>
                            </div>
                            <div className="kpi-card">
                                <div className="kpi-label">Total Costs</div>
                                <div className="kpi-value">{formatCurrency(result.waterfall.total_costs)}</div>
                            </div>
                            <div className="kpi-card">
                                <div className="kpi-label">Net Profit</div>
                                <div className="kpi-value" style={{color: result.waterfall.net_profit >= 0 ? '#000' : '#EF4444'}}>
                                    {formatCurrency(result.waterfall.net_profit)}
                                </div>
                            </div>
                        </div>

                        <div className="waterfall-section">
                            <h3 style={{fontFamily: 'Anton', marginBottom: '1rem', textTransform: 'uppercase'}}>Financial Waterfall</h3>
                            {renderWaterfall(result.waterfall)}
                        </div>

                        <div className="advisor-section">
                            <div className="advisor-title">Strategic Insight</div>
                            <div className="advisor-content">
                                <p><strong>Recommendation:</strong> {result.margin_analysis.recommendation}</p>
                                {result.margin_analysis.risk_factors.length > 0 && (
                                    <ul style={{marginTop: '1rem', paddingLeft: '1.5rem'}}>
                                        {result.margin_analysis.risk_factors.map((risk, i) => (
                                            <li key={i}>{risk}</li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {error && (
                    <div style={{marginTop: '2rem', color: '#EF4444', textAlign: 'center'}}>
                        <p>{error}</p>
                    </div>
                )}
            </div>
        </React.Fragment>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<ProfitSimulation />);
