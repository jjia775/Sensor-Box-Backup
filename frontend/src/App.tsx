import { useEffect, useMemo, useRef, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

type LiveMsg = {
  topic: "reading.new";
  data: { id: number; sensor_id: string; ts: string; value: number; attributes?: any };
};

export default function App() {
  const [sensorId, setSensorId] = useState<string>("");
  const [points, setPoints] = useState<{ ts: number; value: number }[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const url = `ws://localhost:8000/ws/live`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onmessage = (ev) => {
      const msg: LiveMsg = JSON.parse(ev.data);
      if (msg.topic === "reading.new") {
        if (sensorId && msg.data.sensor_id !== sensorId) return;
        setPoints((prev) => {
          const next = [...prev, { ts: new Date(msg.data.ts).getTime(), value: msg.data.value }];
          // keep last 300 points
          return next.slice(-300);
        });
      }
    };

    return () => ws.close();
  }, [sensorId]);

  const data = useMemo(
    () => points.map(p => ({ time: new Date(p.ts).toLocaleTimeString(), value: p.value })),
    [points]
  );

  return (
    <div style={{ padding: 24, fontFamily: "system-ui, Segoe UI, Roboto, Helvetica, Arial" }}>
      <h2>Realtime Sensor Dashboard</h2>

      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 16 }}>
        <label>Filter by Sensor ID</label>
        <input placeholder="(optional) e.g. 7e3c-..." value={sensorId} onChange={e=>setSensorId(e.target.value)} />
        <span style={{ opacity: 0.7 }}>Showing {data.length} points</span>
      </div>

      <LineChart width={900} height={360} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" minTickGap={24} />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="value" dot={false} />
      </LineChart>
    </div>
  );
}
