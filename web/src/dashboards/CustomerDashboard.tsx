import { ArrowRight, BadgeIndianRupee, Box, FileText, Gift, HeartHandshake, Package, RotateCcw, ShieldCheck, ShoppingBag } from "lucide-react";

function Stat({icon,title,value,tone}:any){return <div className="stat-card"><div className={`stat-icon ${tone}`}>{icon}</div><div><span>{title}</span><strong>{value}</strong></div></div>}
export default function CustomerDashboard(){
 return <section className="dashboard">
  <div className="welcome-row"><div><h1>Welcome back, John! 👋</h1><p>Here's your account overview.</p></div></div>
  <div className="stats-grid four"><Stat icon={<ShoppingBag/>} title="Total Orders" value="24" tone="purple"/><Stat icon={<BadgeIndianRupee/>} title="Total Spent" value="₹1,24,560" tone="green"/><Stat icon={<BadgeIndianRupee/>} title="Paid Amount" value="₹1,10,000" tone="blue"/><Stat icon={<Gift/>} title="Refunds Received" value="₹14,560" tone="purple"/></div>
  <div className="panel-grid customer-grid">
   <div className="panel"><PanelHeader title="Recent Orders"/>{["ORD-2025-56421","ORD-2025-56420","ORD-2025-56419","ORD-2025-56418"].map((x,i)=><div className="order-row" key={x}><div><b>{x}</b><small>{["10 Aug 2025","05 Aug 2025","28 Jul 2025","21 Jul 2025"][i]}</small></div><strong>₹{["24,500","18,900","12,500","22,000"][i]}</strong><span className="status">Delivered</span></div>)}</div>
   <div className="panel"><PanelHeader title="Recent Invoices"/>{["INV-2025-98452","INV-2025-98451","INV-2025-98450","INV-2025-98449"].map((x,i)=><div className="order-row" key={x}><div><b>{x}</b><small>{["10 Aug 2025","05 Aug 2025","28 Jul 2025","21 Jul 2025"][i]}</small></div><strong>₹{["24,500","18,900","12,500","22,000"][i]}</strong><span className="status">Paid</span></div>)}</div>
   <div className="customer-stat"><Mini icon={<Package/>} title="My Products" value="12"/><Mini icon={<ShieldCheck/>} title="Active Warranty" value="8"/><Mini icon={<RotateCcw/>} title="My Returns" value="2"/><Mini icon={<ArrowRight/>} title="Product Transfers" value="3"/></div>
  </div>
 </section>
}
function PanelHeader({title}:{title:string}){return <div className="panel-header"><h3>{title}</h3><button>View All</button></div>}
function Mini({icon,title,value}:{icon:React.ReactNode,title:string,value:string}){return <div className="mini-card"><div className="mini-icon">{icon}</div><span>{title}</span><strong>{value}</strong></div>}