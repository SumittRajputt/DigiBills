import React, { useState } from "react";
import { Link } from "react-router-dom";

export default function RetailerLandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="retailer-landing-page min-h-screen">
      {/* NAV */}
      <header className="fixed top-0 inset-x-0 z-50 glass border-b border-indigo-100/70">
        <div className="max-w-[1320px] mx-auto px-5 md:px-8 h-[76px] flex items-center justify-between">
          <Link
            to="/retailer-landing"
            className="flex items-center gap-2.5 font-extrabold text-xl tracking-tight"
          >
            <span className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-secondary text-white grid place-items-center shadow-lg shadow-indigo-200">
              <span className="material-symbols-outlined">
                receipt_long
              </span>
            </span>
            DigiBills
          </Link>

          <nav className="hidden lg:flex items-center gap-7 text-sm font-semibold text-slate-600">
            <a href="#core" className="hover:text-primary">
              Platform
            </a>
            <a href="#why" className="hover:text-primary">
              Why DigiBills
            </a>
            <a href="#pricing" className="hover:text-primary">
              Pricing
            </a>
            <a href="#faq" className="hover:text-primary">
              FAQ
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <div className="login-menu hidden sm:block">
              <button
                type="button"
                className="text-sm font-semibold text-slate-700 inline-flex items-center gap-2 py-3"
              >
                Login <span className="text-xs">⌄</span>
              </button>

              <div className="login-menu-panel">
                <Link className="login-option" to="/login/retailer">
                  <div className="login-icon">🏪</div>
                  <div>
                    <div className="login-option-title">
                      Retailer Login
                    </div>
                    <div className="login-option-desc">
                      Manage your retail business
                    </div>
                  </div>
                  <span className="login-chevron">→</span>
                </Link>

                <Link className="login-option" to="/login/customer">
                  <div className="login-icon">👤</div>
                  <div>
                    <div className="login-option-title">
                      Customer Login
                    </div>
                    <div className="login-option-desc">
                      Access bills &amp; warranties
                    </div>
                  </div>
                  <span className="login-chevron">→</span>
                </Link>
              </div>
            </div>

            <Link
              to="/retailer-register"
              className="px-5 py-2.5 rounded-full bg-gradient-to-r from-primary to-secondary text-white text-sm font-bold shadow-lg shadow-indigo-200"
            >
              Get Started Free
            </Link>

            <button
              type="button"
              aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
              aria-expanded={mobileMenuOpen}
              onClick={() => setMobileMenuOpen((open) => !open)}
              className="lg:hidden w-10 h-10 rounded-xl bg-white border border-indigo-100 grid place-items-center"
            >
              <span className="material-symbols-outlined">
                {mobileMenuOpen ? "close" : "menu"}
              </span>
            </button>
          </div>
        </div>
      </header>

      {mobileMenuOpen && (
        <div className="lg:hidden fixed top-[76px] inset-x-0 z-40 bg-white border-b border-indigo-100 shadow-xl">
          <nav className="px-5 py-5 space-y-1 text-sm font-semibold">
            <a
              href="#core"
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-xl px-4 py-3 hover:bg-indigo-50"
            >
              Platform
            </a>

            <a
              href="#why"
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-xl px-4 py-3 hover:bg-indigo-50"
            >
              Why DigiBills
            </a>

            <a
              href="#pricing"
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-xl px-4 py-3 hover:bg-indigo-50"
            >
              Pricing
            </a>

            <a
              href="#faq"
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-xl px-4 py-3 hover:bg-indigo-50"
            >
              FAQ
            </a>

            <div className="border-t border-slate-100 my-3" />

            <Link
              to="/login/retailer"
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-xl px-4 py-3 hover:bg-indigo-50"
            >
              Retailer Login
            </Link>

            <Link
              to="/login/customer"
              onClick={() => setMobileMenuOpen(false)}
              className="block rounded-xl px-4 py-3 hover:bg-indigo-50"
            >
              Customer Login
            </Link>

            <Link
              to="/retailer-register"
              onClick={() => setMobileMenuOpen(false)}
              className="block mt-2 rounded-xl bg-gradient-to-r from-primary to-secondary px-4 py-3 text-center text-white font-bold"
            >
              Get Started Free
            </Link>
          </nav>
        </div>
      )}

      {/* HERO */}
      <main className="pt-[76px]">
        <section className="relative overflow-hidden gridbg">
          <div className="absolute -top-48 left-[22%] w-[620px] h-[520px] rounded-full bg-indigo-200/35 blur-3xl" />
          <div className="absolute top-40 right-[-180px] w-[500px] h-[420px] rounded-full bg-emerald-100/45 blur-3xl" />

          <div className="max-w-[1320px] mx-auto px-5 md:px-8 py-20 lg:py-28 relative grid lg:grid-cols-[.9fr_1.1fr] gap-12 items-center">
            <div className="fadeup">
              <span className="inline-flex items-center gap-2 px-3.5 py-2 rounded-full bg-white/85 border border-indigo-100 text-primary text-xs font-extrabold">
                <span className="material-symbols-outlined text-base">
                  auto_awesome
                </span>
                Complete Retail Management Platform
              </span>

              <h1 className="text-[48px] md:text-[62px] lg:text-[70px] font-extrabold tracking-[-.055em] leading-[1.01] mt-6">
                Everything Your Retail Business{" "}
                <span className="grad">Needs. In One Place.</span>
              </h1>

              <p className="text-lg md:text-xl text-slate-600 leading-8 mt-6 max-w-xl">
                Billing, inventory, customers, payments, digital warranties,
                employees and suppliers—all in one place, so you can spend
                less time managing and more time growing.
              </p>

              <Link
                to="/retailer-register"
                className="inline-flex mt-8 px-7 py-3.5 rounded-full bg-gradient-to-r from-primary to-secondary text-white font-bold shadow-xl shadow-indigo-200"
              >
                Get Started Free
              </Link>

              <div className="mt-7 flex flex-wrap gap-x-6 gap-y-2 text-sm font-semibold text-slate-500">
                <span>✓ Built for all types of retailers</span>
                <span>✓ Solo retailers to teams</span>
              </div>
            </div>

            {/* HERO PRODUCT PREVIEW */}
            <div className="relative min-h-[560px] flex items-center justify-center">
              <div className="absolute inset-4 rounded-[44px] bg-gradient-to-br from-indigo-100/70 via-white/30 to-emerald-50/80" />

              <div className="relative w-[94%] max-w-[690px] float">
                <div className="device bg-white rounded-[28px] border border-indigo-100 overflow-hidden">
                  <div className="h-14 px-5 border-b flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="w-8 h-8 rounded-lg bg-soft text-primary grid place-items-center">
                        <span className="material-symbols-outlined text-[19px]">
                          receipt_long
                        </span>
                      </span>
                      <b>DigiBills</b>
                      <span className="text-xs text-slate-400">
                        / Point of Sale
                      </span>
                    </div>

                    <span className="px-2.5 py-1 rounded-full bg-mint text-green text-[11px] font-extrabold">
                      Connected
                    </span>
                  </div>

                  <div className="retailer-hero-pos-grid p-5 grid grid-cols-[1fr_220px] gap-4 bg-slate-50/60">
                    <div>
                      <div className="flex gap-2 mb-4">
                        <div className="flex-1 h-10 rounded-xl bg-white border border-slate-200 px-3 flex items-center text-xs text-slate-400">
                          Search products or scan barcode
                        </div>

                        <div className="w-10 h-10 rounded-xl bg-primary text-white grid place-items-center">
                          <span className="material-symbols-outlined">
                            barcode_scanner
                          </span>
                        </div>
                      </div>

                      <div className="retailer-product-grid grid grid-cols-3 gap-3">
                        {[
                          ["smartphone", "Smartphone"],
                          ["headphones", "Headphones"],
                          ["laptop_mac", "Laptop"],
                          ["cable", "Charger"],
                          ["keyboard", "Keyboard"],
                          ["speaker", "Speaker"],
                        ].map(([icon, name]) => (
                          <div
                            key={name}
                            className="p-2.5 rounded-2xl bg-white border border-slate-100"
                          >
                            <div className="h-16 rounded-xl bg-gradient-to-br from-indigo-50 to-white grid place-items-center">
                              <span className="material-symbols-outlined text-primary">
                                {icon}
                              </span>
                            </div>
                            <div className="text-[11px] font-bold mt-2">
                              {name}
                            </div>
                            <div className="text-[11px] text-slate-500 mt-1">
                              Select
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="rounded-2xl bg-white border border-slate-100 p-4">
                      <div className="text-[11px] text-slate-400">
                        Current bill
                      </div>
                      <div className="font-extrabold mt-1">3 items</div>

                      <div className="space-y-3 my-5 text-xs">
                        <div className="flex justify-between gap-3">
                          <span>Wireless Headphones</span>
                          <b>₹2,999</b>
                        </div>
                        <div className="flex justify-between">
                          <span>Charger</span>
                          <b>₹799</b>
                        </div>
                        <div className="flex justify-between">
                          <span>Tax</span>
                          <b>Calculated</b>
                        </div>
                      </div>

                      <div className="border-t pt-3 flex justify-between font-extrabold">
                        <span>Total</span>
                        <span>₹3,798</span>
                      </div>

                      <button
                        type="button"
                        className="w-full mt-4 h-10 rounded-xl bg-primary text-white text-xs font-bold"
                      >
                        Collect Payment
                      </button>
                    </div>
                  </div>

                  <div className="px-5 py-3 border-t flex items-center justify-between text-[11px] text-slate-500">
                    <span>Inventory updates with the bill</span>
                    <span>Customer record ready</span>
                    <span>Warranty can be issued</span>
                  </div>
                </div>

                <div className="absolute -bottom-7 -left-4 md:-left-9 glass border border-white rounded-2xl shadow-xl p-4 w-48">
                  <div className="text-[11px] text-slate-400">
                    Inventory
                  </div>
                  <div className="font-extrabold mt-1">
                    Stock connected
                  </div>
                  <div className="text-[11px] text-green font-bold mt-1">
                    ● Updates from sales
                  </div>
                </div>

                <div className="absolute top-8 -right-4 md:-right-8 glass border border-white rounded-2xl shadow-xl p-4 w-52">
                  <div className="text-[11px] text-slate-400">
                    Customer Digital Pass
                  </div>
                  <div className="font-bold mt-1">
                    Purchase + Warranty
                  </div>
                  <div className="mt-3 h-1.5 rounded-full bg-indigo-100">
                    <div className="w-3/4 h-full rounded-full bg-primary" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* PRODUCT OVERVIEW */}
        <section id="core" className="py-24 bg-white">
          <div className="max-w-[1240px] mx-auto px-5 md:px-8">
            <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
              <div>
                <span className="text-primary text-xs font-extrabold tracking-[.18em]">
                  ONE PLATFORM
                </span>
                <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight mt-3">
                  One place to run the shop.
                </h2>
              </div>
              <p className="max-w-lg text-slate-600 leading-7">
                DigiBills connects the everyday pieces of retail into one business flow—so your data moves with the work.
              </p>
            </div>

            <div className="grid lg:grid-cols-12 gap-4 mt-12">
              <div className="lg:col-span-7 rounded-[28px] bg-soft p-6 md:p-8 border border-indigo-100 overflow-hidden">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="text-sm font-extrabold">Your retail workspace</div>
                    <p className="text-xs text-slate-500 mt-1">The information you need, together.</p>
                  </div>
                  <span className="w-10 h-10 rounded-xl bg-white text-primary grid place-items-center">
                    <span className="material-symbols-outlined">dashboard</span>
                  </span>
                </div>

                <div className="mt-7 grid grid-cols-2 md:grid-cols-3 gap-3">
                  {[
                    ["receipt_long", "Billing", "Sell & bill"],
                    ["inventory_2", "Inventory", "Track stock"],
                    ["group", "Customers", "Purchase history"],
                    ["verified_user", "Warranty", "Digital records"],
                    ["payments", "Payments", "Track & reconcile"],
                    ["monitoring", "Reports", "See performance"],
                  ].map(([icon, title, desc]) => (
                    <div key={title} className="bg-white rounded-2xl p-4 border border-white">
                      <span className="material-symbols-outlined text-primary">{icon}</span>
                      <div className="font-extrabold text-sm mt-4">{title}</div>
                      <div className="text-xs text-slate-500 mt-1">{desc}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="lg:col-span-5 rounded-[28px] bg-ink text-white p-7 md:p-8 relative overflow-hidden">
                <div className="absolute -right-20 -top-20 w-52 h-52 rounded-full bg-indigo-500/30 blur-3xl" />
                <div className="relative">
                  <span className="text-xs font-extrabold tracking-[.18em] text-indigo-200">
                    CONNECTED DATA
                  </span>
                  <h3 className="text-2xl md:text-3xl font-extrabold mt-4">
                    Do the work once. Use it everywhere.
                  </h3>

                  <div className="mt-8 space-y-3">
                    {[
                      ["inventory_2", "Stock", "sale changes inventory"],
                      ["person", "Customer", "purchase stays connected"],
                      ["verified_user", "Warranty", "eligible product gets a record"],
                      ["analytics", "Insights", "transactions inform reports"],
                    ].map(([icon, title, desc]) => (
                      <div key={title} className="flex gap-3 items-center p-3 rounded-2xl bg-white/10 border border-white/10">
                        <span className="w-9 h-9 rounded-xl bg-white/10 grid place-items-center">
                          <span className="material-symbols-outlined text-indigo-200">{icon}</span>
                        </span>
                        <div>
                          <b className="text-sm">{title}</b>
                          <div className="text-xs text-slate-300">{desc}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* PROBLEM / SOLUTION */}
        <section className="py-24 gridbg">
          <div className="max-w-[1120px] mx-auto px-5 md:px-8">
            <div className="text-center max-w-3xl mx-auto">
              <span className="text-primary text-xs font-extrabold tracking-[.18em]">
                FROM FRAGMENTED TO CONNECTED
              </span>
              <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight mt-3">
                Stop managing the shop in pieces.
              </h2>
              <p className="text-slate-600 mt-4 leading-7">
                Retail gets harder when billing, stock, customer records and business information live in different places. DigiBills brings the core workflow together.
              </p>
            </div>

            <div className="grid md:grid-cols-[1fr_auto_1fr] items-center gap-5 mt-12">
              <div className="bg-white rounded-[26px] border border-slate-200 p-7 shadow-sm">
                <div className="text-sm font-extrabold text-slate-500">The old way</div>
                <div className="mt-6 space-y-3 text-sm">
                  {[
                    "Bills in one place",
                    "Stock in another",
                    "Customer details somewhere else",
                    "Warranty records are hard to find",
                    "Reports need manual effort",
                  ].map((text) => (
                    <div key={text} className="flex gap-3 items-center p-3 rounded-xl bg-slate-50">
                      <span className="material-symbols-outlined text-slate-400 text-[18px]">close</span>
                      {text}
                    </div>
                  ))}
                </div>
              </div>

              <div className="w-12 h-12 rounded-full bg-primary text-white grid place-items-center shadow-lg">
                <span className="material-symbols-outlined">arrow_forward</span>
              </div>

              <div className="bg-white rounded-[26px] border border-indigo-100 p-7 shadow-card">
                <div className="text-sm font-extrabold text-primary">With DigiBills</div>
                <div className="mt-6 space-y-3 text-sm">
                  {[
                    "Billing connected to inventory",
                    "Customers connected to purchases",
                    "Digital warranty connected to the sale",
                    "Payments and records stay together",
                    "Reports built from your business activity",
                  ].map((text) => (
                    <div key={text} className="flex gap-3 items-center p-3 rounded-xl bg-soft">
                      <span className="material-symbols-outlined text-green text-[18px]">check_circle</span>
                      {text}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* RETAIL LOOP */}
        <section className="py-24 bg-white">
          <div className="max-w-[1240px] mx-auto px-5 md:px-8 text-center">
            <span className="text-primary text-xs font-extrabold tracking-[.18em]">
              THE RETAIL LOOP
            </span>
            <h2 className="text-4xl md:text-5xl font-extrabold mt-3">
              From purchase to insight, one connected flow.
            </h2>
            <p className="text-slate-600 max-w-2xl mx-auto mt-4">
              A simple operating rhythm for the everyday work behind a retail business.
            </p>

            <div className="mt-12 relative">
              <div className="hidden lg:block absolute left-[8%] right-[8%] top-11 h-px line" />
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 relative">
                {[
                  ["local_shipping", "Supplier", "Buy"],
                  ["inventory", "Inventory", "Stock"],
                  ["receipt_long", "Billing", "Sell"],
                  ["person", "Customer", "Remember"],
                  ["verified_user", "Warranty", "Protect"],
                  ["payments", "Payment", "Reconcile"],
                  ["monitoring", "Insights", "Understand"],
                ].map(([icon, title, desc], index) => (
                  <div
                    key={title}
                    className={`bg-white rounded-2xl p-4 border border-indigo-100 shadow-sm ${
                      index === 3 ? "ring-2 ring-primary/15" : ""
                    }`}
                  >
                    <div className="w-12 h-12 mx-auto rounded-2xl bg-soft text-primary grid place-items-center">
                      <span className="material-symbols-outlined">{icon}</span>
                    </div>
                    <div className="font-extrabold text-sm mt-3">{title}</div>
                    <div className="text-[11px] text-slate-500 mt-1">{desc}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* BILLING + INVENTORY */}
        <section id="billing" className="py-28 bg-soft">
          <div className="max-w-[1240px] mx-auto px-5 md:px-8">
            <div className="grid lg:grid-cols-2 gap-16 items-center">
              <div>
                <span className="text-primary text-xs font-extrabold tracking-[.18em]">
                  BILLING + INVENTORY
                </span>
                <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight mt-3">
                  Sell confidently because your stock stays in the picture.
                </h2>
                <p className="text-slate-600 leading-7 mt-5">
                  Billing and inventory are part of the same workflow. Create bills, keep product information organized, receive stock and understand what needs attention.
                </p>

                <div className="mt-8 grid sm:grid-cols-2 gap-3 text-sm font-semibold">
                  {[
                    "Product / SKU management",
                    "Stock in & stock out",
                    "Stock adjustments",
                    "Low-stock visibility",
                    "Purchase receiving",
                    "Inventory history",
                  ].map((text) => (
                    <div key={text} className="p-3.5 rounded-xl bg-white border border-indigo-100">
                      ✓ {text}
                    </div>
                  ))}
                </div>
              </div>

              <div className="relative">
                <div className="bg-white rounded-[30px] border border-indigo-100 p-5 shadow-card">
                  <div className="flex items-center justify-between pb-4 border-b">
                    <b>Inventory overview</b>
                    <span className="text-xs text-slate-400">Today</span>
                  </div>

                  <div className="grid grid-cols-3 gap-3 mt-5">
                    {[
                      ["Products", "SKUs", "inventory_2"],
                      ["Low Stock", "Attention", "warning"],
                      ["Receiving", "Purchases", "move_to_inbox"],
                    ].map(([label, value, icon]) => (
                      <div key={label} className="p-4 rounded-2xl bg-soft">
                        <div className="text-xs text-slate-500">{label}</div>
                        <div className="text-lg font-extrabold mt-1">{value}</div>
                        <span className="material-symbols-outlined text-primary text-xl mt-3">{icon}</span>
                      </div>
                    ))}
                  </div>

                  <div className="mt-5 rounded-2xl border p-4">
                    <div className="flex justify-between text-xs font-bold">
                      <span>Stock movement</span>
                      <span className="text-slate-400">Connected to sales</span>
                    </div>
                    <div className="mt-5 flex items-end gap-2 h-28">
                      {[42, 62, 48, 78, 58, 88, 72, 94, 66, 80].map((height, i) => (
                        <div
                          key={i}
                          className="flex-1 rounded-t-lg bg-gradient-to-t from-primary/30 to-indigo-100"
                          style={{ height: `${height}%` }}
                        />
                      ))}
                    </div>
                  </div>
                </div>

                <div className="absolute -bottom-8 -right-4 bg-white rounded-2xl p-4 shadow-xl border border-indigo-100 w-48">
                  <div className="text-xs text-slate-400">At the counter</div>
                  <div className="font-extrabold mt-1">Bill → stock update</div>
                  <div className="text-xs text-green mt-1">Connected workflow</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* WARRANTY */}
        <section id="warranty" className="py-28 bg-ink text-white overflow-hidden">
          <div className="max-w-[1240px] mx-auto px-5 md:px-8">
            <div className="grid lg:grid-cols-[.82fr_1.18fr] gap-16 items-center">
              <div>
                <span className="text-indigo-300 text-xs font-extrabold tracking-[.18em]">
                  THE DIFFERENTIATOR
                </span>
                <h2 className="text-4xl md:text-6xl font-extrabold tracking-tight mt-4">
                  Make warranty a digital part of the customer experience.
                </h2>
                <p className="text-slate-300 leading-7 mt-6">
                  DigiBills connects an eligible purchase with a digital warranty record, making warranty information easier to issue, access and keep with the customer.
                </p>

                <div className="mt-8 space-y-3">
                  {[
                    ["verified_user", "Digital warranty record", "A clear record linked to the purchase."],
                    ["qr_code_2", "Customer access", "Give customers a digital way to find warranty information."],
                    ["history", "Connected history", "Keep the purchase and warranty context together."],
                  ].map(([icon, title, desc]) => (
                    <div key={title} className="flex gap-4 p-4 rounded-2xl bg-white/8 border border-white/10">
                      <span className="w-11 h-11 rounded-xl bg-white/10 grid place-items-center">
                        <span className="material-symbols-outlined text-indigo-200">{icon}</span>
                      </span>
                      <div>
                        <b>{title}</b>
                        <p className="text-sm text-slate-400 mt-1">{desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="relative min-h-[530px] flex items-center justify-center">
                <div className="absolute w-[480px] h-[480px] rounded-full bg-indigo-500/10 blur-3xl" />

                <div className="relative w-[380px] bg-white text-ink rounded-[34px] p-5 shadow-2xl rotate-[-2deg]">
                  <div className="rounded-[25px] bg-gradient-to-br from-indigo-50 to-white p-6 border border-indigo-100">
                    <div className="flex justify-between items-center">
                      <div>
                        <div className="text-xs text-slate-400">DigiBills</div>
                        <div className="font-extrabold text-lg mt-1">Digital Warranty</div>
                      </div>
                      <span className="w-11 h-11 rounded-2xl bg-mint text-green grid place-items-center">
                        <span className="material-symbols-outlined">verified_user</span>
                      </span>
                    </div>

                    <div className="mt-8 p-4 rounded-2xl bg-white border">
                      <div className="text-xs text-slate-400">Customer</div>
                      <div className="font-bold mt-1">Purchase record</div>

                      <div className="grid grid-cols-2 gap-3 mt-5 text-xs">
                        <div>
                          <span className="text-slate-400">Product</span>
                          <b className="block mt-1">Eligible item</b>
                        </div>
                        <div>
                          <span className="text-slate-400">Status</span>
                          <b className="block mt-1 text-green">Active</b>
                        </div>
                      </div>
                    </div>

                    <div className="mt-5 p-4 rounded-2xl bg-ink text-white flex items-center gap-4">
                      <div className="w-14 h-14 bg-white rounded-xl grid place-items-center">
                        <span className="material-symbols-outlined text-ink text-3xl">qr_code_2</span>
                      </div>
                      <div>
                        <div className="text-xs text-slate-400">Digital access</div>
                        <b>Warranty record</b>
                        <div className="text-xs text-slate-400 mt-1">Linked to purchase</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="absolute bottom-6 left-2 md:left-0 bg-white/10 border border-white/15 backdrop-blur rounded-2xl p-4 w-52">
                  <div className="text-xs text-indigo-200">Retailer view</div>
                  <div className="font-bold mt-1">Warranty issued</div>
                  <div className="text-xs text-slate-400 mt-1">
                    Connected to the customer record
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* CUSTOMER EXPERIENCE */}
        <section id="customer" className="py-28 bg-white">
          <div className="max-w-[1240px] mx-auto px-5 md:px-8">
            <div className="grid lg:grid-cols-[1.1fr_.9fr] gap-16 items-center">
              <div className="order-2 lg:order-1">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-soft rounded-[28px] p-5 border border-indigo-100">
                    <div className="text-xs text-slate-500">Customer profile</div>

                    <div className="flex items-center gap-3 mt-5">
                      <div className="w-12 h-12 rounded-full bg-white grid place-items-center text-primary font-extrabold">
                        AK
                      </div>
                      <div>
                        <b>Customer</b>
                        <div className="text-xs text-slate-500">Purchase history</div>
                      </div>
                    </div>

                    <div className="mt-6 space-y-2">
                      {["Recent bill", "Warranty record", "Payment history"].map((text) => (
                        <div key={text} className="bg-white rounded-xl p-3 text-xs font-semibold flex justify-between">
                          <span>{text}</span>
                          <span className="material-symbols-outlined text-primary text-base">chevron_right</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-[28px] bg-ink text-white p-5 flex flex-col justify-between min-h-[300px]">
                    <div>
                      <span className="material-symbols-outlined text-indigo-200 text-3xl">
                        phone_iphone
                      </span>
                      <h3 className="font-extrabold text-xl mt-5">
                        A better post-sale record.
                      </h3>
                      <p className="text-sm text-slate-400 mt-3 leading-6">
                        Keep customer and purchase information connected instead of scattered across receipts and registers.
                      </p>
                    </div>
                    <div className="text-xs text-indigo-200">
                      Purchase → Customer → Warranty
                    </div>
                  </div>
                </div>
              </div>

              <div className="order-1 lg:order-2">
                <span className="text-primary text-xs font-extrabold tracking-[.18em]">
                  CUSTOMER EXPERIENCE
                </span>
                <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight mt-3">
                  Turn a bill into an ongoing customer record.
                </h2>
                <p className="text-slate-600 leading-7 mt-5">
                  Keep customer details and purchase history connected to the transactions that matter. Digital warranty can extend that relationship beyond the counter.
                </p>

                <div className="mt-8 space-y-3 text-sm font-semibold">
                  {[
                    "Customer profiles",
                    "Purchase history",
                    "Connected warranty records",
                    "Payment information linked to transactions",
                  ].map((text) => (
                    <div key={text} className="flex items-center gap-3">
                      <span className="w-7 h-7 rounded-full bg-mint text-green grid place-items-center">
                        <span className="material-symbols-outlined text-[17px]">check</span>
                      </span>
                      {text}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* BUSINESS MANAGEMENT */}
        <section id="team" className="py-28 bg-soft">
          <div className="max-w-[1240px] mx-auto px-5 md:px-8">
            <div className="max-w-3xl">
              <span className="text-primary text-xs font-extrabold tracking-[.18em]">
                BUSINESS MANAGEMENT
              </span>
              <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight mt-3">
                The business behind the counter matters too.
              </h2>
              <p className="text-slate-600 leading-7 mt-5">
                DigiBills helps you manage your people, suppliers and performance alongside everyday selling.
              </p>
            </div>

            <div className="grid lg:grid-cols-3 gap-5 mt-12">
              <div className="lg:col-span-2 bg-white rounded-[28px] p-7 border border-indigo-100 shadow-sm">
                <div className="flex justify-between">
                  <div>
                    <b>Employee performance</b>
                    <p className="text-xs text-slate-500 mt-1">
                      See retail sales and monthly performance.
                    </p>
                  </div>
                  <span className="w-10 h-10 rounded-xl bg-soft text-primary grid place-items-center">
                    <span className="material-symbols-outlined">leaderboard</span>
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-7">
                  {[
                    ["Retail Sales", "Track"],
                    ["Bills", "Monitor"],
                    ["DigiBills Sales", "Eligible"],
                    ["Rank", "Monthly"],
                  ].map(([label, value]) => (
                    <div key={label} className="p-4 rounded-2xl bg-soft">
                      <div className="text-xs text-slate-500">{label}</div>
                      <div className="font-extrabold text-lg mt-1">{value}</div>
                    </div>
                  ))}
                </div>

                <div className="mt-5 p-5 rounded-2xl bg-ink text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <div className="font-extrabold">DigiBills Incentives</div>
                    <div className="text-sm text-slate-400 mt-1">
                      20% on eligible DigiBills subscriptions, extended warranties and retailer referrals.
                    </div>
                  </div>
                  <span className="px-3 py-2 rounded-xl bg-white/10 text-indigo-200 text-xs font-bold">
                    20% eligible incentive
                  </span>
                </div>
              </div>

              <div className="bg-white rounded-[28px] p-7 border border-indigo-100">
                <span className="w-10 h-10 rounded-xl bg-soft text-primary grid place-items-center">
                  <span className="material-symbols-outlined">local_shipping</span>
                </span>
                <h3 className="font-extrabold text-xl mt-6">
                  Basic supplier management
                </h3>
                <p className="text-sm text-slate-500 leading-6 mt-3">
                  Keep supplier records, purchase activity, receiving and outstanding visibility organized.
                </p>

                <div className="mt-6 space-y-2 text-xs font-semibold">
                  {[
                    "Supplier master",
                    "Purchase records",
                    "Goods receiving",
                    "Outstanding visibility",
                  ].map((text) => (
                    <div key={text} className="p-3 rounded-xl bg-soft">
                      ✓ {text}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* PAYMENTS + REPORTS */}
        <section id="insights" className="py-24 bg-white">
          <div className="max-w-[1240px] mx-auto px-5 md:px-8">
            <div className="grid lg:grid-cols-[.8fr_1.2fr] gap-14 items-center">
              <div>
                <span className="text-primary text-xs font-extrabold tracking-[.18em]">
                  PAYMENTS + REPORTS
                </span>
                <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight mt-3">
                  Know what happened today—and what needs attention.
                </h2>
                <p className="text-slate-600 leading-7 mt-5">
                  Keep payment information connected to transactions and use basic reports to understand sales, inventory, customers and employee performance.
                </p>

                <div className="mt-7 flex flex-wrap gap-2">
                  {["UPI", "Cash", "Card", "Split Payment"].map((method) => (
                    <span key={method} className="px-4 py-2 rounded-full bg-soft text-sm font-bold">
                      {method}
                    </span>
                  ))}
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="rounded-[28px] bg-soft p-6 border border-indigo-100">
                  <div className="flex justify-between">
                    <b>Payments</b>
                    <span className="material-symbols-outlined text-primary">payments</span>
                  </div>

                  <div className="mt-7 space-y-3">
                    {["UPI", "Card", "Cash", "Split"].map((method) => (
                      <div key={method} className="bg-white rounded-2xl p-4 flex justify-between text-sm">
                        <span className="font-semibold">{method}</span>
                        <span className="text-slate-400">Recorded</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-[28px] bg-ink text-white p-6">
                  <div className="flex justify-between">
                    <b>Reports</b>
                    <span className="material-symbols-outlined text-indigo-200">monitoring</span>
                  </div>

                  <div className="mt-7 space-y-3">
                    {[
                      "Sales performance",
                      "Inventory view",
                      "Customer records",
                      "Employee sales",
                    ].map((text) => (
                      <div key={text} className="p-4 rounded-2xl bg-white/10 border border-white/10 text-sm font-semibold">
                        {text}
                        <span className="material-symbols-outlined float-right text-indigo-200 text-base">
                          arrow_forward
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* WHY DIGIBILLS */}
        <section id="why" className="py-28 gridbg">
          <div className="max-w-[1240px] mx-auto px-5 md:px-8">
            <div className="text-center">
              <span className="text-primary text-xs font-extrabold tracking-[.18em]">
                WHY DIGIBILLS
              </span>
              <h2 className="text-4xl md:text-5xl font-extrabold mt-3">
                Why retailers choose DigiBills.
              </h2>
              <p className="text-slate-600 max-w-2xl mx-auto mt-4">
                Built around the way a retail business actually moves.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mt-12">
              {[
                ["all_inclusive", "Everything in one place", "Run billing, inventory, customers, payments and business management from one platform."],
                ["devices", "Digital-first experience", "Give customers a modern digital record for purchases and eligible warranties."],
                ["sync", "Connected workflow", "Reduce repeated work by keeping key retail information connected."],
                ["trending_up", "Business visibility", "Understand sales, stock, payments and team performance more clearly."],
                ["groups", "Empower your team", "Give employees visibility into sales performance and eligible DigiBills incentives."],
                ["rocket_launch", "Built to grow", "Start with core retail tools and add planned capabilities over time."],
              ].map(([icon, title, desc]) => (
                <div key={title} className="bg-white rounded-[24px] p-6 border border-indigo-100 hover:-translate-y-1 transition">
                  <span className="w-11 h-11 rounded-xl bg-soft text-primary grid place-items-center">
                    <span className="material-symbols-outlined">{icon}</span>
                  </span>
                  <h3 className="font-extrabold text-lg mt-5">{title}</h3>
                  <p className="text-sm text-slate-500 leading-6 mt-2">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* COMING SOON */}
        <section id="coming" className="py-24 bg-white">
          <div className="max-w-[1100px] mx-auto px-5 md:px-8 text-center">
            <span className="px-3 py-1.5 rounded-full bg-mint text-green text-xs font-extrabold tracking-[.16em]">
              COMING SOON • NO EXTRA COST
            </span>
            <h2 className="text-4xl md:text-5xl font-extrabold mt-5">
              More capability as your business grows.
            </h2>
            <p className="text-slate-600 max-w-2xl mx-auto mt-4 leading-7">
              DigiBills will expand after launch without changing the core promise: one platform for your retail business.
            </p>

            <div className="grid md:grid-cols-3 gap-4 mt-10">
              {[
                ["storefront", "Multi-outlet Operations", "Manage more than one outlet as your business expands."],
                ["manage_accounts", "Advanced Employee Management", "Deeper team management capabilities over time."],
                ["local_shipping", "Advanced Supplier Management", "More powerful supplier workflows after launch."],
              ].map(([icon, title, desc]) => (
                <div key={title} className="p-7 rounded-[26px] bg-soft border border-indigo-100 text-left">
                  <span className="w-11 h-11 rounded-xl bg-white text-primary grid place-items-center">
                    <span className="material-symbols-outlined">{icon}</span>
                  </span>
                  <h3 className="font-extrabold mt-5">{title}</h3>
                  <p className="text-sm text-slate-500 mt-2 leading-6">{desc}</p>
                  <div className="text-xs font-bold text-green mt-6">
                    Planned • No extra cost
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* PRICING */}
        <section id="pricing" className="py-28 bg-soft">
          <div className="max-w-[1200px] mx-auto px-5 md:px-8">
            <div className="text-center max-w-3xl mx-auto">
              <span className="text-primary text-xs font-extrabold tracking-[.18em]">
                PRICING
              </span>
              <h2 className="text-4xl md:text-5xl font-extrabold mt-3">
                A plan that grows with your retail business.
              </h2>
              <p className="text-slate-600 mt-4">
                Choose the plan that fits your current needs. Exact pricing and limits can be configured from the DigiBills admin system.
              </p>

              <div className="inline-flex mt-6 p-1 bg-white rounded-full border border-indigo-100">
                <button
                  type="button"
                  className="px-5 py-2 rounded-full bg-primary text-white text-sm font-bold"
                >
                  Monthly
                </button>
                <button
                  type="button"
                  className="px-5 py-2 rounded-full text-sm font-bold"
                >
                  Yearly
                </button>
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-5 mt-12">
              {[
                ["For getting started", "Basic", "Core retail tools", false],
                ["For growing retailers", "Plus", "More capacity and features", true],
                ["For advanced needs", "Pro", "Highest available limits", false],
              ].map(([subtitle, plan, desc, popular]) => (
                <div
                  key={String(plan)}
                  className={`bg-white rounded-[28px] p-7 border ${
                    popular ? "border-primary shadow-card relative" : "border-indigo-100"
                  }`}
                >
                  {popular && (
                    <span className="absolute -top-3 right-6 px-3 py-1 rounded-full bg-primary text-white text-[10px] font-extrabold">
                      POPULAR
                    </span>
                  )}

                  <div className="text-sm text-slate-500">{subtitle}</div>
                  <h3 className="text-2xl font-extrabold mt-2">{plan}</h3>
                  <div className="mt-6 text-slate-400 text-sm font-semibold">
                    Pricing configured by DigiBills
                  </div>
                  <p className="text-sm text-slate-600 mt-4">{desc}</p>

                  <Link
                    to="/retailer-register"
                    className={`block text-center w-full mt-7 py-3 rounded-xl font-bold ${
                      popular ? "bg-primary text-white" : "bg-soft text-ink"
                    }`}
                  >
                    Get Started
                  </Link>
                </div>
              ))}
            </div>

            <div className="mt-7 bg-white rounded-[24px] border border-indigo-100 overflow-hidden">
              <details>
                <summary className="w-full p-5 flex justify-between items-center font-extrabold cursor-pointer">
                  <span>Compare plan features</span>
                  <span className="material-symbols-outlined">expand_more</span>
                </summary>

                <div className="border-t overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-soft">
                        <th className="text-left p-4">Feature</th>
                        <th className="p-4">Basic</th>
                        <th className="p-4">Plus</th>
                        <th className="p-4">Pro</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        "Billing & POS",
                        "Inventory",
                        "Customer Management",
                        "Digital Warranty",
                        "Payments & Reconciliation",
                        "Employee Management",
                        "Supplier Management",
                        "Reports / Analytics",
                      ].map((feature) => (
                        <tr key={feature} className="border-t">
                          <td className="p-4 font-semibold">{feature}</td>
                          <td className="p-4 text-center">✓</td>
                          <td className="p-4 text-center">✓</td>
                          <td className="p-4 text-center">✓</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section id="faq" className="py-28 bg-white">
          <div className="max-w-[900px] mx-auto px-5 md:px-8">
            <div className="text-center">
              <span className="text-primary text-xs font-extrabold tracking-[.18em]">
                FAQ
              </span>
              <h2 className="text-4xl md:text-5xl font-extrabold mt-3">
                Questions retailers ask.
              </h2>
            </div>

            <div className="mt-10 space-y-3">
              {[
                ["What is DigiBills?", "DigiBills is a complete retail management platform covering billing, inventory, customers, digital warranty, payments, employees, suppliers and reports."],
                ["Who is DigiBills for?", "DigiBills is designed for all types of retailers, from solo retailers to businesses with employees."],
                ["What makes Digital Warranty different?", "Digital Warranty is a core V1 capability that connects an eligible purchase with a digital warranty record for the customer."],
                ["How do employee incentives work?", "Eligible DigiBills subscriptions, extended warranties and retailer referrals can generate a 20% employee incentive, subject to the applicable DigiBills rules. A retailer referral means the employee refers a retailer who then signs up."],
                ["What is coming after launch?", "Multi-outlet Operations, Advanced Employee Management and Advanced Supplier Management are planned post-launch capabilities at no extra cost."],
                ["Can I start with a small retail business?", "Yes. DigiBills is designed for solo retailers as well as retailers who work with employees and grow over time."],
              ].map(([question, answer]) => (
                <details key={question} className="group p-5 rounded-2xl bg-soft border border-indigo-50">
                  <summary className="cursor-pointer list-none flex justify-between gap-4 items-center font-bold">
                    {question}
                    <span className="material-symbols-outlined group-open:rotate-180 transition">
                      expand_more
                    </span>
                  </summary>
                  <p className="text-sm text-slate-600 leading-6 mt-3">{answer}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section id="signup" className="py-24">
          <div className="max-w-[1180px] mx-auto px-5 md:px-8">
            <div className="relative overflow-hidden rounded-[38px] bg-gradient-to-br from-primary to-secondary text-white p-10 md:p-16 text-center shadow-2xl shadow-indigo-200">
              <div className="absolute -top-28 -left-20 w-72 h-72 rounded-full bg-white/10 blur-3xl" />
              <div className="absolute -bottom-32 -right-20 w-80 h-80 rounded-full bg-indigo-950/20 blur-3xl" />

              <div className="relative">
                <span className="text-indigo-100 text-xs font-extrabold tracking-[.18em]">
                  READY WHEN YOU ARE
                </span>
                <h2 className="text-4xl md:text-6xl font-extrabold tracking-tight mt-4">
                  Everything Your Retail Business Needs. In One Place.
                </h2>
                <p className="mt-5 text-indigo-100 text-lg">
                  Start managing your business with DigiBills.
                </p>

                <Link
                  to="/retailer-register"
                  className="inline-flex mt-8 px-7 py-3.5 rounded-full bg-white text-primary font-extrabold"
                >
                  Get Started Free
                </Link>

                <div className="mt-5 text-xs text-indigo-100">
                  Simple onboarding: create your account + add your basic business details.
                </div>
              </div>
            </div>
          </div>
        </section>


      </main>

      {/* FOOTER */}
      <footer id="footer" className="bg-ink text-white">
        <div className="max-w-[1240px] mx-auto px-5 md:px-8 py-14">
          <div className="flex flex-col md:flex-row justify-between gap-10">
            <div>
              <div className="flex items-center gap-2 font-extrabold text-xl">
                <span className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary to-secondary grid place-items-center">
                  <span className="material-symbols-outlined">receipt_long</span>
                </span>
                DigiBills
              </div>
              <p className="text-slate-400 text-sm mt-3 max-w-xs">
                Complete retail management, made simple.
              </p>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-x-12 gap-y-3 text-sm text-slate-300">
              <a href="#core">Platform</a>
              <a href="#why">Why DigiBills</a>
              <a href="#pricing">Pricing</a>
              <a href="#warranty">Digital Warranty</a>
              <a href="#faq">FAQ</a>
              <Link to="/login/retailer">Login</Link>
            </div>
          </div>

          <div className="mt-12 pt-6 border-t border-white/10 text-xs text-slate-500">
            © 2026 DigiBills. Product capabilities shown are representative of the V1 scope.
          </div>
        </div>
      </footer>
    </div>
  );
}
