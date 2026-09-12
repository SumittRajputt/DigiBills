/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#3525cd",
        secondary: "#665cf0",
        ink: "#12172a",
        muted: "#626579",
        surface: "#fbfaff",
        soft: "#f1f2ff",
        mint: "#e9fff5",
        green: "#087052",
      },
      fontFamily: {
        sans: ["Plus Jakarta Sans", "sans-serif"],
      },
      boxShadow: {
        card: "0 24px 70px rgba(36, 28, 110, 0.11)",
        float: "0 35px 90px rgba(20, 22, 45, 0.16)",
      },
    },
  },
  plugins: [],
};
