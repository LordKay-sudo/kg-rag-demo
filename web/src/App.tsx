import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import About from "./pages/About";
import Ask from "./pages/Ask";
import Corpus from "./pages/Corpus";
import Graph from "./pages/Graph";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Ask />} />
        <Route path="/corpus" element={<Corpus />} />
        <Route path="/graph/:entityId" element={<Graph />} />
        <Route path="/about" element={<About />} />
      </Routes>
    </Layout>
  );
}
