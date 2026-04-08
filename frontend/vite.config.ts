import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return;
          }

          const packagePath = id.split("node_modules/")[1] ?? "";
          const segments = packagePath.split("/");
          const packageName = segments[0]?.startsWith("@")
            ? `${segments[0]}/${segments[1]}`
            : segments[0];

          if (packageName === "recharts" || packageName.startsWith("d3-")) {
            return "charts";
          }

          if (packageName === "driver.js") {
            return "onboarding";
          }

          if (["react", "react-dom", "scheduler"].includes(packageName)) {
            return "react-vendor";
          }
        },
      },
    },
  },
});
