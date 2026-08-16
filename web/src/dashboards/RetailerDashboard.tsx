import { AlertTriangle, BarChart3, FileText, IndianRupee, Package, ShoppingCart, Users } from "lucide-react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const trend = [{d:"1 Aug",v:18},{d:"3 Aug",v:26},{d:"5 Aug",v:31},{d:"7 Aug",v:25},{d:"9 Aug",v:41},{d:"10 Aug",v:36},{d:"12 Aug",v:49}];

function Stat({icon,title,value,change,tone="green"}:any){return <div className="stat-card"><div className={`stat-icon ${tone}`}>{icon}</div><div><span>{title}</span><strong>{value}</strong><small className={change.startsWith("-")?"negative":"positive"}>{change} <em>vs last month</em></small></div></div>}
export default function RetailerDashboard(){
 return <section className="dashboard">
  <div className="welcome-row"><div><h1>Welcome back, TechZone Retail! 👋</h1><p>Here's your business overview.</p></div><button className="date-filter">12 May 2025 – 12 Aug 2025⌄</button></div>
  <div className="stats-grid four"><Stat icon={<IndianRupee/>} title="Today's Sales" value="₹48,650" change="+12.4%" /><Stat icon={<BarChart3/>} title="This Month Sales" value="₹12.48 L" change="+16.4%" /><Stat icon={<FileText/>} title="Total Invoices" value="321" change="+11.2%" tone="blue"/><Stat icon={<IndianRupee/>} title="Outstanding Amount" value="₹82,430" change="-4.3%" tone="orange"/></div>
  <div className="panel-grid retailer-grid">
   <div className="panel chart-panel"><PanelHeader title="Sales Trend"/><ResponsiveContainer width="100%" height={235}><AreaChart data={trend}><CartesianGrid strokeDasharray="3 3" vertical={false}/><XAxis dataKey="d"/><YAxis/><Tooltip/><Area type="monotone" dataKey="v" stroke="#11a36a" fill="#e8faf3" strokeWidth={3}/></AreaChart></ResponsiveContainer></div>
   <div className="panel"><PanelHeader title="Top Selling Products"/>{["iPhone 15 128GB","Samsung Galaxy S24","OnePlus 12","Sony WH-1000XM5","boAt Airdopes 141"].map((x,i)=><div className="product-rank" key={x}><span>{i+1}</span><b>{x}</b><strong>{[45,38,32,28,25][i]}</strong></div>)}</div>
   <div className="panel"><PanelHeader title="Low Stock Alerts"/>{["iPhone 15 128GB","AirPods Pro 2","Samsung S24 Ultra"].map((x,i)=><div className="alert-row" key={x}><AlertTriangle size={15}/><b>{x}</b><strong>Stock: {[5,3,4][i]}</strong></div>)}</div>
   <div className="panel"><PanelHeader title="Recent Invoices"/>{["INV-2025-98452","INV-2025-98451","INV-2025-98450"].map((x,i)=><div className="simple-row" key={x}><b>{x}</b><span>₹{["24,500","18,900","7,800"][i]}</span><small>10 Aug 2025</small></div>)}</div>
   <div className="panel"><PanelHeader title="Recent Payments"/>{["PAY-2025-78452","PAY-2025-78451","PAY-2025-78450"].map((x,i)=><div className="simple-row" key={x}><b>{x}</b><span>₹{["24,500","12,000","18,900"][i]}</span><small>10 Aug 2025</small></div>)}</div>
  </div>
 </section>
}
function PanelHeader({title}:{title:string}){return <div className="panel-header"><h3>{title}</h3><button>This Month⌄</button></div>}