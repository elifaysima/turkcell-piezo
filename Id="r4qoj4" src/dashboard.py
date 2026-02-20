from __future__ import annotations
"""
Dashboard:
- MQTT'den StepPacket alır
- health + fusion + anomaly çalıştırır
- Dash/Plotly ile canlı grafik + alarm listesi basar

ÇALIŞTIRMA (Windows/Anaconda Prompt):
  python src/dashboard.py

Gerekenler:
- Mosquitto açık (1883)
- requirements kurulmuş
"""

import threading
import time
from collections import deque, defaultdict

import paho.mqtt.client as mqtt
from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import plotly.graph_objects as go

from common import decode_packet
from anomaly import detect
from fusion import ingest, fuse_ready
from health import health_alerts_for_packet, check_offline, check_outliers, HealthThresholds

MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883
TOPIC = "piyon/v1/steps"

FLOW_BUF = defaultdict(lambda: deque(maxlen=600)) # site_id -> (ts, flow, ratio, n_used)
ALERT_BUF = deque(maxlen=300) # list of dict
MODULE_LAST = {} # (site, mod) -> last dict

HEALTH_THR = HealthThresholds()


def mqtt_worker():
    def on_message(client, userdata, msg):
        try:
            pkt = decode_packet(msg.payload.decode("utf-8"))

            MODULE_LAST[(pkt.site_id, pkt.module_id)] = {
                "ts": pkt.ts,
                "steps1": pkt.steps_dir1,
                "steps2": pkt.steps_dir2,
                "vcap": pkt.vcap,
            }

            # packet-level health checks (stuck vs)
            for a in health_alerts_for_packet(pkt, HEALTH_THR):
                a["ts"] = pkt.ts
                ALERT_BUF.appendleft(a)

            ingest(pkt)

            # fuse any ready buckets
            for (site_id, ts, flow, ratio, n_used) in fuse_ready(now_ts=int(time.time())):
                FLOW_BUF[site_id].append((ts, flow, ratio, n_used))

                # anomaly expects steps1/steps2, we reconstruct from fused flow+ratio
                s1 = int(round(flow * ratio))
                s2 = int(round(flow * (1.0 - ratio)))

                alerts, dbg = detect(site_id, s1, s2, 1, ts)
                for a in alerts:
                    a["ts"] = ts
                    a["site_id"] = site_id
                    a["n_used"] = n_used
                    ALERT_BUF.appendleft(a)

        except Exception as e:
            ALERT_BUF.appendleft({"type": "BAD_MSG", "error": str(e), "ts": int(time.time())})

    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.subscribe(TOPIC)
    client.loop_forever()


def periodic_health_checks():
    while True:
        now_ts = int(time.time())

        # offline check
        for a in check_offline(now_ts, HEALTH_THR):
            a["ts"] = now_ts
            ALERT_BUF.appendleft(a)

        # outlier check per site
        sites = {s for (s, _) in MODULE_LAST.keys()}
        for s in sites:
            for a in check_outliers(s, HEALTH_THR):
                a["ts"] = now_ts
                ALERT_BUF.appendleft(a)

        time.sleep(3)


app = Dash(__name__)
app.layout = html.Div(
    [
        html.H2("PİYON — Canlı Yoğunluk & Anomali Dashboard"),
        html.Div(
            [
                dcc.Dropdown(id="site-select", options=[], value=None, placeholder="Site seç"),
            ],
            style={"width": "420px"},
        ),
        dcc.Graph(id="flow-graph"),
        dcc.Interval(id="tick", interval=1000, n_intervals=0),
        html.H4("Son Alarmlar"),
        html.Div(id="alerts"),
        html.H4("Modül Durumu (son paket)"),
        html.Div(id="modules"),
    ],
    style={"fontFamily": "Arial", "margin": "18px"},
)


@app.callback(
    Output("site-select", "options"),
    Output("site-select", "value"),
    Input("tick", "n_intervals"),
    Input("site-select", "value"),
)
def refresh_sites(_, current):
    sites = sorted(FLOW_BUF.keys())
    opts = [{"label": s, "value": s} for s in sites]
    if current in sites:
        return opts, current
    return opts, (sites[0] if sites else None)


@app.callback(
    Output("flow-graph", "figure"),
    Output("alerts", "children"),
    Output("modules", "children"),
    Input("tick", "n_intervals"),
    Input("site-select", "value"),
)
def refresh_ui(_, site_id):
    fig = go.Figure()

    # graph
    if site_id and site_id in FLOW_BUF and len(FLOW_BUF[site_id]) > 0:
        data = list(FLOW_BUF[site_id])
        ts = [x[0] for x in data]
        flow = [x[1] for x in data]
        ratio = [x[2] for x in data]

        fig.add_trace(go.Scatter(x=ts, y=flow, mode="lines+markers", name="Flow (fused)"))
        fig.add_trace(go.Scatter(x=ts, y=ratio, mode="lines", name="Dir1 Ratio", yaxis="y2"))
        fig.update_layout(
            title=f"Site: {site_id}",
            xaxis_title="Unix Time (s)",
            yaxis_title="Flow (steps/s proxy)",
            yaxis2=dict(title="Dir1 Ratio", overlaying="y", side="right", range=[0, 1]),
            height=420,
        )
    else:
        fig.update_layout(title="Veri bekleniyor...", height=420)

    # alerts list
    alert_items = []
    for a in list(ALERT_BUF)[:12]:
        alert_items.append(html.Div(str(a), style={"borderBottom": "1px solid #ddd", "padding": "6px 0"}))

    # module status list
    mod_items = []
    items = [(k, v) for k, v in MODULE_LAST.items() if (site_id is None or k[0] == site_id)]
    items = sorted(items, key=lambda kv: (kv[0][0], kv[0][1]))
    for (s, m), v in items[:25]:
        mod_items.append(
            html.Div(
                f"{s}/{m} ts={v['ts']} s1={v['steps1']} s2={v['steps2']} vcap={v.get('vcap')}",
                style={"borderBottom": "1px solid #eee", "padding": "4px 0"},
            )
        )

    return fig, alert_items, mod_items


def main():
    threading.Thread(target=mqtt_worker, daemon=True).start()
    threading.Thread(target=periodic_health_checks, daemon=True).start()
    app.run_server(debug=False)


if __name__ == "__main__":
    main()
