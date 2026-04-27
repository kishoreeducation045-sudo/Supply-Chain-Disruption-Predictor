/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#7bd0ff",
        secondary: "#4edea3",
        error: "#ef4444",
        surface: "#0b1326",
        "surface-container": "#171f33",
        "surface-container-high": "#222a3d",
      },
      fontFamily: {
        inter: ["Inter", "sans-serif"],
      }
    },
  },
  plugins: [],
}