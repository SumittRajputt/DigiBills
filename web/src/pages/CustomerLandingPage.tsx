import React from "react";
import { Link } from "react-router-dom";

export default function CustomerLandingPage() {
  return (
    <div className="customer-landing-page min-h-screen bg-white">
      {/* NAV */}
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-slate-200/80 glass">
        <div className="max-w-7xl mx-auto px-6 lg:px-10 h-[78px] flex items-center justify-between">
          <a href="#" className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-[#3925d0] to-[#6d59ee] flex items-center justify-center shadow-lg shadow-indigo-200">
              <svg
                width="23"
                height="23"
                viewBox="0 0 24 24"
                fill="none"
                stroke="white"
                strokeWidth="2"
              >
                <rect x="6" y="3" width="12" height="18" rx="2" />
                <path d="M9 7h6M9 11h6M9 15h3" />
              </svg>
            </div>
            <span className="text-xl font-extrabold tracking-tight">
              DigiBills
            </span>
          </a>

          <nav className="hidden md:flex items-center gap-9 text-sm font-semibold text-slate-600">
            <a href="#experience" className="hover:text-indigo-600">
              Your Experience
            </a>
            <a href="#warranty" className="hover:text-indigo-600">
              Digital Warranty
            </a>
            <a href="#how" className="hover:text-indigo-600">
              How It Works
            </a>
            <a href="#faq" className="hover:text-indigo-600">
              FAQ
            </a>
          </nav>

          <div className="flex items-center gap-4">
            <div className="login-menu hidden sm:block">
              <button
                type="button"
                className="text-sm font-semibold text-slate-700 inline-flex items-center gap-2 py-3"
              >
                Login <span className="text-xs">⌄</span>
              </button>

              <div className="login-menu-panel">
                <Link className="login-option" to="/login/customer">
                  <div className="login-icon">👤</div>
                  <div>
                    <div className="login-option-title">Customer Login</div>
                    <div className="login-option-desc">
                      Access your bills &amp; warranties
                    </div>
                  </div>
                  <span className="login-chevron">→</span>
                </Link>

                <Link className="login-option" to="/login/retailer">
                  <div className="login-icon">🏪</div>
                  <div>
                    <div className="login-option-title">Retailer Login</div>
                    <div className="login-option-desc">
                      Manage your retail business
                    </div>
                  </div>
                  <span className="login-chevron">→</span>
                </Link>
              </div>
            </div>

            <Link
              to="/login/customer"
              className="rounded-full bg-[#3b2bd5] text-white px-5 py-3 text-sm font-bold shadow-lg shadow-indigo-200 hover:bg-[#3020bf]"
            >
              Access My DigiBills
            </Link>
          </div>
        </div>
      </header>

      {/* HERO */}
      <section className="pt-[78px] min-h-[720px] grid-bg relative overflow-hidden">
        <div className="absolute -top-40 right-0 w-[620px] h-[620px] rounded-full bg-indigo-200/25 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 w-[500px] h-[300px] rounded-full bg-emerald-100/35 blur-3xl" />

        <div className="max-w-7xl mx-auto px-6 lg:px-10 py-20 lg:py-28 grid lg:grid-cols-[.9fr_1.1fr] gap-14 items-center relative">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-white px-4 py-2 text-xs font-extrabold text-indigo-700 shadow-sm mb-7">
              <span className="w-2 h-2 rounded-full bg-emerald-400" />
              Your digital purchase companion
            </div>

            <h1 className="text-5xl sm:text-6xl lg:text-[72px] leading-[.98] font-extrabold tracking-[-.055em]">
              Your Purchases.
              <br />
              Your Bills.
              <br />
              <span className="gradient-text">Your Warranties.</span>
            </h1>

            <p className="mt-7 text-lg leading-8 text-slate-600 max-w-xl">
              Keep your DigiBills purchase records, digital bills and eligible
              warranties together—so you can find what you need without
              searching through old receipts.
            </p>

            <div className="mt-9 flex flex-wrap items-center gap-4">
              <Link
                to="/login/customer"
                className="rounded-full bg-[#3b2bd5] text-white px-7 py-4 font-bold shadow-xl shadow-indigo-200"
              >
                Access My DigiBills
              </Link>

              <a href="#experience" className="font-bold text-slate-700 px-2 py-3">
                See how it works <span className="text-indigo-600">→</span>
              </a>
            </div>

            <div className="mt-9 flex flex-wrap gap-6 text-sm font-semibold text-slate-500">
              <span>✓ Digital bills</span>
              <span>✓ Purchase history</span>
              <span>✓ Warranty records</span>
            </div>
          </div>

          {/* CUSTOMER DIGITAL PASS */}
          <div className="relative min-h-[520px] flex items-center justify-center">
            <div className="absolute top-8 right-0 sm:right-8 w-52 rounded-2xl bg-white p-4 shadow-soft border border-slate-100 rotate-3">
              <div className="text-xs text-slate-400">Latest purchase</div>
              <div className="mt-1 font-extrabold">Wireless Headphones</div>
              <div className="mt-2 flex justify-between text-sm">
                <span className="text-slate-500">Bill total</span>
                <b>₹2,999</b>
              </div>
            </div>

            <div className="w-[330px] sm:w-[360px] rounded-[42px] bg-[#101427] p-3 phone-shadow rotate-[-3deg]">
              <div className="rounded-[33px] bg-slate-50 overflow-hidden">
                <div className="px-6 pt-7 pb-4 flex items-center justify-between">
                  <div>
                    <div className="text-xs text-slate-400">DigiBills</div>
                    <div className="font-extrabold text-xl">My Purchases</div>
                  </div>
                  <div className="w-10 h-10 rounded-xl bg-indigo-100 flex items-center justify-center text-indigo-600">
                    ⌁
                  </div>
                </div>

                <div className="mx-5 rounded-2xl bg-white border border-slate-200 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-xs text-slate-400">Today</div>
                      <div className="font-extrabold">Purchase record</div>
                    </div>
                    <span className="px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold">
                      Saved
                    </span>
                  </div>

                  <div className="mt-4 flex justify-between text-sm">
                    <span className="text-slate-500">Store</span>
                    <b>Retail Partner</b>
                  </div>

                  <div className="mt-2 flex justify-between text-sm">
                    <span className="text-slate-500">Amount</span>
                    <b>₹3,798</b>
                  </div>
                </div>

                <div className="mx-5 mt-3 rounded-2xl bg-[#111528] text-white p-5">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="text-xs text-slate-400">
                        Digital Warranty
                      </div>
                      <div className="font-extrabold text-lg mt-1">
                        Warranty record
                      </div>
                    </div>

                    <div className="w-9 h-9 rounded-xl bg-emerald-400/15 text-emerald-300 flex items-center justify-center">
                      ✓
                    </div>
                  </div>

                  <div className="mt-5 h-20 rounded-xl bg-white/5 border border-white/10 flex items-center gap-4 px-4">
                    <div className="w-14 h-14 bg-white rounded-lg flex items-center justify-center text-slate-900 text-xl">
                      ▦
                    </div>
                    <div>
                      <div className="text-xs text-slate-400">Access</div>
                      <div className="font-bold">Linked to purchase</div>
                    </div>
                  </div>
                </div>

                <div className="p-5 grid grid-cols-3 gap-2 text-center text-[10px] font-bold text-slate-500">
                  <div>Bill</div>
                  <div>Warranty</div>
                  <div>History</div>
                </div>
              </div>
            </div>

            <div className="absolute bottom-6 left-0 sm:left-8 rounded-2xl bg-white border border-slate-100 shadow-soft p-4 w-56">
              <div className="text-xs text-slate-400">Warranty status</div>
              <div className="mt-1 font-extrabold">Active</div>
              <div className="mt-3 h-2 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full w-3/4 bg-emerald-400 rounded-full" />
              </div>
              <div className="mt-2 text-[11px] text-slate-500">
                Purchase and warranty stay connected.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* EXPERIENCE */}
      <section id="experience" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6 lg:px-10">
          <div className="max-w-3xl">
            <div className="text-xs font-extrabold tracking-[.2em] text-indigo-700">
              A BETTER WAY TO KEEP YOUR RECORDS
            </div>

            <h2 className="mt-4 text-4xl lg:text-6xl font-extrabold tracking-[-.04em]">
              The receipt shouldn't be the end of the purchase.
            </h2>

            <p className="mt-5 text-lg text-slate-600 leading-8">
              With DigiBills, your purchase can remain useful after you leave
              the store. Your bill, customer record and eligible warranty can
              stay connected.
            </p>
          </div>

          <div className="mt-14 grid md:grid-cols-3 gap-5">
            <div className="rounded-[28px] bg-[#f1f2ff] p-7 min-h-[270px]">
              <div className="w-12 h-12 rounded-2xl bg-white flex items-center justify-center text-2xl shadow-sm">
                🧾
              </div>
              <h3 className="mt-7 text-2xl font-extrabold">Digital bills</h3>
              <p className="mt-3 text-slate-600 leading-7">
                Keep purchase details available digitally instead of relying on
                a paper receipt.
              </p>
            </div>

            <div className="rounded-[28px] bg-[#111528] text-white p-7 min-h-[270px]">
              <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center text-2xl">
                🛡️
              </div>
              <h3 className="mt-7 text-2xl font-extrabold">
                Digital warranties
              </h3>
              <p className="mt-3 text-slate-300 leading-7">
                Eligible products can have warranty information connected to
                the original purchase record.
              </p>
            </div>

            <div className="rounded-[28px] bg-[#eafaf4] p-7 min-h-[270px]">
              <div className="w-12 h-12 rounded-2xl bg-white flex items-center justify-center text-2xl shadow-sm">
                📦
              </div>
              <h3 className="mt-7 text-2xl font-extrabold">
                Purchase history
              </h3>
              <p className="mt-3 text-slate-600 leading-7">
                Build a useful record of purchases so important information is
                easier to find later.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* WARRANTY */}
      <section id="warranty" className="py-24 bg-[#101427] text-white overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 lg:px-10 grid lg:grid-cols-[1fr_1fr] gap-16 items-center">
          <div>
            <div className="text-xs font-extrabold tracking-[.2em] text-indigo-300">
              DIGITAL WARRANTY
            </div>

            <h2 className="mt-5 text-4xl lg:text-6xl font-extrabold tracking-[-.045em]">
              Keep your warranty where you can actually find it.
            </h2>

            <p className="mt-6 text-lg leading-8 text-slate-300 max-w-xl">
              When an eligible purchase has a DigiBills warranty record, the
              warranty can stay connected to the purchase instead of getting
              lost with a paper document.
            </p>

            <div className="mt-9 space-y-4">
              <div className="flex gap-4">
                <span className="w-8 h-8 shrink-0 rounded-full bg-emerald-400/15 text-emerald-300 flex items-center justify-center">
                  ✓
                </span>
                <div>
                  <b>Connected to your purchase</b>
                  <p className="text-sm text-slate-400 mt-1">
                    Warranty context stays with the relevant purchase record.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <span className="w-8 h-8 shrink-0 rounded-full bg-emerald-400/15 text-emerald-300 flex items-center justify-center">
                  ✓
                </span>
                <div>
                  <b>Easy digital access</b>
                  <p className="text-sm text-slate-400 mt-1">
                    Find the record digitally when you need it.
                  </p>
                </div>
              </div>

              <div className="flex gap-4">
                <span className="w-8 h-8 shrink-0 rounded-full bg-emerald-400/15 text-emerald-300 flex items-center justify-center">
                  ✓
                </span>
                <div>
                  <b>Purchase history stays useful</b>
                  <p className="text-sm text-slate-400 mt-1">
                    Your bill and warranty can be understood together.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="relative flex justify-center">
            <div className="w-[350px] sm:w-[410px] rounded-[38px] bg-white p-4 shadow-2xl rotate-3 text-slate-900">
              <div className="rounded-[27px] bg-slate-50 p-6">
                <div className="flex justify-between items-center">
                  <div>
                    <div className="text-xs text-slate-400">DigiBills</div>
                    <div className="text-xl font-extrabold">
                      Digital Warranty
                    </div>
                  </div>
                  <div className="w-11 h-11 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                    ✓
                  </div>
                </div>

                <div className="mt-7 rounded-2xl bg-white border border-slate-200 p-5">
                  <div className="text-xs text-slate-400">Customer</div>
                  <div className="font-extrabold text-lg">
                    Purchase record
                  </div>

                  <div className="mt-5 grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs text-slate-400">Product</div>
                      <b>Eligible item</b>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400">Status</div>
                      <b className="text-emerald-600">Active</b>
                    </div>
                  </div>
                </div>

                <div className="mt-4 rounded-2xl bg-[#111528] text-white p-5 flex items-center gap-4">
                  <div className="w-14 h-14 rounded-xl bg-white flex items-center justify-center text-slate-900 text-xl">
                    ▦
                  </div>
                  <div>
                    <div className="text-xs text-slate-400">
                      Digital access
                    </div>
                    <div className="font-extrabold">Warranty record</div>
                    <div className="text-xs text-slate-400 mt-1">
                      Linked to purchase
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="absolute -bottom-5 -left-2 sm:left-4 rounded-2xl bg-white/10 backdrop-blur border border-white/15 p-4 w-56">
              <div className="text-xs text-slate-400">Retailer view</div>
              <div className="font-bold mt-1">Warranty issued</div>
              <div className="text-xs text-slate-400 mt-1">
                Connected to customer record
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className="py-24 bg-[#f5f5ff]">
        <div className="max-w-7xl mx-auto px-6 lg:px-10">
          <div className="text-center max-w-3xl mx-auto">
            <div className="text-xs font-extrabold tracking-[.2em] text-indigo-700">
              HOW IT WORKS
            </div>

            <h2 className="mt-4 text-4xl lg:text-6xl font-extrabold tracking-[-.04em]">
              Simple for you. Useful after every purchase.
            </h2>

            <p className="mt-5 text-lg text-slate-600">
              Your retailer handles the billing side. DigiBills gives you a
              digital place to keep the information that matters.
            </p>
          </div>

          <div className="mt-14 grid md:grid-cols-4 gap-4">
            <div className="bg-white rounded-3xl p-6 border border-slate-200">
              <div className="text-indigo-600 font-extrabold text-sm">01</div>
              <div className="text-3xl mt-6">🛍️</div>
              <h3 className="font-extrabold text-xl mt-5">Make a purchase</h3>
              <p className="text-slate-500 mt-2 leading-6">
                Buy from a retailer using DigiBills.
              </p>
            </div>

            <div className="bg-white rounded-3xl p-6 border border-slate-200">
              <div className="text-indigo-600 font-extrabold text-sm">02</div>
              <div className="text-3xl mt-6">🧾</div>
              <h3 className="font-extrabold text-xl mt-5">
                Your bill is recorded
              </h3>
              <p className="text-slate-500 mt-2 leading-6">
                Your purchase details can be available digitally.
              </p>
            </div>

            <div className="bg-white rounded-3xl p-6 border border-slate-200">
              <div className="text-indigo-600 font-extrabold text-sm">03</div>
              <div className="text-3xl mt-6">🛡️</div>
              <h3 className="font-extrabold text-xl mt-5">
                Warranty can follow
              </h3>
              <p className="text-slate-500 mt-2 leading-6">
                Eligible warranty information can stay linked to the purchase.
              </p>
            </div>

            <div className="bg-white rounded-3xl p-6 border border-slate-200">
              <div className="text-indigo-600 font-extrabold text-sm">04</div>
              <div className="text-3xl mt-6">📱</div>
              <h3 className="font-extrabold text-xl mt-5">
                Access it later
              </h3>
              <p className="text-slate-500 mt-2 leading-6">
                Return to your digital records when you need them.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CUSTOMER DIGITAL RECORD */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6 lg:px-10 grid lg:grid-cols-[.85fr_1.15fr] gap-16 items-center">
          <div>
            <div className="text-xs font-extrabold tracking-[.2em] text-indigo-700">
              YOUR DIGITAL RECORD
            </div>

            <h2 className="mt-4 text-4xl lg:text-5xl font-extrabold tracking-[-.04em]">
              One place for the details you don't want to lose.
            </h2>

            <p className="mt-5 text-lg leading-8 text-slate-600">
              See your purchases, bills and warranty records in a customer
              experience designed around what happens after checkout.
            </p>
          </div>

          <div className="rounded-[32px] bg-[#f1f2ff] p-5 shadow-soft">
            <div className="bg-white rounded-[25px] border border-slate-200 overflow-hidden">
              <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center">
                <div>
                  <div className="text-xs text-slate-400">Welcome back</div>
                  <div className="font-extrabold text-xl">My DigiBills</div>
                </div>

                <div className="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center font-bold text-indigo-700">
                  AK
                </div>
              </div>

              <div className="p-5 grid sm:grid-cols-3 gap-3">
                <div className="rounded-2xl bg-slate-50 p-4">
                  <div className="text-xs text-slate-400">Purchases</div>
                  <div className="text-2xl font-extrabold mt-2">12</div>
                  <div className="text-xs text-slate-500 mt-1">
                    Saved records
                  </div>
                </div>

                <div className="rounded-2xl bg-emerald-50 p-4">
                  <div className="text-xs text-slate-400">Warranties</div>
                  <div className="text-2xl font-extrabold mt-2">3</div>
                  <div className="text-xs text-emerald-700 mt-1">
                    Active records
                  </div>
                </div>

                <div className="rounded-2xl bg-indigo-50 p-4">
                  <div className="text-xs text-slate-400">Bills</div>
                  <div className="text-2xl font-extrabold mt-2">12</div>
                  <div className="text-xs text-indigo-700 mt-1">Digital</div>
                </div>
              </div>

              <div className="px-5 pb-5">
                <div className="text-sm font-extrabold mb-3">
                  Recent purchases
                </div>

                <div className="space-y-2">
                  <div className="p-4 rounded-2xl border border-slate-100 flex justify-between">
                    <div>
                      <b>Wireless Headphones</b>
                      <div className="text-xs text-slate-400 mt-1">
                        Today · Warranty active
                      </div>
                    </div>
                    <b>₹2,999</b>
                  </div>

                  <div className="p-4 rounded-2xl border border-slate-100 flex justify-between">
                    <div>
                      <b>Charger</b>
                      <div className="text-xs text-slate-400 mt-1">
                        12 Aug · Bill saved
                      </div>
                    </div>
                    <b>₹799</b>
                  </div>

                  <div className="p-4 rounded-2xl border border-slate-100 flex justify-between">
                    <div>
                      <b>Smartwatch</b>
                      <div className="text-xs text-slate-400 mt-1">
                        28 Jul · Warranty active
                      </div>
                    </div>
                    <b>₹4,999</b>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* BENEFITS */}
      <section className="py-24 bg-[#f7f8fc]">
        <div className="max-w-7xl mx-auto px-6 lg:px-10">
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5">
            <div>
              <div className="text-xs font-extrabold tracking-[.2em] text-indigo-700">
                BUILT AROUND YOU
              </div>
              <h2 className="mt-4 text-4xl lg:text-5xl font-extrabold tracking-[-.04em]">
                Less searching. More certainty.
              </h2>
            </div>

            <p className="max-w-lg text-slate-600 leading-7">
              DigiBills is designed to make the customer side of retail
              simpler, especially when you need an old bill or warranty record
              later.
            </p>
          </div>

          <div className="mt-12 grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-3xl p-6 border border-slate-200">
              <div className="text-2xl">🔎</div>
              <h3 className="font-extrabold mt-6">Find records faster</h3>
              <p className="text-sm text-slate-500 mt-2 leading-6">
                Keep purchase information organized digitally.
              </p>
            </div>

            <div className="bg-white rounded-3xl p-6 border border-slate-200">
              <div className="text-2xl">🧠</div>
              <h3 className="font-extrabold mt-6">
                Remember what you bought
              </h3>
              <p className="text-sm text-slate-500 mt-2 leading-6">
                Your purchase history gives you useful context.
              </p>
            </div>

            <div className="bg-white rounded-3xl p-6 border border-slate-200">
              <div className="text-2xl">🛡️</div>
              <h3 className="font-extrabold mt-6">
                Keep warranty details close
              </h3>
              <p className="text-sm text-slate-500 mt-2 leading-6">
                Eligible warranty records can remain connected to purchases.
              </p>
            </div>

            <div className="bg-white rounded-3xl p-6 border border-slate-200">
              <div className="text-2xl">📲</div>
              <h3 className="font-extrabold mt-6">Go digital</h3>
              <p className="text-sm text-slate-500 mt-2 leading-6">
                A cleaner digital record for the purchases that matter.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ACCESS CTA */}
      <section id="access" className="py-24">
        <div className="max-w-5xl mx-auto px-6">
          <div className="rounded-[38px] bg-gradient-to-br from-[#3224c8] via-[#5140dc] to-[#7560f0] p-10 lg:p-16 text-white text-center shadow-2xl shadow-indigo-200 relative overflow-hidden">
            <div className="absolute -top-32 -right-24 w-80 h-80 rounded-full bg-white/10 blur-2xl" />
            <div className="absolute -bottom-40 -left-20 w-96 h-96 rounded-full bg-emerald-300/10 blur-3xl" />

            <div className="relative">
              <div className="text-xs font-extrabold tracking-[.2em] text-indigo-100">
                YOUR DIGIBILLS
              </div>

              <h2 className="mt-4 text-4xl lg:text-6xl font-extrabold tracking-[-.045em]">
                Your purchase records, ready when you need them.
              </h2>

              <p className="mt-5 text-indigo-100 text-lg max-w-2xl mx-auto leading-8">
                Already have DigiBills from a retailer? Access your customer
                account and see your digital records.
              </p>

              <Link
                to="/login/customer"
                className="inline-flex mt-9 rounded-full bg-white text-[#3928cc] px-7 py-4 font-extrabold shadow-lg"
              >
                Access My DigiBills
              </Link>

              <div className="mt-5 text-sm text-indigo-100">
                Running a retail business?{" "}
                <Link
                  to="/retailer-landing"
                  className="font-extrabold text-white underline underline-offset-4"
                >
                  Register as a Retailer →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-24 bg-white">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center">
            <div className="text-xs font-extrabold tracking-[.2em] text-indigo-700">
              FAQ
            </div>
            <h2 className="mt-4 text-4xl lg:text-5xl font-extrabold tracking-[-.04em]">
              Questions, answered.
            </h2>
          </div>

          <div className="mt-12 space-y-3">
            <details className="group border border-slate-200 rounded-2xl p-5">
              <summary className="cursor-pointer list-none font-extrabold flex justify-between">
                What is DigiBills?
                <span className="text-indigo-600">+</span>
              </summary>
              <p className="text-slate-600 leading-7 mt-4 pr-8">
                DigiBills is a digital retail platform that can give customers
                access to digital bills, purchase records and eligible digital
                warranty information from participating retailers.
              </p>
            </details>

            <details className="group border border-slate-200 rounded-2xl p-5">
              <summary className="cursor-pointer list-none font-extrabold flex justify-between">
                Do I need to buy a DigiBills subscription?
                <span className="text-indigo-600">+</span>
              </summary>
              <p className="text-slate-600 leading-7 mt-4 pr-8">
                No customer subscription plans are presented on this customer
                experience. DigiBills customer access is connected to the
                retailer's use of the platform.
              </p>
            </details>

            <details className="group border border-slate-200 rounded-2xl p-5">
              <summary className="cursor-pointer list-none font-extrabold flex justify-between">
                Will every purchase have a digital warranty?
                <span className="text-indigo-600">+</span>
              </summary>
              <p className="text-slate-600 leading-7 mt-4 pr-8">
                Warranty availability depends on the purchase and retailer.
                Only eligible purchases can have a DigiBills digital warranty
                record.
              </p>
            </details>

            <details className="group border border-slate-200 rounded-2xl p-5">
              <summary className="cursor-pointer list-none font-extrabold flex justify-between">
                Can I see my previous purchases?
                <span className="text-indigo-600">+</span>
              </summary>
              <p className="text-slate-600 leading-7 mt-4 pr-8">
                Your available purchase history depends on the records
                associated with your DigiBills customer account.
              </p>
            </details>
          </div>
        </div>
      </section>

      {/* CROSS CONNECTION */}
      <section className="py-10 bg-slate-50 border-y border-slate-200">
        <div className="max-w-6xl mx-auto px-6 lg:px-10 flex flex-col md:flex-row items-center justify-between gap-5">
          <div>
            <div className="font-extrabold text-lg">Are you a retailer?</div>
            <p className="text-sm text-slate-500 mt-1">
              Explore how DigiBills helps you run your retail business from one
              place.
            </p>
          </div>

          <Link
            to="/retailer-landing"
            className="rounded-full bg-white border border-slate-200 px-6 py-3 text-sm font-bold text-indigo-700 hover:border-indigo-300 shadow-sm"
          >
            Explore DigiBills for Retailers →
          </Link>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="border-t border-slate-200 bg-[#fafaff]">
        <div className="max-w-7xl mx-auto px-6 lg:px-10 py-12 flex flex-col md:flex-row justify-between gap-8">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[#3b2bd5] flex items-center justify-center text-white">
                ▤
              </div>
              <b className="text-xl">DigiBills</b>
            </div>

            <p className="mt-4 text-sm text-slate-500 max-w-sm">
              Your digital place for purchase records, bills and eligible
              warranties.
            </p>
          </div>

          <div className="flex flex-wrap gap-7 text-sm font-semibold text-slate-500">
            <a href="#experience">Experience</a>
            <a href="#warranty">Warranty</a>
            <a href="#how">How It Works</a>
            <a href="#faq">FAQ</a>
            <a href="#">Privacy</a>
            <a href="#">Terms</a>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 lg:px-10 py-5 border-t border-slate-200 text-xs text-slate-400">
          © 2026 DigiBills. Customer experience.
        </div>
      </footer>
    </div>
  );
}
