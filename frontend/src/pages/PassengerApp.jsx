import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import api from '../api.js';
import 'leaflet/dist/leaflet.css';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl: null, iconUrl: null, shadowUrl: null });

const STOPS_LIST = [
    'Shivajinagar Bus Stand', 'Hinjewadi Phase 1', 'Hinjewadi Phase 2', 'Hinjewadi Phase 3',
    'Baner Road', 'Balewadi Stadium', 'Aundh', 'Kothrud Depot', 'Deccan Gymkhana',
    'FC Road', 'Swargate', 'Hadapsar', 'Magarpatta City', 'Katraj', 'Warje',
    'Pune Railway Station', 'Nigdi', 'Pimpri', 'Akurdi', 'Chinchwad',
    'Viman Nagar', 'Kharadi IT Park', 'Koregaon Park', 'Kalyani Nagar',
    'Yerwada', 'Ramwadi (Metro)', 'Civil Court', 'PCMC Bus Stand', 'Wakad',
];

function CrowdIndicator({ pct }) {
    const color = pct > 80 ? '#e53935' : pct > 60 ? '#e88c00' : '#00a86b';
    const bg = pct > 80 ? '#fdecea' : pct > 60 ? '#fff7e0' : '#e2f9ef';
    const label = pct > 80 ? 'Crowded' : pct > 60 ? 'Moderate' : 'Light';
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div className="crowd-bar" style={{ width: 80 }}>
                <div className="crowd-fill" style={{ width: `${pct}%`, background: color }} />
            </div>
            <span style={{
                fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 99,
                background: bg, color,
            }}>{label} {pct}%</span>
        </div>
    );
}

function ETACard({ dep }) {
    return (
        <div style={{
            display: 'flex', alignItems: 'center', gap: 12,
            padding: '9px 12px',
            background: '#f8fafc', border: '1px solid rgba(15,40,90,0.10)',
            borderRadius: 10, marginBottom: 7,
        }}>
            <div style={{
                width: 46, height: 46, borderRadius: 10, flexShrink: 0,
                background: '#e8f0fe', border: '1px solid rgba(26,108,245,0.20)',
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            }}>
                <span style={{ fontSize: 18, fontWeight: 900, color: '#1a6cf5', fontFamily: 'JetBrains Mono,monospace', lineHeight: 1 }}>
                    {dep.in_min}
                </span>
                <span style={{ fontSize: 9, color: '#9aafc4', textTransform: 'uppercase' }}>min</span>
            </div>
            <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#0d1b3e', marginBottom: 5 }}>
                    Departs in {dep.in_min} min
                </div>
                <CrowdIndicator pct={dep.crowd === 'low' ? 28 : dep.crowd === 'medium' ? 56 : 85} />
            </div>
        </div>
    );
}

