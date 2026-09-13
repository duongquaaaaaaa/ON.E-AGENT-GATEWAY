import { BrowserRouter, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import ProductList from "./pages/ProductList";
import ProductDetail from "./pages/ProductDetail";
import QuerySimulator from "./pages/QuerySimulator";
import BeforeAfter from "./pages/BeforeAfter";
import "./index.css";

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-wrapper">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<ProductList />} />
            <Route path="/products/:id" element={<ProductDetail />} />
            <Route path="/simulator" element={<QuerySimulator />} />
            <Route path="/compare" element={<BeforeAfter />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
