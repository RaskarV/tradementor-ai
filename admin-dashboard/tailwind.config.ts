import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: { 950: "#070f1d", 900: "#0a1424", 800: "#0f1c33", 700: "#16284a", 600: "#1d3560" },
        line: "#1b2d4d",
        ink: { DEFAULT: "#e6edf7", dim: "#8aa0c0" },
        teal: { DEFAULT: "#2dd4bf", dim: "#14867a" },
        sky: { DEFAULT: "#3b82f6" },
        alert: "#f87171",
        amber: "#fbbf24",
      },
      fontFamily: { sans: ["var(--font-plex)", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
};
export default config;
