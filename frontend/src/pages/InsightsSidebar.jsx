import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar, Legend } from 'recharts';
import api from '../api.js';

/* ── Mini helpers ── */
function MiniCard({ label, value, unit = '', color = '#1a6cf5', icon }) {
    return (
        <div style={{
            background: '#fff', borderRadius: 12, border: '1px solid rgba(15,40,90,0.10)',
            boxShadow: '0 2px 10px rgba(15,40,90,0.07)', padding: '14px 16px',
            display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 130,
        }}>
            {icon && <span style={{ fontSize: 22, marginBottom: 2 }}>{icon}</span>}
            <div style={{ fontSize: 22, fontWeight: 800, color, fontFamily: 'JetBrains Mono,monospace' }}>
                {value}<span style={{ fontSize: 13, fontWeight: 600 }}> {unit}</span>
            </div>
            <div style={{ fontSize: 11, color: '#9aafc4', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</div>
        </div>
    );
}

function SectionHead({ children, badge }) {
    return (
        <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            borderBottom: '1px solid rgba(15,40,90,0.09)', padding: '10px 16px',
        }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: '#1a6cf5', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{children}</span>
            {badge && <span style={{ fontSize: 10, color: '#9aafc4', fontWeight: 600 }}>{badge}</span>}
        </div>
    );
}

/* ─────────────────────────────────────────────────────────────────────────
   PANEL 1 — Model Accuracy Proof
───────────────────────────────────────────────────────────────────────── */
function AccuracyPanel() {
    const [summary, setSummary] = useState(null);
    const [perRoute, setPerRoute] = useState([]);
    const [pvData, setPvData] = useState([]);
    const [selRoute, setSelRoute] = useState('R155');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            try {
                const [s, r] = await Promise.all([api.getAccuracySummary(), api.getModelAccuracy()]);
                setSummary(s); setPerRoute(r);
                setSelRoute(r[0]?.route_id || 'R155');
            } catch (e) { console.error(e); }
            finally { setLoading(false); }
        };
        load();
    }, []);

    useEffect(() => {
        if (!selRoute) return;
        api.getPredictedVsActual(selRoute, 14).then(setPvData).catch(() => { });
    }, [selRoute]);

    if (loading) return (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9aafc4', fontSize: 13 }}>
            ⏳ Training hybrid models…
        </div>
    );

    const mapeColor = (m) => m < 10 ? '#00a86b' : m < 14 ? '#e88c00' : '#e53935';

    return (
        <div style={{ flex: 1, overflowY: 'auto' }}>
            {/* Summary row */}
            <div style={{ padding: '14px 16px' }}>
                <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
                    <MiniCard label="Avg MAPE (all routes)" value={`${summary?.avg_mape ?? '…'}%`}
                        color={mapeColor(summary?.avg_mape ?? 12)} icon="🎯" />
                    <MiniCard label="Best Route MAPE" value={`${summary?.best_mape ?? '…'}%`} color="#00a86b" icon="⭐" />
                    <MiniCard label="Model Method" value={summary?.method === 'prophet+xgboost' ? 'Hybrid' : 'Prophet'} unit="" color="#6c3acb" icon="🤖" />
                    <MiniCard label="Test Period" value={`${summary?.total_routes ?? 10}`} unit="routes" icon="🗺️" />
                </div>

                {/* Methodology badge */}
                <div style={{
                    padding: '10px 14px', borderRadius: 10,
                    background: 'linear-gradient(135deg, #e8f0fe, #f0ebff)',
                    border: '1px solid rgba(26,108,245,0.18)',
                    marginBottom: 16,
                }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: '#1a6cf5', marginBottom: 4 }}>
                        🤖 Hybrid Prophet + XGBoost Ensemble
                    </div>
                    <div style={{ fontSize: 11, color: '#4a5f80', lineHeight: 1.6 }}>
                        Prophet captures Pune's daily/weekly seasonality + event calendar. XGBoost corrects residuals
                        using rain intensity, lag features, and time-of-day interactions.
                        Trained on <strong>3 years real Open-Meteo Pune weather</strong> (2022–2024).
                    </div>
                </div>

                {/* Per-route MAPE table */}
                <div style={{ fontWeight: 700, fontSize: 11, color: '#0d1b3e', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                    Per-Route Accuracy
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {perRoute.map(r => (
                        <button key={r.route_id} onClick={() => setSelRoute(r.route_id)}
                            style={{
                                display: 'flex', alignItems: 'center', gap: 10,
                                padding: '10px 12px', borderRadius: 9,
                                background: selRoute === r.route_id ? '#e8f0fe' : '#f8fafc',
                                border: `1px solid ${selRoute === r.route_id ? 'rgba(26,108,245,0.30)' : 'rgba(15,40,90,0.09)'}`,
                                cursor: 'pointer', textAlign: 'left',
                            }}>
                            <div style={{ flex: 1 }}>
                                <div style={{ fontSize: 12, fontWeight: 700, color: '#0d1b3e' }}>{r.route_name}</div>
                                <div style={{ fontSize: 10, color: '#9aafc4', marginTop: 2 }}>Method: {r.method}</div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                                <div style={{ fontSize: 18, fontWeight: 800, color: mapeColor(r.mape), fontFamily: 'JetBrains Mono,monospace' }}>
                                    {r.mape}%
                                </div>
                                <div style={{ fontSize: 9, color: '#9aafc4' }}>MAPE</div>
                            </div>
                        </button>
                    ))}
                </div>

                {/* Predicted vs Actual chart */}
                {pvData.length > 0 && (
                    <div style={{ marginTop: 20 }}>
                        <div style={{ fontSize: 12, fontWeight: 700, color: '#0d1b3e', marginBottom: 12 }}>
                            📈 Predicted vs Actual — {selRoute} (last 14 days)
                        </div>
                        <ResponsiveContainer width="100%" height={200}>
                            <AreaChart data={pvData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                                <defs>
                                    <linearGradient id="gActual" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#1a6cf5" stopOpacity={0.2} />
                                        <stop offset="95%" stopColor="#1a6cf5" stopOpacity={0} />
                                    </linearGradient>
                                    <linearGradient id="gPred" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#00a86b" stopOpacity={0.2} />
                                        <stop offset="95%" stopColor="#00a86b" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#9aafc4' }} tickLine={false}
                                    interval={Math.floor(pvData.length / 6)} />
                                <YAxis tick={{ fontSize: 9, fill: '#9aafc4' }} tickLine={false} axisLine={false} />
                                <Tooltip contentStyle={{ background: '#fff', border: '1px solid rgba(15,40,90,0.12)', borderRadius: 8, fontSize: 11 }}
                                    labelStyle={{ color: '#4a5f80' }} />
                                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 8 }} />
                                <Area type="monotone" dataKey="actual" name="Actual" stroke="#1a6cf5"
                                    fill="url(#gActual)" strokeWidth={2} dot={false} />
                                <Area type="monotone" dataKey="predicted" name="Predicted" stroke="#00a86b"
                                    fill="url(#gPred)" strokeWidth={2} dot={false} strokeDasharray="4 2" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                )}
            </div>
        </div>
    );
}