function JourneyStep({ step, isLast }) {
    const modeColor = step.mode === 'bus' ? '#1a6cf5' : step.mode === 'walk' ? '#00a86b' : '#6c3acb';
    const modeBg = step.mode === 'bus' ? '#e8f0fe' : step.mode === 'walk' ? '#e2f9ef' : '#f0ebff';
    return (
        <div style={{ display: 'flex', gap: 14, position: 'relative', marginBottom: 4 }}>
            {!isLast && (
                <div style={{
                    position: 'absolute', left: 20, top: 44, bottom: -4, width: 2,
                    background: 'linear-gradient(180deg, rgba(15,40,90,0.15), rgba(15,40,90,0.02))',
                }} />
            )}
            <div style={{
                width: 40, height: 40, borderRadius: '50%', flexShrink: 0,
                background: modeBg, border: `2px solid ${modeColor}44`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 18, zIndex: 1,
            }}>
                {step.mode === 'bus' ? '🚌' : step.mode === 'walk' ? '🚶' : step.mode === 'metro' ? '🚇' : '🚲'}
            </div>
            <div style={{ flex: 1, paddingBottom: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8, marginBottom: 4 }}>
                    <div>
                        <div style={{ fontSize: 13, fontWeight: 700, color: '#0d1b3e' }}>{step.description}</div>
                        {step.route && <div style={{ fontSize: 11, color: modeColor, fontWeight: 600, marginTop: 2 }}>{step.route}</div>}
                    </div>
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#4a5f80', fontFamily: 'JetBrains Mono,monospace', flexShrink: 0 }}>
                        {(step.wait_min || 0) + step.duration_min}m
                    </span>
                </div>
                {step.mode === 'bus' && step.next_departures && (
                    <div style={{ marginTop: 6 }}>
                        <div style={{ fontSize: 10, color: '#9aafc4', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>
                            Next Departures
                        </div>
                        {step.next_departures.map((d, i) => <ETACard key={i} dep={d} />)}
                        {step.crowd_pct && (
                            <div style={{ marginTop: 8 }}>
                                <div style={{ fontSize: 10, color: '#9aafc4', marginBottom: 5, fontWeight: 600 }}>Current Load</div>
                                <CrowdIndicator pct={step.crowd_pct} />
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

function StopAutocomplete({ value, onChange, onSelect, placeholder }) {
    const [open, setOpen] = useState(false);
    const filtered = STOPS_LIST.filter(s => s.toLowerCase().includes(value.toLowerCase()) && s !== value).slice(0, 6);
    return (
        <div style={{ position: 'relative', flex: 1 }}>
            <input
                value={value}
                onChange={e => { onChange(e.target.value); setOpen(true); }}
                onFocus={() => setOpen(true)}
                placeholder={placeholder}
                style={{
                    width: '100%', padding: '10px 14px', borderRadius: 8,
                    background: '#f4f7fc', color: '#0d1b3e',
                    border: '1px solid rgba(15,40,90,0.14)', fontSize: 13,
                    outline: 'none', transition: 'border-color 0.18s',
                }}
                onFocusCapture={e => e.target.style.borderColor = 'rgba(26,108,245,0.40)'}
                onBlurCapture={e => { e.target.style.borderColor = 'rgba(15,40,90,0.14)'; setTimeout(() => setOpen(false), 200); }}
            />
            {open && filtered.length > 0 && (
                <div style={{
                    position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 9999,
                    background: '#ffffff', border: '1px solid rgba(26,108,245,0.25)',
                    borderRadius: 10, overflow: 'hidden', marginTop: 4,
                    boxShadow: '0 8px 24px rgba(15,40,90,0.15)',
                }}>
                    {filtered.map(s => (
                        <div key={s} onClick={() => { onSelect(s); setOpen(false); }}
                            style={{
                                padding: '10px 14px', cursor: 'pointer', fontSize: 13, color: '#4a5f80',
                                transition: 'background 0.12s', display: 'flex', gap: 8, alignItems: 'center'
                            }}
                            onMouseEnter={e => e.currentTarget.style.background = '#f0f4ff'}
                            onMouseLeave={e => e.currentTarget.style.background = ''}
                        >
                            <span style={{ color: '#1a6cf5' }}>📍</span> {s}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default function PassengerApp() {
    const [origin, setOrigin] = useState('Shivajinagar Bus Stand');
    const [destination, setDestination] = useState('Hinjewadi Phase 1');
    const [journey, setJourney] = useState(null);
    const [loading, setLoading] = useState(false);
    const [buses, setBuses] = useState([]);
    const [routes, setRoutes] = useState([]);

    const QUICK = [
        { from: 'Shivajinagar Bus Stand', to: 'Hinjewadi Phase 1' },
        { from: 'Kothrud Depot', to: 'Viman Nagar' },
        { from: 'Swargate', to: 'Hadapsar' },
    ];

    useEffect(() => {
        const load = async () => {
            try { const [b, r] = await Promise.all([api.getBuses(), api.getRoutes()]); setBuses(b); setRoutes(r); } catch { }
        };
        load(); const iv = setInterval(load, 15000); return () => clearInterval(iv);
    }, []);

    const planJourney = async (from, to) => {
        setLoading(true);
        try { const j = await api.planJourney(from, to); setJourney(j); } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const swap = () => { const t = origin; setOrigin(destination); setDestination(t); };
    const journeyPath = journey ? [[journey.origin.lat, journey.origin.lon], [journey.destination.lat, journey.destination.lon]] : null;

    return (
        <div style={{ display: 'flex', height: '100%', overflow: 'hidden', background: '#f0f4f9' }}>

            {/* LEFT: Planner */}
            <div style={{
                width: 390, flexShrink: 0,
                borderRight: '1px solid rgba(15,40,90,0.10)',
                background: '#ffffff',
                display: 'flex', flexDirection: 'column', overflow: 'hidden',
                boxShadow: '2px 0 8px rgba(15,40,90,0.06)',
            }}>
                {/* Search panel */}
                <div style={{ padding: '18px 16px', borderBottom: '1px solid rgba(15,40,90,0.09)', flexShrink: 0 }}>
                    <div style={{
                        fontSize: 11, fontWeight: 700, color: '#1a6cf5',
                        textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 14
                    }}>
                        Plan Your Journey
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8, position: 'relative' }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#00a86b', flexShrink: 0 }} />
                            <StopAutocomplete value={origin} onChange={setOrigin} onSelect={setOrigin} placeholder="From stop..." />
                        </div>
                        <button onClick={swap} style={{
                            position: 'absolute', right: 4, top: '50%', transform: 'translateY(-50%)',
                            width: 28, height: 28, borderRadius: '50%',
                            background: '#f0f4f9', border: '1px solid rgba(15,40,90,0.18)',
                            cursor: 'pointer', fontSize: 14, color: '#4a5f80',
                            display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10,
                        }}>⇅</button>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                            <div style={{ width: 10, height: 10, borderRadius: 3, background: '#1a6cf5', flexShrink: 0 }} />
                            <StopAutocomplete value={destination} onChange={setDestination} onSelect={setDestination} placeholder="To stop..." />
                        </div>
                    </div>

                    <button className="btn btn-primary" onClick={() => planJourney(origin, destination)}
                        disabled={loading} style={{ width: '100%', marginTop: 12, justifyContent: 'center', padding: '11px' }}>
                        {loading ? '⏳ Planning...' : '🚀 Find Best Route'}
                    </button>

                    {!journey && (
                        <div style={{ marginTop: 14 }}>
                            <div style={{ fontSize: 10, color: '#9aafc4', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                                Popular Routes
                            </div>
                            {QUICK.map((s, i) => (
                                <button key={i}
                                    onClick={() => { setOrigin(s.from); setDestination(s.to); planJourney(s.from, s.to); }}
                                    style={{
                                        width: '100%', padding: '9px 12px', marginBottom: 5, borderRadius: 8,
                                        background: '#f8fafc', border: '1px solid rgba(15,40,90,0.10)',
                                        cursor: 'pointer', textAlign: 'left', fontSize: 12, color: '#4a5f80',
                                        transition: 'all 0.15s', display: 'flex', alignItems: 'center', gap: 6,
                                    }}
                                    onMouseEnter={e => { e.currentTarget.style.borderColor = 'rgba(26,108,245,0.3)'; e.currentTarget.style.color = '#1a6cf5'; }}
                                    onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(15,40,90,0.10)'; e.currentTarget.style.color = '#4a5f80'; }}
                                >
                                    <span style={{ color: '#1a6cf5' }}>›</span> {s.from} → {s.to}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Journey result */}
                {journey && (
                    <div className="scroll-y" style={{ flex: 1 }}>
                        {/* Summary */}
                        <div style={{
                            padding: '16px',
                            background: 'linear-gradient(135deg, #1a6cf5, #0f4bb0)',
                            color: '#fff',
                        }}>
                            <div style={{ fontSize: 11, fontWeight: 600, opacity: 0.8, marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                                Journey Summary
                            </div>
                            <div style={{ display: 'flex', gap: 10, justifyContent: 'space-around' }}>
                                {[
                                    { v: `${journey.total_duration_min}m`, l: 'Duration', e: '⏱️' },
                                    { v: `${journey.total_distance_km}km`, l: 'Distance', e: '📏' },
                                    { v: `₹${journey.fare_inr}`, l: 'Fare', e: '🎫' },
                                    { v: `+${journey.time_saved_min}m`, l: 'vs Driving', e: '⚡' },
                                ].map(m => (
                                    <div key={m.l} style={{ textAlign: 'center' }}>
                                        <div style={{ fontSize: 16, marginBottom: 2 }}>{m.e}</div>
                                        <div style={{ fontSize: 15, fontWeight: 800, fontFamily: 'JetBrains Mono,monospace' }}>{m.v}</div>
                                        <div style={{ fontSize: 9, opacity: 0.75, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{m.l}</div>
                                    </div>
                                ))}
                            </div>
                            <div style={{
                                marginTop: 12, padding: '7px 12px', borderRadius: 8,
                                background: 'rgba(255,255,255,0.18)', fontSize: 11, display: 'flex', gap: 6, alignItems: 'center',
                            }}>
                                <span>🌱</span> Saving {journey.carbon_saved_g}g CO₂ vs driving
                            </div>
                        </div>

                        {/* Steps */}
                        <div style={{ padding: '18px 16px' }}>
                            <div style={{ fontSize: 10, color: '#9aafc4', textTransform: 'uppercase', letterSpacing: '0.1em', fontWeight: 700, marginBottom: 16 }}>
                                Step-by-step
                            </div>
                            {journey.steps.map((step, i) => (
                                <JourneyStep key={step.step} step={step} isLast={i === journey.steps.length - 1} />
                            ))}
                        </div>

                        <div style={{ padding: '0 16px 18px' }}>
                            <button className="btn btn-ghost" style={{ width: '100%', justifyContent: 'center' }}
                                onClick={() => setJourney(null)}>← Plan Another Journey</button>
                        </div>
                    </div>
                )}
            </div>

            {/* RIGHT: Map */}
            <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
                {/* Live badge */}
                <div style={{
                    position: 'absolute', top: 12, right: 16, zIndex: 500,
                    padding: '7px 14px', borderRadius: 99,
                    background: '#fff', border: '1px solid rgba(0,168,107,0.28)',
                    boxShadow: '0 2px 10px rgba(15,40,90,0.10)',
                    display: 'flex', gap: 6, alignItems: 'center',
                }}>
                    <span className="live-dot" />
                    <span style={{ fontSize: 11, color: '#00a86b', fontWeight: 700 }}>
                        {buses.length} Buses Live
                    </span>
                </div>

                {/* Journey origin/dest overlay */}
                {journey && (
                    <div style={{
                        position: 'absolute', top: 12, left: 16, zIndex: 500,
                        padding: '12px 16px', borderRadius: 12,
                        background: '#ffffff', border: '1px solid rgba(26,108,245,0.25)',
                        boxShadow: '0 2px 16px rgba(15,40,90,0.12)', maxWidth: 260,
                    }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: '#1a6cf5', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                            Journey Mapped
                        </div>
                        <div style={{ fontSize: 12, color: '#4a5f80', lineHeight: 1.7 }}>
                            <span style={{ color: '#00a86b', fontWeight: 700 }}>●</span> {journey.origin.name}<br />
                            <span style={{ color: '#9aafc4', fontSize: 11 }}>↓</span><br />
                            <span style={{ color: '#e53935', fontWeight: 700 }}>■</span> {journey.destination.name}
                        </div>
                        <div style={{ marginTop: 8, fontSize: 12, fontWeight: 700, color: '#1a6cf5' }}>
                            ⏱️ {journey.total_duration_min} min · ₹{journey.fare_inr}
                        </div>
                    </div>
                )}

                <MapContainer center={[18.5204, 73.8567]} zoom={12}
                    style={{ height: '100%', width: '100%' }} zoomControl={false}>
                    <TileLayer
                        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                        maxZoom={19}
                    />

                    {/* Route polylines */}
                    {routes.map(route => {
                        const coords = route.stop_coordinates?.map(s => [s.lat, s.lon]) || [];
                        return coords.length > 1 ? (
                            <Polyline key={route.route_id} positions={coords}
                                color={route.color} weight={2} opacity={0.5} />
                        ) : null;
                    })}

                    {/* Journey path highlight */}
                    {journeyPath && (
                        <Polyline positions={journeyPath} color="#1a6cf5" weight={5} opacity={0.85} />
                    )}

                    {/* Origin */}
                    {journey && (
                        <CircleMarker center={[journey.origin.lat, journey.origin.lon]}
                            radius={11} color="#00a86b" fillColor="#00a86b" fillOpacity={0.85} weight={3}>
                            <Popup><strong>{journey.origin.name}</strong><br />Your Origin</Popup>
                        </CircleMarker>
                    )}

                    {/* Destination */}
                    {journey && (
                        <CircleMarker center={[journey.destination.lat, journey.destination.lon]}
                            radius={11} color="#e53935" fillColor="#e53935" fillOpacity={0.85} weight={3}>
                            <Popup><strong>{journey.destination.name}</strong><br />Your Destination</Popup>
                        </CircleMarker>
                    )}

                    {/* Live buses */}
                    {buses.slice(0, 70).map(bus => {
                        const color = bus.status === 'breakdown' ? '#e53935' : bus.status === 'crowded' ? '#e88c00' : bus.status === 'delayed' ? '#fb6f00' : '#00a86b';
                        return (
                            <CircleMarker key={bus.bus_id} center={[bus.lat, bus.lon]}
                                radius={5} color={color} fillColor={color} fillOpacity={0.7} weight={2}>
                                <Popup>
                                    <div style={{ fontFamily: 'Inter,sans-serif', fontSize: 12, lineHeight: 1.6 }}>
                                        <strong>{bus.bus_id}</strong> — {bus.route_name}<br />
                                        Load: {bus.occupancy_pct}% · {bus.status}<br />
                                        Next: {bus.next_stop} in {bus.eta_next_stop_min}m
                                    </div>
                                </Popup>
                            </CircleMarker>
                        );
                    })}
                </MapContainer>
            </div>
        </div>
    );
}
