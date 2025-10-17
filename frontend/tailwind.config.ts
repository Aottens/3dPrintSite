import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#1F2937",
          accent: "#10B981",
          muted: "#9CA3AF"
        }
      }
    },
  },
  plugins: [],
};

export default config;