/* ─────────────────────────────────────────────────────────────────────────
   PANEL 2 — SDG Impact
───────────────────────────────────────────────────────────────────────── */
function SDGPanel() {
    const [impact, setImpact] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            try { const d = await api.getSdgImpact(); setImpact(d); }
            catch { }
            finally { setLoading(false); }
        };
        load(); const iv = setInterval(load, 30000); return () => clearInterval(iv);
    }, []);

    if (loading || !impact) return (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9aafc4', fontSize: 13 }}>
            ⏳ Calculating SDG impact…
        </div>
    );

    const sdgs = [
        {
            num: 11, label: 'Sustainable Cities', color: '#f4a020', icon: '🏙️',
            metrics: [
                { v: `${impact.sdg11.co2_saved_kg_today.toLocaleString()} kg`, l: 'CO₂ Saved Today' },
                { v: `${impact.sdg11.on_time_percentage}%`, l: 'On-Time Buses' },
                { v: `${impact.sdg11.wait_time_reduction_pct}%`, l: 'Wait Time Reduction' },
                { v: impact.sdg11.daily_riders_served.toLocaleString(), l: 'Daily Riders Served' },
            ],
        },
        {
            num: 7, label: 'Affordable Clean Energy', color: '#fcc30b', icon: '⚡',
            metrics: [
                { v: `${impact.sdg7.fuel_saved_litres_today}L`, l: 'Fuel Saved Today' },
                { v: `₹${impact.sdg7.cost_saved_inr_today.toLocaleString()}`, l: 'Cost Saved' },
                { v: `${impact.sdg7.fuel_efficiency_improvement_pct}%`, l: 'Efficiency Gain' },
                { v: impact.sdg7.active_buses, l: 'Active Buses' },
            ],
        },
        {
            num: 9, label: 'Innovation & Infrastructure', color: '#fd6925', icon: '🔧',
            metrics: [
                { v: impact.sdg9.routes_optimised, l: 'Routes Optimised' },
                { v: impact.sdg9.recommendations_generated, l: 'AI Recommendations' },
                { v: `${impact.sdg9.avg_prediction_accuracy_pct}%`, l: 'Model Accuracy' },
                { v: impact.sdg9.anomalies_detected, l: 'Anomalies Detected' },
            ],
        },
        {
            num: 13, label: 'Climate Action', color: '#3f7e44', icon: '🌍',
            metrics: [
                { v: impact.sdg13.cars_off_road_equivalent_today.toLocaleString(), l: 'Cars Off Road Equiv.' },
                { v: `${impact.sdg13.co2_intensity_gcm_per_pkm}g`, l: 'CO₂/passenger-km' },
                { v: `${impact.sdg13.annual_co2_reduction_tonnes}t`, l: 'Annual CO₂ Savings' },
            ],
        },
    ];

    return (
        <div style={{ flex: 1, overflowY: 'auto' }}>
            <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 14 }}>
                {sdgs.map(sdg => (
                    <div key={sdg.num} style={{
                        borderRadius: 12, overflow: 'hidden',
                        border: '1px solid rgba(15,40,90,0.10)',
                        boxShadow: '0 2px 10px rgba(15,40,90,0.06)',
                    }}>
                        <div style={{
                            padding: '10px 14px',
                            background: `${sdg.color}15`,
                            borderBottom: `1px solid ${sdg.color}30`,
                            display: 'flex', alignItems: 'center', gap: 10,
                        }}>
                            <span style={{ fontSize: 22 }}>{sdg.icon}</span>
                            <div>
                                <div style={{ fontSize: 11, fontWeight: 700, color: sdg.color, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                                    SDG {sdg.num}
                                </div>
                                <div style={{ fontSize: 13, fontWeight: 700, color: '#0d1b3e' }}>{sdg.label}</div>
                            </div>
                        </div>
                        <div style={{
                            background: '#fff', padding: '12px 14px',
                            display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10,
                        }}>
                            {sdg.metrics.map(m => (
                                <div key={m.l}>
                                    <div style={{ fontSize: 17, fontWeight: 800, color: sdg.color, fontFamily: 'JetBrains Mono,monospace' }}>{m.v}</div>
                                    <div style={{ fontSize: 10, color: '#9aafc4', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{m.l}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
                <div style={{ textAlign: 'center', fontSize: 10, color: '#c0ccdf', paddingBottom: 4 }}>
                    Updated {new Date(impact.timestamp).toLocaleTimeString('en-IN')}
                </div>
            </div>
        </div>
    );
}

/* ─────────────────────────────────────────────────────────────────────────
   Main Export — tabbed panel for accuracy + SDG
───────────────────────────────────────────────────────────────────────── */
export default function InsightsSidebar() {
    const [tab, setTab] = useState('accuracy');

    return (
        <div style={{
            display: 'flex', flexDirection: 'column', height: '100%',
            background: '#f8fafc', overflow: 'hidden',
            borderLeft: '1px solid rgba(15,40,90,0.10)',
        }}>
            <SectionHead badge="Round 2 Features">ML Insights & Impact</SectionHead>

            {/* Tab switcher */}
            <div style={{ padding: '8px', borderBottom: '1px solid rgba(15,40,90,0.08)', flexShrink: 0 }}>
                <div className="tab-nav">
                    <button className={`tab-btn ${tab === 'accuracy' ? 'active' : ''}`} onClick={() => setTab('accuracy')}>
                        🎯 Model Accuracy
                    </button>
                    <button className={`tab-btn ${tab === 'sdg' ? 'active' : ''}`} onClick={() => setTab('sdg')}>
                        🌱 SDG Impact
                    </button>
                </div>
            </div>

            {tab === 'accuracy' ? <AccuracyPanel /> : <SDGPanel />}
        </div>
    );
}
